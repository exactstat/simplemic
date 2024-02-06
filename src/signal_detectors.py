import abc
import pyaudio
import math
import numpy as np
import kmeans1d
import struct

class SignalDetectorInterface(abc.ABC):
    @abc.abstractmethod
    def detect(self, raw_audio: bytes) -> bool:
        """
        Detects if there is a signal in the raw audio data.  
        raw_audio is a chunk of audio bytes from the microphone.  
        The return value is True if the signal is detected, False otherwise.
        """
        pass

    @abc.abstractmethod
    def tune(self):
        """Tune the detector or set / reset the parameters for the detector."""
        pass


class LoudDetector(SignalDetectorInterface):

    def __init__(self, 
                 threshold_energy: int = 2000, 
                 rate: int = 16000, 
                 format: int = pyaudio.paInt16, 
                 frames_per_buffer: int = 1000,
                 tune_sec: int = 5,
                 verbose_level: int = 0):
        """Initializes the LoudDetector.
        Parameters:
        - threshold_energy (int): The threshold for the energy of the audio data to detect the silence (compromise value is 2000).
        - rate (int): The sample rate of the audio data. Ie frames per second (default is 16000).
        - format: The format of the audio data (default is pyaudio.paInt16).
        - frames_per_buffer (int): The number of frames per buffer. Ie how much frmes to read at a time.
        - tune_sec (int): The number of seconds to listen to the microphone to tune the threshold.
        - verbose_level (int): The level of verbosity (0 - no verbosity, 1 - some verbosity, 2 - full verbosity).
        """
        self.threshold_energy = threshold_energy
        self.rate = rate
        self.fmt = format
        self.frames_per_buffer = frames_per_buffer
        self.tune_sec = tune_sec
        self.sample_width = pyaudio.get_sample_size(self.fmt)
        self.verbose_level = verbose_level

    def _log(self, msg: str, required_level: int):
        if self.verbose_level >= required_level:
            print(msg)
    
    @staticmethod
    def rms(data: bytes, width: int) -> int:
        """Calculates the root-mean-square of an audio fragment.
        The reason for this method is to avoid the use of audioop module 
        (that should be removed from standard library in the python 3.13)
        
        Args:
            data: A byte string containing the audio fragment.
            width: The number of bytes per sample in the audio fragment.

        Returns:
            The root-mean-square of the audio fragment.
        """
        count = len(data) // width
        fmt = f"{count}h"
        samples = struct.unpack(fmt, data)
        sum_squares = sum(sample ** 2 for sample in samples)
        rms = math.sqrt(sum_squares / count)
        return int(rms)
    
    def detect(self, raw_audio: bytes) -> bool:
        """Detects if there is a signal in the raw audio data.
        Returns True if the signal is detected, False otherwise."""
        energy = self.rms(raw_audio, self.sample_width)
        return energy > self.threshold_energy

    def find_threshold(self, values: list[int]) -> int:
        """Find the threshold for the energy of the audio data to detect the silence.
        1D K-means clustering is used to find the threshold."""
        values = np.array(values)
        clusters, centroids = kmeans1d.cluster(values, 2)
        centroids = np.round(centroids)
        self._log(f"Found 2 clusters with entroids: {centroids}, distance: {np.abs(centroids[0] - centroids[1])}", 2)
        quiet_cluster = np.argmin(centroids)
        loud_cluster = np.argmax(centroids)
        max_quiet = np.max(values[clusters == quiet_cluster])
        min_loud = np.min(values[clusters == loud_cluster])
        threshold = round((max_quiet + min_loud) / 2)
        return threshold

    def tune(self) -> int:
        """Define the threshold for the energy of the audio data to detect the silence.
        It listens to the microphone for a tune_sec seconds and calculates the energy of the audio data.
        Then it finds the threshold for the energy to detect the silence.
        """
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        sample_width = pyaudio.get_sample_size(self.fmt)
        # Open the microphone stream
        stream = p.open(format=self.fmt, channels=1, rate=self.rate, input=True, frames_per_buffer=self.frames_per_buffer)
        energy_values = list()
        # Loop for recording
        self._log("Tuning...", 1)
        duration_sec = 0
        try:
            while duration_sec < self.tune_sec:
                # Read a chunk of data from the microphone
                data = stream.read(self.frames_per_buffer)
                # Calculate and append the energy of the audio data
                energy_values.append(self.rms(data, sample_width))
                duration_sec += self.frames_per_buffer / self.rate
                self._log(f"Listening... {duration_sec} sec.", 2)
        except KeyboardInterrupt:
            self._log("Tuning interrupted. Nothing set.", 1)
            raise
        th = self.find_threshold(energy_values)
        self.threshold_energy = th
        self._log(f"Threshold: {th} (energy level)", 1)
        # Close the microphone stream
        stream.stop_stream()
        stream.close()
        return th