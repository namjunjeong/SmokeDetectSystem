import grpc
import Proto.stream_pb2 as stream_pb2
import Proto.stream_pb2_grpc as stream_pb2_grpc
import io
from websocket import Wss_Server
from func.yolo_utils import Yolo_Utils_Class
from func.post_process import del_overlap
from concurrent import futures
from PIL import Image
import datetime
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
    def __init__(self, container, model_name, fps, smoke_time):
        super(Streaming, self).__init__()
        self.Y = Yolo_Utils_Class(model_name)
        self.container = container
        self.fps = fps
        self.cur_smoker = 0
        self.smoke_state = False
        self.smoke_time = smoke_time
            
    def ImgStream(self, request_iterator, context): #server handler
        for req in request_iterator:
            io_file = io.BytesIO(req.data) #convert data type
            pil = Image.open(io_file) #convert data type
            
            ########### processing data #############
            plotted_img, box_data = self.Y.yolo_predict(pil_img = pil, ind = req.id, with_image=True, save=True)
            box_data = del_overlap(box_data)
            
            detected_smoker = len(box_data)
            if (self.cur_smoker != 0) or (detected_smoker != 0):
                if self.cur_smoker <= detected_smoker:
                    self.cur_smoker += (detected_smoker-int(self.cur_smoker))/(self.fps*self.smoke_time)
                    if int(self.cur_smoker) == detected_smoker:
                        self.smoke_state = True
                        self.cur_smoker = int(self.cur_smoker)
                elif self.cur_smoker > detected_smoker:
                    self.cur_smoker -= 1/(self.fps*self.smoke_time)
                    self.smoke_state = False
                    if self.cur_smoker < 0:
                        self.cur_smoker = 0
            self.cur_smoker = round(self.cur_smoker, 3) # solve precision problem
            print(f'cur : {self.cur_smoker}     det : {detected_smoker}')
            ########### processing data #############
            response = stream_pb2.Result()
            response.smoke = self.smoke_state
            
            self.container.append([plotted_img, 'O' if self.smoke_state else 'X'])
            
            yield response

def logger(message, **kwagrs):
    print('[' + datetime.datetime.now().isoformat()[:-3] + '] ' + ' [grpc] : '+ message, **kwagrs)

if __name__=="__main__":
    model=input("input model name with .pt : ")
    fps = int(input("input FPS : "))
    smoke_time = float(input("input time(second) to judge as smoke : "))
    container = []
    wss_thread = Wss_Server(addr = "localhost", port=3001,container= container, fps=fps)
    wss_thread.daemon = True # main 죽으면 같이 죽도록 설정
    wss_thread.start() #websocket 서버 실행
    
    grpc_options = [('grpc.max_send_message_length', 32000000), ('grpc.max_receive_message_length', 32000000)]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options=grpc_options)
    stream_pb2_grpc.add_StreamingServicer_to_server(Streaming(container, model_name=model, fps=fps, smoke_time = smoke_time), server)
    logger("****************************************")
    logger("*        🟢 grpc server started        *")
    logger("*        listening on port : 50051     *")
    logger("****************************************")
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()
