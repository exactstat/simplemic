import pytest
import numpy as np
from src.signal_detectors import LoudDetector
import random
import simpleaudio as sa
import time

skip_manual = False

def test_classify_energy():
    small_values = random.sample(range(100), 5)
    big_values = random.sample(range(500, 1000), 5)
    values = small_values + big_values
    th = LoudDetector().find_threshold(values)
    assert np.mean(small_values) == np.mean([v for v in values if v < th])
    assert np.mean(big_values) == np.mean([v for v in values if v >= th])


@pytest.mark.skipif(skip_manual, reason="Skip manual test")
def test_detect():
    d = LoudDetector(tune_sec=5, frames_per_buffer=4000, verbose_level=1)
    hi_beep = sa.WaveObject.from_wave_file('tests/hi_beep.wav')
    low_beep = sa.WaveObject.from_wave_file('tests/low_beep.wav')

    hi_beep.play()
    time.sleep(0.5)

    th = d.tune()

    low_beep.play()
    time.sleep(0.5)

    print(f"Threshold: {th}")

    assert th > 0