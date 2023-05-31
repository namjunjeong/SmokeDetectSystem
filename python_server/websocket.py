import asyncio
import websockets
import threading
import base64
import datetime
import io
import cv2
from PIL import Image

class Wss_Server(threading.Thread):
    def __init__ (self, addr, port, container, fps):
        super(Wss_Server, self).__init__()
        self.port = port
        self.server_addr = addr
        self.container = container
        self.sleep_time = 1/fps
        self.CLIENTS = set()
    
    def logger(self, message, **kwagrs):
        print('[' + datetime.datetime.now().isoformat()[:-3] + '] ' + ' [wss] : '+ message, **kwagrs)
    
    async def handler(self, websocket):
        #client가 접속하면 실행. set에 client socket정보 추가
        #접속 끊기면 삭제
        self.CLIENTS.add(websocket)
        self.logger("client registered")
        while True:
            try:
                await websocket.wait_closed()
            finally:
                self.CLIENTS.remove(websocket)
            
    async def send(self, websocket, message):
        #실제로 메시지 전송하는 부분
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass

    async def broadcast(self, message):
        #비동기적으로 모든 클라이언트에게 메시지 전송
        for websocket in self.CLIENTS:
            asyncio.create_task(self.send(websocket, message))

    async def broadcast_msg(self):
        #여기서 반복하면서 데이터 처리함
        while True:
            await asyncio.sleep(self.sleep_time)
            if len(self.container) != 0 : 
                #grpc와 같이 물려있는 container를 계속 체크. 데이터가 들어오면 처리
                self.logger("send img")
                
                img, smoking = self.container.pop(0) #앞에 이미지, 뒤에 smoking state 존재
                
                #아래는 이미지를 base64로 바꾸는 과정
                imgarray = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)) #색 보정 및 PIL image로 변경
                rawbyte = io.BytesIO()
                imgarray.save(rawbyte, "PNG")
                rawbyte.seek(0)
                #맨 앞에 smoking state piggyback
                base = base64.b64encode(smoking.encode('ascii')) + base64.b64encode(rawbyte.read())

                await self.broadcast(base)
            else :
                self.logger("noimg")
            
    async def start_server(self):
        async with websockets.serve(self.handler, self.server_addr, self.port):
            self.logger("****************************************")
            self.logger("*         🟢wss server started         *")
            self.logger(f'*        listening on port : {self.port}      *')
            self.logger("****************************************")
            await self.broadcast_msg()

    def run(self):
        asyncio.run(self.start_server())

#test in module
if __name__ == "__main__":
    wss_thread = Wss_Server(addr = "localhost", port=3001)
    wss_thread.daemon = True # main 죽으면 같이 죽도록 설정
    wss_thread.start() #websocket 서버 실행