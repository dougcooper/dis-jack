from typing import List
import jack
from jack import OwnPort
import asyncio

from dis_jack.data_interface import AudioInterface
from dis_jack.utils import FLOAT_SIZE_BYTES, ArrayFIFO, ByteFIFO, ElapsedTimer
from enum import Enum

class Direction(Enum):
    IN = 'tx'
    OUT = 'rx'
    
    def __str__(self):
        return self.value
    
class Port:
    def __init__(self):
        pass
    
class NotEnoughData(BaseException):
    pass

class JackInterface(AudioInterface):
    def __init__(self,name,auto_connect=True,server=None,dir:List[Direction] = [Direction.IN,Direction.OUT]):
        super().__init__()
        self.client = jack.Client(name, servername=server)
        self.shutdown = asyncio.Event()
        self.buffer = ArrayFIFO('h')
        self.dir = dir
        self.counts = {"no_data":0,"ok_data":0,"ne_data":0}
        self.auto_connect = auto_connect
        if Direction.IN in self.dir:
            self.client.inports.register(f'input_1')
        
        if Direction.OUT in self.dir:
            self.client.outports.register(f'output_1')
            
        @self.client.set_xrun_callback
        def xrun(delay):
            print("An xrun occured, increase JACK's period size?")
        
        @self.client.set_shutdown_callback
        def shutdown(status, reason):
            print('JACK shutdown!')
            print('status:', status)
            print('reason:', reason)
            self.shutdown.set()
            
        @self.client.set_process_callback
        def process(frames):
            #process inputs
            for port in self.client.inports:
                i_port: OwnPort = port
                i_b = i_port.get_buffer()
                try:
                    self.out_data.put_nowait(i_b[:])
                except (asyncio.QueueFull):
                    print("dropping samples")
            
            #process outputs
            for port in self.client.outports:
                t = ElapsedTimer()
                o_port: OwnPort = port
                o_b = o_port.get_buffer()
                data = bytes(bytearray(frames * FLOAT_SIZE_BYTES)) #null byte array
                        
                try:                  
                    frames_processed = False
                    while not frames_processed:
                        if len(self.buffer) >= frames:
                            #we have enough data
                            s_data = self.buffer.get(frames)
                            f_data = [float(i)/32767 for i in s_data]
                            data = ArrayFIFO('f',f_data).getvalue().tobytes()
                            self.counts["ok_data"]+=1
                            frames_processed = True
                        else:
                            #get some data
                            block=self.in_data.get_nowait() #array(S16_LE)
                            self.buffer.put(block)
                except:
                    self.counts["no_data"]+=1
                finally:
                    o_b[:] = data

                print(f'{port.name}: {self.counts}')
                    
    def __enter__(self):
        client = self.client.__enter__()
        
        if self.auto_connect:
            self._connect()
            
        return client
        
    def __exit__(self,*args):
        self.client.__exit__()
        
    def _connect(self):
        if self.client.inports:
            capture = self.client.get_ports(is_physical=True, is_output=True)
            if not capture:
                raise RuntimeError('No physical capture ports')

            for src, dest in zip(capture, self.client.inports):
                print(f"connecting {src} to {dest}")
                self.client.connect(src, dest)
        
        if self.client.outports:
            playback = self.client.get_ports(is_physical=True, is_input=True)
            if not playback:
                raise RuntimeError('No physical playback ports')

            for src, dest in zip(self.client.outports, playback):
                print(f"connecting {src} to {dest}")
                self.client.connect(src, dest)
                    
    def samplerate(self):
        return self.client.samplerate
        
class Autoconnect:
    def __init__(self,where: str = None):
        self.to = where
    
    