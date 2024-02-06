# simplemic

With `simplemic` you can easily record audio from a microphone.

* Provides a generator for reading from a buffer.
* Works on the basis of a stream from `pyaudio`, has an interface for creating your own streams.
* Has the ability to connect a signal detector, has an interface for creating your own detectors.

## Install from GitHub
**There is no release on PyPI yet.**

Install from the GitHub repository:
```bash
pip install git+https://github.com/exactstat/simplemic
```


## The easiest way to use

1. Import and create an instance of the `Microphone` class
2. Start the read loop

```python
from simplemic import Microphone
mic = Microphone(verbose_level=2)
events = mic.start()
for e in events:
	if len(e) == 0:
		break
	if e != b'silent':
		pass
mic.stop()
```

Parameters:

* **full_stop_delay** (required, default to 10 sec.): length of a silence for automatical turn off of the microphone (in seconds).  It must be greater than 0 to prevent an endless reading loop.
* **signal_delay** (optional, default 3 sec.): length of a silence that indicates the end of a signal (in seconds). It works only in conjunction with a `signal_detector`. If the signal detector recognises a signal, the signal will be recorded until the end of the signal + the specified delay.
* **signal_detector** (optional): a signal detector object, detects signal and silence. By default, the signal detector is based on the energy level set to 2000. This means that you will not receive all the data from the microphone, but only detected parts of different lengths + `signal_delay` value.
* **stream_factory** (required, default `PyAudio` strem): a factory object that creates a stream object. `pyaudio` stream is default and configured for voice recording: 16000 Hz, reading by 0.25 seconds (4000 frames)
* **verbose_level** (required, default 0): the level of verbosity (0, 1, 2). 0 - no output, 1 - minimal output, 2 - detailed output.

If the microphone returns zero-length data (`if len(e) == 0:...`), the reading loop is completed according to the settings.

If the microphone returns the byte string "silent" (`if e != b'silent':...`), it means that there is no signal. This, works only if the signal detector is working.
The workflow can be interrupted by pressing CTRL+C, which will cause the stream to close correctly.

Output example (verbose_level=2):
```
Listening...
Silence: 0.25 sec.
Silence: 0.5 sec.
...
Silence: 1.5 sec.
Silence: 1.75 sec.
Signal detected
RECORDING. signal: 0.25 sec., silence: 0 sec.
RECORDING. signal: 0.5 sec., silence: 0 sec.
...
RECORDING. signal: 3.5 sec., silence: 0 sec.
RECORDING. signal: 3.75 sec., silence: 0 sec.
RECORDING. signal: 4.0 sec., silence: 0 sec.
RECORDING. signal: 4.0 sec., silence: 0.25 sec.
RECORDING. signal: 4.0 sec., silence: 0.5 sec.
...
RECORDING. signal: 4.0 sec., silence: 2.75 sec.
RECORDING. signal: 4.0 sec., silence: 3.0 sec.
Signal returned
Silence: 0.25 sec.
Silence: 0.5 sec.
...
Silence: 9.75 sec.
Silence: 10.0 sec.
Stream closed
Stop listening: Full stop after 10 seconds of silence
Full stop: No data remain in buffer
```

Let's look at what happened:

1. First, there was 1.75 seconds of silence.
2. Then you said something and the signal detector noticed it.
3. The recording started and lasted for 4 seconds while you were speaking.
4. After that, the silence counter was turned on and the recording continued for 3 seconds (`signal_delay`).
5. You received a signal (`Signal returned`) and can use it, for example, to send it to automatic speech recognition.
6. Then there was silence for 10 seconds (`full_stop_delay`).
7. After that, the stream stops.

## Use without a signal detector
You need to disable the signal detector if you want to receive the entire signal (by chunks of `frames_per_buffer` size).
To disable the signal detector, set the `signal_detector` parameter to `None`.

```python
from simplemic import Microphone
mic = Microphone(verbose_level=2, full_stop_delay=10, signal_detector=None)
events = mic.start()
for e in events:
	if len(e) == 0:
		break
mic.stop()
```

Output example (verbose_level=2):

```
No signal detector provided. The microphone will not detect signals, just stream the audio data.
Listening...
Signal returned, streaming time: 0.25 sec.
Signal returned, streaming time: 0.5 sec.
...
Signal returned, streaming time: 9.75 sec.
Signal returned, streaming time: 10.0 sec.
Stream closed
Stop listening: Full stop after 10 seconds of streaming
```

