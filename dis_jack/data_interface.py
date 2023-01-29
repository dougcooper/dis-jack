from abc import ABC, abstractmethod
import asyncio
import queue

class AsyncDataInterface(ABC):
    def __init__(self):
        self.in_data = asyncio.Queue()
        self.out_data = asyncio.Queue()
        
class SyncDataInterface(ABC):
    def __init__(self):
        self.in_data = queue.Queue()
        self.out_data = queue.Queue()
        
class AudioInterface(AsyncDataInterface):
    @abstractmethod
    def samplerate(self):
        raise NotImplementedError()
    