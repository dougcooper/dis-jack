from dis_jack.utils import ArrayFIFO, ByteFIFO,ElapsedTimer

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
    
def test_array():
    b = [1,2,3]
        
    fifo = ArrayFIFO('h')
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
    
    fifo.put([4,5])
    d = fifo.getvalue()
    assert len(d) == 5
    assert len(fifo) == 5
    
def test_elapsed():
    
    def do_work(t: ElapsedTimer):
        _ = 1+1
        t1 = t.elapsed()
        assert  t1 > 0
        _ = 1+1
        t2 = t.elapsed()
        assert t2 > t1
        
    t = ElapsedTimer()
    do_work(t)
    
    with ElapsedTimer() as t:
        do_work(t)