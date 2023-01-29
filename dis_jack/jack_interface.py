import jack
from jack import OwnPort
import asyncio

from dis_jack.data_interface import AudioInterface
from dis_jack.utils import FLOAT_SIZE_BYTES, ByteFIFO
from enum import Enum

class Direction(Enum):
    IN = 'tx'
    OUT = 'rx'
    IN_OUT = 'tx_rx'
    
    def __str__(self):
        return self.value
    
class Port:
    def __init__(self):
        pass

class JackInterface(AudioInterface):
    def __init__(self,name,server=None,dir:Direction = Direction.IN_OUT):
        super().__init__()
        self.client = jack.Client(name, servername=server)
        self.shutdown = asyncio.Event()
        self.buffer = ByteFIFO()
        self.dir = dir
        if self.dir == Direction.IN or self.dir == Direction.IN_OUT:
            self.client.inports.register(f'input_1')
        
        if self.dir == Direction.OUT or self.dir == Direction.IN_OUT:
            self.client.outports.register(f'output_1')
        
        @self.client.set_shutdown_callback
        def shutdown(status, reason):
            print('JACK shutdown!')
            print('status:', status)
            print('reason:', reason)
            self.shutdown.set()
            
        @self.client.set_process_callback
        def process(frames):
            for port in self.client.inports:
                i_port: OwnPort = port
                i_b = i_port.get_buffer()
                try:
                    self.out_data.put_nowait(i_b[:])
                except:
                    print("dropping samples")
            
            for port in self.client.outports:
                o_port: OwnPort = port
                o_b = o_port.get_buffer()
                frame_byte_len = frames * FLOAT_SIZE_BYTES
                try:
                    block=self.in_data.get_nowait()
                    self.buffer.put(block)
                    
                    while len(self.buffer) > frame_byte_len:
                        o_b[:] = bytes(self.buffer.get(frame_byte_len))
                        print("added some audio")
                    
                    # buf_len = len(self.buffer)
                    # if buf_len >= frame_byte_len:
                    #     o_b[:] = bytes(self.buffer.get(frame_byte_len))
                    # else:
                    #     o_b[:buf_len] = bytes(self.buffer.getvalue())
                    #     o_b[buf_len:] = bytes(bytearray(frame_byte_len-buf_len))
                except:
                    # print("pushing silence to jack")
                    o_b[:] = bytes(bytearray(frame_byte_len))
    
    def __enter__(self):
        return self.client.__enter__()
        
    def __exit__(self):
        self.client.__exit__()
        
    def __call__(self, autoconnect = False):
        if autoconnect:
            #FIXME: this throws an error when trying to autoconnect
            if self.client.inports:
                capture = self.client.get_ports(is_physical=True, is_output=True)
                if not capture:
                    raise RuntimeError('No physical capture ports')

                for src, dest in zip(capture, self.client.inports):
                    self.client.connect(src, dest)
            
            if self.client.outports:
                playback = self.client.get_ports(is_physical=True, is_input=True)
                if not playback:
                    raise RuntimeError('No physical playback ports')

                for src, dest in zip(self.client.outports, playback):
                    self.client.connect(src, dest)
                
        return self
    
    def samplerate(self):
        return self.client.samplerate
        
    