import grpc

import stream_pb2
import stream_pb2_grpc
from concurrent import futures
import io
from PIL import Image
from ultralytics import YOLO
import cv2

model = YOLO('yolov8n.pt')#define yolo model

class Streaming(stream_pb2_grpc.StreamingServicer):
    def ImgStream(self, request_iterator, context): #server handler
        for req in request_iterator:
            io_file = io.BytesIO(req.data) #convert data type
            pil = Image.open(io_file) #convert data type
            
            ########### processing data #############
            result = model(pil)
            res_plot = result[0].plot()
            cv2.imwrite(f'{req.id}.jpeg',res_plot)#save processed image
            ########### processing data #############
            
            response = stream_pb2.Result()
            response.smoke = False #return processing result
            yield response

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    stream_pb2_grpc.add_StreamingServicer_to_server(Streaming(), server)
    print("****************************************")
    print("*           🟢server started           *")
    print("*        listing on port : 50051       *")
    print("****************************************")
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()
    
if __name__=="__main__":
    serve()