import pytest
from src import Microphone, signal_detectors, streams
import simpleaudio as sa
import time

skip_manual = False

def test_mic_list():
    mic = Microphone()
    lst = mic.mic_list()
    print(lst)
    assert mic.mic_list() != []  # This is a placeholder for the real test


@pytest.mark.skipif(skip_manual, reason="Skip manual test")
def test_start_stop():
    sd = signal_detectors.LoudDetector(threshold_energy=2000)
    st = streams.PyAudioStream(frames_per_buffer=4000)
    mic = Microphone(stream_factory=st, signal_detector=sd, verbose_level=2)
    hi_beep = sa.WaveObject.from_wave_file('tests/hi_beep.wav')
    low_beep = sa.WaveObject.from_wave_file('tests/low_beep.wav')

    hi_beep.play()
    time.sleep(0.5)
    
    events = mic.start()
    for e in events:
        if len(e) == 0:
            break
        if e != b'silent':
            pass
    mic.stop()

    low_beep.play()
    time.sleep(0.5)
    assert True

    