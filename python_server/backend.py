import grpc
import Proto.stream_pb2 as stream_pb2
import Proto.stream_pb2_grpc as stream_pb2_grpc
import io
import datetime
import math
from websocket import Wss_Server
from func.yolo_utils import Yolo_Utils_Class
from func.post_process import del_overlap
from concurrent import futures
from PIL import Image
'''
n초 동안 흡연이 연속으로 감지되면 흡연으로 판단
fps에 따라 n초동안 연속으로 감지되면 흡연으로 판단하도록 알고리즘 구성
cur_smoker는 객체검출로 검출된 흡연자의 수를 천천히 따라감
아래에서 사용될 가중치 n은 1/(self.fps*self.smoke_time) 와 같음
검출된 흡연자의 수가 cur_smoker보다 많을경우 위에서 계산된 가중치 부가
검출된 흡연자의 수가 cur_smoker보다 훨씬 많을 경우 그에 따라 가중치 증가
이때 가중치를 부가한 후 cur_smoker가 검출된 흡연자의 수보다 커지면 흡연으로 판단

검출된 흡연자의 수가 cur_smoker보다 적을경우 위에서 계산된 가중치 감소. 천천히 떨어뜨림
'''


class Streaming(stream_pb2_grpc.StreamingServicer):
    def __init__(self, container, model_name, fps, smoke_time, smoke_duration):
        super(Streaming, self).__init__()
        self.Y = Yolo_Utils_Class(model_name)
        self.container = container
        self.fps = fps
        self.cur_smoker = 0
        self.baseline = 0 #감지된 흡연자의 수를 천천히 따라가는 값
        self.smoke_state = 0 #0보다 클 경우 흡연중
        self.judge_time = smoke_time * self.fps # 몇초간 담배가 인식되면 흡연으로 판단할지
        self.maintain_time = smoke_duration * self.fps + 1 # 흡연 state가 유지되는 시간
            
    def ImgStream(self, request_iterator, context): #server handler
        smoke_state_bool = False
        for req in request_iterator:
            io_file = io.BytesIO(req.data) #convert data type
            pil = Image.open(io_file) #convert data type
            
            ########### processing data #############
            plotted_img, box_data = self.Y.yolo_predict(pil_img = pil, ind = req.id, with_image=True, save=True)
            box_data = del_overlap(box_data)
            
            detected_smoker = len(box_data)
            
            if self.cur_smoker < detected_smoker: #감지된 흡연자가 cur_smoker보다 많으면 가중치 추가
                self.cur_smoker += (detected_smoker-int(self.cur_smoker))/(self.judge_time)
                if self.cur_smoker > detected_smoker:
                    self.cur_smoker = detected_smoker
            elif self.cur_smoker > detected_smoker: #적으면 가중치*2만큼 감소
                self.cur_smoker -= (math.ceil(self.cur_smoker) - detected_smoker)/(self.judge_time)*2
                if self.cur_smoker < 0 :
                    self.cur_smoker = 0
                
            if self.baseline < detected_smoker: #감지된 흡연자가 baseline보다 많으면 가중치*10 추가
                self.baseline += (detected_smoker-int(self.baseline))/(self.judge_time*10)
                if self.baseline > detected_smoker:
                    self.baseline = detected_smoker
            elif self.baseline > detected_smoker: #적으면 가중치*20만큼 감소
                self.baseline -= (math.ceil(self.baseline) - detected_smoker)/(self.judge_time*10)*2
                if self.baseline < 0 :
                    self.baseline = 0
            
            self.cur_smoker = round(self.cur_smoker, 5) # solve precision problem
            self.baseline = round(self.baseline, 6) # solve precision problem
            
            if self.cur_smoker > self.baseline:
                if self.cur_smoker == detected_smoker:
                    self.smoke_state = self.maintain_time

            self.smoke_state -= 1
            if self.smoke_state < 0:
                self.smoke_state = 0
            smoke_state_bool = True if self.smoke_state>0 else False
            print(f'cur : {self.cur_smoker}     det : {detected_smoker}       base : {self.baseline}      smoke_state : {self.smoke_state}')
            ########### processing data #############
            response = stream_pb2.Result()
            response.smoke = smoke_state_bool
            
            self.container.append([plotted_img, 'O' if smoke_state_bool else 'X'])
            
            yield response

def logger(message, **kwagrs):
    print('[' + datetime.datetime.now().isoformat()[:-3] + '] ' + ' [grpc] : '+ message, **kwagrs)

if __name__=="__main__":
    model=input("input model name with .pt : ")
    fps = int(input("input FPS : "))
    smoke_time = float(input("input time(second) to judge as smoke : "))
    smoke_duration = float(input("input time(second) to maintain smoking state : "))
    container = []
    wss_thread = Wss_Server(port=3001,container= container, fps=fps)
    wss_thread.daemon = True # main 죽으면 같이 죽도록 설정
    wss_thread.start() #websocket 서버 실행
    
    grpc_options = [('grpc.max_send_message_length', 32000000), ('grpc.max_receive_message_length', 32000000)]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options=grpc_options)
    stream_pb2_grpc.add_StreamingServicer_to_server(Streaming(container, model_name=model, fps=fps, smoke_time = smoke_time, smoke_duration = smoke_duration), server)
    logger("****************************************")
    logger("*        🟢 grpc server started        *")
    logger("*        listening on port : 50051     *")
    logger("****************************************")
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()
