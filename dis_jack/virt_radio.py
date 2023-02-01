from io import BytesIO
import time
from typing import Callable, TypeVar
from opendis.PduFactory import createPdu, PduTypeDecoders
from opendis.dis7 import SignalPdu, EntityID
from opendis.DataOutputStream import DataOutputStream
from dis_jack.audio_recorder import AudioWriterExecutor
from dis_jack.data_interface import AudioInterface, AsyncDataInterface
import asyncio
import audioop
from dis_jack.utils import FLOAT_SIZE_BYTES, ByteFIFO
from array import array

class Address:
    def __init__(self, site=1, host=1, entity=1, radio=1):
        self.site = site
        self.host = host
        self.entity = entity
        self.radio = radio

    @staticmethod
    def from_pdu(pdu):
        return Address(pdu.entityID.siteID, pdu.entityID.applicationID, pdu.entityID.entityID, pdu.radioID)

    def __str__(self) -> str:
        return f'{self.site}:{self.host}:{self.entity}:{self.radio}'

    def __eq__(self, rh) -> bool:
        return self.site == rh.site and self.host == rh.host and self.entity == rh.entity and self.radio == rh.radio


T = TypeVar('T')


class Filter:
    def filter(self: T, predicate: Callable[[T], bool]):
        return self if predicate(self) else None


class NotSignalPdu(Exception):
    def __init__(self, pdu_type):
        message = f'Received pdu type {PduTypeDecoders[pdu_type].__name__}'
        super().__init__(message)

class NotPdu(Exception):
    pass


class MySignalPdu(SignalPdu, Filter):
    def __init__(self, address: Address = Address(1,1,1,1)):
        self.entityID = EntityID()
        self.entityID.siteID = address.site
        self.entityID.applicationID = address.host
        self.entityID.entityID = address.entity
        self.radioID = address.radio

    @classmethod
    def from_signalpdu(cls, to_be_casted_obj):
        casted_obj = cls()
        if hasattr(to_be_casted_obj,'pduType'):
            if to_be_casted_obj.pduType != 26:
                raise NotSignalPdu(to_be_casted_obj.pduType)
            else:
                casted_obj.__dict__ = to_be_casted_obj.__dict__
        else:
            raise NotPdu()
        return casted_obj

    def address(self):
        return Address.from_pdu(self)

    def to_bytes(self):
        memoryStream = BytesIO()
        outputStream = DataOutputStream(memoryStream)
        self.serialize(outputStream)
        return memoryStream.getvalue()

class VirtualRadio:
    def __init__(self, audio: AudioInterface, network: AsyncDataInterface, audio_writer: AudioWriterExecutor = AudioWriterExecutor()):
        self.from_audio = audio.out_data
        self.to_audio = audio.in_data
        self.from_network = network.out_data
        self.to_network = network.in_data
        self.samples_per_pdu = 512  # TODO: make configurable
        self.pdu_samplerate = 8000  # TODO: make configurable
        self.audio_samplerate = audio.samplerate()
        self.address = Address(1,1,1,1)  # TODO: make configurable
        self.writer = audio_writer
        
    async def _do_transmit(self):
        ''' 
        Handle data from audio source
        '''
        buffer = ByteFIFO()
        resample_state = None
        while True:
            #TODO: would it be slightly more efficient to get an array of shorts rather than bytes?
            block = await self.from_audio.get() #S16_LE
            buffer.put(block)
            in_byte_len = self.samples_per_pdu*2
            while len(buffer) > in_byte_len:
                data = bytes(buffer.get(in_byte_len))
                resampled_data, resample_state = audioop.ratecv(
                    data, 2, 1, self.audio_samplerate, self.pdu_samplerate, resample_state)
                compressed_data = audioop.lin2ulaw(resampled_data, 2)
                pdu = MySignalPdu(self.address)
                pdu.data = compressed_data
                pdu.encodingScheme = 1  # voice + 8-bit mulaw
                pdu.sampleRate = self.pdu_samplerate
                pdu.dataLength = len(compressed_data)
                pdu.samples = len(compressed_data)
                try:
                    self.to_network.put_nowait(pdu.to_bytes())
                except:
                    print("vtb to network buffer full")

    async def _do_receive(self):
        ''' 
        Handle data from network.

        Note: we dont produce fixed size audio blocks here because we dont know the blocksize and it can change at runtime
        '''
        resample_state = None
        with self.writer as writer:
            while True:
                data = await self.from_network.get()
                pdu = createPdu(data)
                try:
                    pdu = MySignalPdu.from_signalpdu(pdu).filter(
                        lambda pdu: pdu.address() != self.address and pdu.encodingScheme == 1)
                    if pdu is not None:
                        ulaw = array('b',pdu.data) #signed chars
                        lin_data = audioop.ulaw2lin(ulaw.tobytes(), 2) #output as signed short
                        writer.write("dis_out",lin_data)
                        resampled_data, resample_state = audioop.ratecv(
                            lin_data, 2, 1, pdu.sampleRate, self.audio_samplerate, resample_state)
                        out_data = array('h',[])
                        out_data.frombytes(resampled_data)
                        out_data.extend([0 for i in range(int(self.audio_samplerate/pdu.sampleRate*pdu.samples-len(out_data)))]) #pad if needed
                        writer.write("audio_out",out_data.tobytes())
                        await self.to_audio.put(out_data)
                    else:
                        print("signal pdu not mine")
                except (NotSignalPdu,ValueError,asyncio.QueueFull) as err:
                    print(err)

    async def process(self):
        await asyncio.gather(*[self._do_receive(), self._do_transmit()])
