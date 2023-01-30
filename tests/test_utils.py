from dis_jack.utils import ByteFIFO

def test_fifo():
    b = bytes([1,2,3])
    assert len(b) == 3
        
    fifo = ByteFIFO()
    fifo.put(b)
    assert len(fifo) == 3
    
    d = fifo.get(3)
    assert len(d) == 3
    assert len(fifo) == 0
    
    fifo.put(b)
    assert len(fifo) == 3
    
    d = fifo.peek(3)
    assert len(d) == 3
    assert len(fifo) == 3
    
    fifo.put(bytes([4,5]))
    d = fifo.getvalue()
    assert len(d) == 5
    assert len(fifo) == 5