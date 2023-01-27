from abc import ABC, abstractmethod
import asyncio

class DataInterface(ABC):
    def __init__(self):
        self.in_data = asyncio.Queue()
        self.out_data = asyncio.Queue()
        
class AudioInterface(DataInterface):
    @abstractmethod
    def samplerate(self):
        raise NotImplementedError()
    