from dis_jack.audio_recorder import AudioRecorder,AudioWriterExecutor
import os
import pytest

sr = 8000

@pytest.fixture
def dir(fs):
    test_dir = "/var/data"
    fs.create_dir(test_dir)
    assert os.path.exists(test_dir)
    return test_dir

def test_audio_recorder(dir):            
    r = AudioRecorder("foo",dir,sr)
    r.open()
    r.write(bytearray(sr))
    r.close()
    r.close() #can call close multiple times
    
    assert os.path.exists(f"{dir}/foo.wav")
    
def test_audio_executor(dir):
    exec = AudioWriterExecutor({"some_foo":AudioRecorder("foo",dir,sr)})
    
    with exec as e:
        e.write("some_foo",bytearray(sr))
        
    assert os.path.exists(f"{dir}/foo.wav")
    
    with exec as e:
        e.write("bar",bytearray(sr))
        
    assert not os.path.exists(f"{dir}/bar.wav")
                        
    exec = AudioWriterExecutor()
    
    with exec as e:
        e.write("bar",bytearray(sr))
        
    assert not os.path.exists(f"{dir}/bar.wav")