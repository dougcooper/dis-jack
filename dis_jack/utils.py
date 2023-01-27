import asyncio
import struct
from typing import List,Coroutine

FLOAT_SIZE_BYTES = len(struct.pack('f',0.0))

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