### Setting up a stream
To setup a stream, you need to initialise it separately and pass it as a parameter to the microphone instance

```python
from simplemic import Microphone, streams
st = streams.PyAudioStream(
                 rate = 16000, 
                 frames_per_buffer = 4000, 
                 channels = 1, 
                 format = pyaudio.paInt16, 
                 input_device_index = 0
                 )
mic = Microphone(stream_factory=st, verbose_level=2)
```

Parameters:
* **rate**: the sample rate in Hz. Should be standard values: 16000, 24000, 32000, 44100 Hz (frames per second). Also must be divided by `frames_per_buffer without` a remainder.
* **frames_per_buffer**: the number of frames to read at a time. 4000 frames (1/4 second) are enough to record a voice in 16000 Hz format. Default value is 4000.
* **channels**: the number of channels to read. the microphone usually has 1 channel.
* **format**: the format of the audio data (default is pyaudio.paInt16).
* **input_device_index**: the index of the input device to use (default is 0).

### Setting up a signal detector
To setup a signal detector, you need to initialise it separately and pass it as a parameter to the microphone instance

```python
from simplemic import Microphone, signal_detectors
sd = signal_detectors.LoudDetector(
                 threshold_energy = 2000, 
                 rate = 16000, 
                 format = pyaudio.paInt16, 
                 frames_per_buffer = 1000,
                 tune_sec = 5,
                 verbose_level = 0
                 )
mic = Microphone(signal_detector=sd, verbose_level=2)
```

You can set `threshold_energy` manually. The default value is 2000. The higher the value, the louder the signal must be to be detected.

Parameters:
* **threshold_energy**: the threshold energy level for the signal detector. The default value is 2000.

**The next parameters are used only for tuning the detector:**

* **rate**: the sample rate in Hz. Should be standard values: 16000, 24000, 32000, 44100 Hz (frames per second). Also must be divided by `frames_per_buffer` without a remainder.
* **frames_per_buffer**: the number of frames to read at a time. 1000 frames (i.e. 1/16 second) are enough to tune a threshold level in 16000 Hz format. Default value is 1000.
* **channels**: the number of channels to read. the microphone usually has 1 channel.
* **format**: the format of the audio data (default is pyaudio.paInt16).
* **tune_sec**: the length of the signal to tune the threshold level (in seconds). The default value is 5.
* **verbose_level**: the level of verbosity (0, 1, 2). 0 - no output, 1 - minimal output, 2 - detailed output.

### Optimal `threshold_energy` level
You can determine the optimal `threshold_energy` value for your microphone by using the `tune` method of the signal detector.
```python
from simplemic import signal_detectors
sd = signal_detectors.LoudDetector(
                 threshold_energy = 2000, 
                 rate = 16000, 
                 fmt = pyaudio.paInt16, 
                 frames_per_buffer = 1000,
                 tune_sec = 5,
                 verbose_level = 1
                 )
th = d.tune()
print(f"Threshold: {th}")
```
Use the microphone for 5 seconds (`tune_sec`) and leave some silence as well.`LoudDetector` will automatically classify the quiet and loud parts of the recording and determine the optimal threshold_energy. The `threshold_energy` value will be returned and also _it will be set as the `threshold_energy` value of the detector._

Output example (verbose_level=1):
```
Tuning...
Threshold: 2699 (energy level)
```

### Creating your own signal detector
The `signal_detectors` module contains one standard detector that distinguishes between quiet and loud sound parts. You may want to create your own detector, for example, based on the Silero VAD neural network. To create your own signal detector, use the `signal_detectors.SignalDetectorInterface`.

`SignalDetectorInterface` - the interface for the signal detector.

**Required methods:** detect, tune

Whatever the logic of your detector, it will be compatible with `simplemic` if it supports the `detect()` and `tune()` methods.

### Creating your own stream
The `streams` module contains class interfaces for the stream and the stream factory. Use these interfaces to create your own stream.

`StreamInterface` - the interface for the stream.

**Required methods:** read, start_stream, stop_stream, close, is_stopped.

**Required `__init__` attributes:** rate, frames_per_buffer.
- rate: the sample rate in Hz.
- frames_per_buffer: the number of frames to read at a time.

Create your own stream class based on this interface to ensure that it works within simplemic.

`StreamFactoryInterface` - the interface for the stream factory.

**Required methods:** get_stream

The `streams` module uses the `pyaudio` stream and the `streams.PyAudioStream` factory.

Whatever the logic of your stream and factory, they will be compatible with `simplemic` if they support standard interfaces.
