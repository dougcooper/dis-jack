from dis_jack.virt_radio import Address,MySignalPdu, NotPdu, NotSignalPdu
from opendis.dis7 import SignalPdu,EntityStatePdu
import audioop
import array
import pytest

@pytest.fixture
def address():
    return Address(1,1,1,1)

@pytest.fixture
def pdu(address):
    return MySignalPdu(address)

def test_address(address):
   assert str(address) == "1:1:1:1"
   
def test_signal_pdu_address(address):
    pdu = MySignalPdu(address)
    assert pdu.address() == address
    
def test_signal_pdu_filter(pdu: MySignalPdu):
    ''' show that predicate can access members of MySignalPdu '''
    f1 = pdu.filter(lambda pdu: pdu.address() == Address(1,1,1,1))
    assert f1 != None
    
def test_signal_pdu_cast():
    #valid cast
    pdu1 = SignalPdu()
    sig = MySignalPdu.from_signalpdu(pdu1)
    assert sig
    
    class Foo:
        pass
    
    with pytest.raises(NotPdu):
        MySignalPdu.from_signalpdu(Foo())
    
    with pytest.raises(NotSignalPdu) as err:
        pdu2 = EntityStatePdu()
        sig = MySignalPdu.from_signalpdu(pdu2)
        
def test_mu_law():
    size = 2
    invals = [-29,29,90,220,450,900,2000,4000,8100]
    indata = array.array('h',invals)
    ulaw = audioop.lin2ulaw(indata.tobytes(),size)
    lin = audioop.ulaw2lin(ulaw,size)
    outdata = array.array('h',lin)
    outvals = outdata.tolist()
    assert invals == outvals