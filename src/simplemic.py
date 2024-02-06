import pyaudio
from .signal_detectors import LoudDetector, SignalDetectorInterface
from .streams import PyAudioStream, StreamInterface, StreamFactoryInterface


class Microphone:
    def __init__(self,
                 full_stop_delay: int = 10,
                 signal_delay: int | None = 3,
                 signal_detector: SignalDetectorInterface | None = LoudDetector(threshold_energy=2000),
                 stream_factory: StreamFactoryInterface = PyAudioStream(rate=16000, frames_per_buffer=4000, channels=1, input_device_index=0, format=pyaudio.paInt16),
                 verbose_level: int = 0
                 ):
        """Initializes the Microphone object.

        Parameters:
        - full_stop_delay (required, int): length of a silence that indicates the automatical turn off of the microphone (in seconds).
        - signal_delay (optional, int): length of a silence that indicates the end of a signal (in seconds).
        - signal_detector (optional, SignalDetectorInterface): a signal detector object, detects signal and silence.
        - stream_factory (StreamFactoryInterface): a factory object that creates a stream object.
        - verbose_level (required, int): the level of verbosity (0, 1, 2). 0 - no output, 1 - minimal output, 2 - detailed output.
        """
        if full_stop_delay <= 0:
            raise ValueError("Full stop delay required to avoid infinite loop, should be greater than 0.")

        if not signal_detector:
            signal_delay = None
            print("No signal detector provided. The microphone will not detect signals, just stream the audio data.")
            
        self.signal_detector = signal_detector
        self.stream_factory = stream_factory
        self.signal_delay = signal_delay
        self.full_stop_delay = full_stop_delay
        self.stream: StreamInterface = stream_factory.get_stream()
        self._on = False
        self.verbose_level = verbose_level
        self.timestep = stream_factory.frames_per_buffer / stream_factory.rate 

    def _log(self, msg: str, required_level: int):
        if self.verbose_level >= required_level:
            print(msg)
    
    def mic_list(self):
        """List all available microphones.
        
        Output is multiline string with indexes and names of microphones
        """
        result = []
        try:
            for i in range(pyaudio.PyAudio().get_device_count()):
                device_info = pyaudio.PyAudio().get_device_info_by_index(i)
                result.append(device_info.get("name"))
            result = '\n'.join([f"{i}: {name}" for i, name in enumerate(result)])
        except Exception as e:
            raise e
        return result

    def _listen(self):
        self._log("Listening...", 1)
        acc_data = b''
        acc_silence_sec = 0
        acc_signal_sec = 0
        try:
            while self._on:
                data = self.stream.read(self.stream_factory.frames_per_buffer)
                if not self.signal_detector:
                    acc_signal_sec += self.stream_factory.frames_per_buffer / self.stream_factory.rate
                    self._log(f"Signal returned, streaming time: {acc_signal_sec} sec.", 2)
                    if acc_signal_sec >= self.full_stop_delay:
                        self.stop()
                        self._log("Stop listening: Full stop after 10 seconds of streaming", 1)
                    yield data
                else:            
                    if self.signal_detector.detect(data):
                        self._log("Signal detected", 1)
                        acc_silence_sec = 0
                        while acc_silence_sec < self.signal_delay:
                            acc_data += data
                            data = self.stream.read(self.stream_factory.frames_per_buffer)
                            if not self.signal_detector.detect(data):
                                acc_silence_sec += self.stream_factory.frames_per_buffer / self.stream_factory.rate
                            else:
                                acc_signal_sec += self.stream_factory.frames_per_buffer / self.stream_factory.rate
                                acc_silence_sec = 0
                            self._log(f"RECORDING. signal: {acc_signal_sec} sec., silence: {acc_silence_sec} sec.", 2)
                        ret_data = acc_data
                        acc_data = b''
                        acc_silence_sec = 0
                        acc_signal_sec = 0
                        self._log("Signal returned", 1)
                        yield ret_data
                    else:
                        acc_silence_sec += self.stream_factory.frames_per_buffer / self.stream_factory.rate
                        self._log(f"Silence: {acc_silence_sec} sec.", 2)
                        if acc_silence_sec >= self.full_stop_delay:
                            self.stop()
                            self._log("Stop listening: Full stop after 10 seconds of silence", 1)
                            if acc_data:
                                ret_data = acc_data
                                acc_data = b''
                                self._log("Full stop: remaining data returned", 1)
                                yield ret_data
                            else:
                                self._log("Full stop: No data remain in buffer", 1)
                                yield b''
                        yield b'silent'
        except KeyboardInterrupt:
            self._log("Listening interrupted", 1)
            self.stop()
    
    def start(self):
        self._on = True
        return self._listen()

    def stop(self):
        if self._on:
            self._on = False
            self.stream.stop_stream()
            self.stream.close()
            self._log("Stream closed", 1)