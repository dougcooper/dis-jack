import asyncio
import struct
from array import array
from typing import List,Coroutine
from timeit import default_timer as timer

FLOAT_SIZE_BYTES = 4
S16_LE = 2

async def select(coros: List[Coroutine]):
    """ returns when a single task completes"""
    tasks = [asyncio.create_task(coro) for coro in coros]
    await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)

class ByteFIFO:
    """ byte FIFO buffer """
    def __init__(self):
        self._buf = bytearray()

    def put(self, data):
        self._buf.extend(data)

    def get(self, size):
        data = self._buf[:size]
        # The fast delete syntax
        self._buf[:size] = b''
        return data

    def peek(self, size):
        return self._buf[:size]

    def getvalue(self):
        # peek with no copy
        return self._buf

    def __len__(self):
        return len(self._buf)
    
class ArrayFIFO:
    """ Array FIFO buffer """
    def __init__(self,type,data=[]):
        self._buf = array(type,data)

    def put(self, data):
        self._buf.extend(data)

    def get(self, size):
        data = self._buf[:size]
        # The fast delete syntax
        del self._buf[:size]
        return data

    def peek(self, size):
        return self._buf[:size]

    def getvalue(self):
        # peek with no copy
        return self._buf
    
    def putbytes(self,bytes):
        self._buf.frombytes(bytes)

    def __len__(self):
        return len(self._buf)
    
class ElapsedTimer:
    def __init__(self):
        self.start = timer()
        self.end = 0
        
    def __enter__(self):
        self.start = timer()
        return self
        
    def __exit__(self,*args):
        self.end = timer()
        
    def elapsed(self):
        self.end = timer()
        return self.end - self.start