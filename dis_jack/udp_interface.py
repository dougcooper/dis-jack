import asyncio
from dis_jack.data_interface import AsyncDataInterface
from dis_jack.utils import select

class UdpInterface(AsyncDataInterface):
    def __init__(self):
        super().__init__()
        self._disconnected = asyncio.Event()
        self._transport: asyncio.DatagramTransport = None
        
    def connection_lost(self, exc):
        print("Connection closed")
        self._disconnected.set()
        
    def connection_made(self, transport):
        print("Transport connected")
        self._transport =transport
        
    def error_received(self, exc):
        print('Error received:', exc)
        
    def datagram_received(self,data,addr):
        try:
            self.out_data.put_nowait(data)
        except:
            print("udp out buffer full")
        
    async def process(self):
        async def send_data():
            for data in await self.in_data.get():
                self._transport.sendto(data)
        
        await select([send_data(),self._disconnected.wait()]) 