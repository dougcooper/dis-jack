from typing import Dict
from wave import Wave_write
import wave
from abc import ABC, abstractmethod


class Recorder(ABC):
    @abstractmethod
    def open(self):
        raise NotImplementedError()
    
    @abstractmethod
    def write(self,data):
        raise NotImplementedError()

class AudioRecorder(Recorder):
    def __init__(self,name,path,sample_rate,sample_width=2,nchans=1):
        self.writer:Wave_write = None
        self.name = name
        self.path = path
        self.full_path = f'{self.path}/{self.name}.wav'
        self.rate = sample_rate
        self.width = sample_width
        self.nchans = nchans
        self.frame_cnt = 0
        
    def open(self):
        self.writer = wave.open(self.full_path,'wb')
        self.writer.setframerate(self.rate)
        self.writer.setsampwidth(self.width)
        self.writer.setnchannels(self.nchans)
        
    def write(self,data):
        self.writer.writeframesraw(data)
        
    def close(self):
        self.writer.close()
    
    def __del__(self):
        self.close()
        
class AudioWriterExecutor:
    def __init__(self,writers:Dict[str,Recorder] = {}):
        self.writers = writers
        
    def add_writer(self,name,writer):
        self.writers[name] = writer
        
    def write(self,name: str,data):
        try:
            writer:Recorder = self.writers[name]
            writer.write(data)
        except KeyError:
            #we dont want side effects here
            print(f"writer {name} does not exist")
        
    def __enter__(self):
        for _,writer in self.writers.items():
            writer.open()
        return self
    
    def __exit__(self,*args):
        pass
        
