import jack
from jack import OwnPort
import asyncio

from dis_jack.data_interface import AudioInterface
from dis_jack.utils import FLOAT_SIZE_BYTES, ByteFIFO

jack.__name__ = "jack"

class JackInterface(AudioInterface):
    def __init__(self,name,server=None):
        super().__init__()
        self.client = jack.Client(name, servername=server)
        self.shutdown = asyncio.Event()
        self.buffer = ByteFIFO()
        
        @self.client.set_shutdown_callback
        def shutdown(status, reason):
            print('JACK shutdown!')
            print('status:', status)
            print('reason:', reason)
            self.shutdown.set()
            
        @self.client.set_process_callback
        def process(frames):
            i_port: OwnPort = self.client.inports[0]
            i_b = i_port.get_buffer()
            try:
                self.out_data.put_nowait(i_b[:])
            except:
                print("dropping samples")
            
            o_port: OwnPort = self.client.outports[0]
            o_b = o_port.get_buffer()
            frame_byte_len = frames * FLOAT_SIZE_BYTES
            try:
                block=self.in_data.get_nowait()
                self.buffer.put(block)
                
                buf_len = len(self.buffer)
                if buf_len >= frame_byte_len:
                    o_b[:] = bytes(self.buffer.get(frame_byte_len))
                else:
                    o_b[:buf_len] = bytes(self.buffer.getvalue())
                    o_b[buf_len:] = bytes(bytearray(frame_byte_len-buf_len))
            except:
                o_b[:] = bytes(bytearray(frame_byte_len))
                
        self.client.inports.register(f'input_1')
        self.client.outports.register(f'output_1')
    
    def __enter__(self):
        self.client.activate()
        
    def __exit__(self):
        self.client.deactivate()
        
    def __call__(self, autoconnect = False):
        if autoconnect:
            capture = self.client.get_ports(is_physical=True, is_output=True)
            if not capture:
                raise RuntimeError('No physical capture ports')

            for src, dest in zip(capture, self.client.inports):
                self.client.connect(src, dest)

            playback = self.client.get_ports(is_physical=True, is_input=True)
            if not playback:
                raise RuntimeError('No physical playback ports')

            for src, dest in zip(self.client.outports, playback):
                self.client.connect(src, dest)
                
        return self
    
    def samplerate(self):
        return self.client.samplerate
        
    