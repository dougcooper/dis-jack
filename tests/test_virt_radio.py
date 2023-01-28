from dis_jack.virt_radio import Address,MySignalPdu
import pytest

@pytest.fixture
def address():
    return Address("1:1:1:1")

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
    f1 = pdu.filter(lambda pdu: pdu.address() == Address("1:1:1:1"))
    assert f1 != None 