import asyncio
import websockets
import threading
import base64
import datetime

class Wss_Server(threading.Thread):
    def __init__ (self, addr, port, container):
        super(Wss_Server, self).__init__()
        self.port = port
        self.server_addr = addr
        self.container = container
        self.CLIENTS = set()
    
    def logger(self, message, **kwagrs):
        print('[' + datetime.datetime.now().isoformat()[:-3] + '] ' + ' [wss] : '+ message, **kwagrs)
    
    async def handler(self, websocket):
        self.CLIENTS.add(websocket)
        self.logger("client registered")
        while True:
            try:
                await websocket.wait_closed()
            finally:
                self.CLIENTS.remove(websocket)
            
    async def send(self, websocket, message):
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass

    async def broadcast(self, message):
        for websocket in self.CLIENTS:
            asyncio.create_task(self.send(websocket, message))

    async def broadcast_msg(self):
        while True:
            if len(self.container) != 0 :
                self.logger("send img")
                message = base64.b64encode(self.container.pop(0))
                await self.broadcast(message)
            else :
                self.logger("no img")
                await asyncio.sleep(0.5)
            
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