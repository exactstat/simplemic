import pyaudio
import abc


class StreamInterface(abc.ABC):
    """Interface for the stream object.  

    The stream object is used to read audio data from the microphone.

    Required methods: read, start_stream, stop_stream, close, is_stopped.

    Required attributes: rate, frames_per_buffer.
    - rate: the sample rate in Hz.
    - frames_per_buffer: the number of frames to read at a time.
    """
    
    @abc.abstractmethod
    def __init__(self, rate: int, frames_per_buffer: int, **kwargs):
        """Initialize the stream.  
        The rate is a positive integer.  
        The frames_per_buffer is a positive integer."""
        pass
    
    @abc.abstractmethod
    def read(self, num_frames: int) -> bytes:
        """Read a number of frames from the stream.  
        The number of frames is a positive integer.  
        The return value is a bytes object."""
        pass

    @abc.abstractmethod
    def start_stream(self):
        """Start the stream.  
        The stream can be stopped with the stop_stream method."""
        pass
    
    @abc.abstractmethod
    def stop_stream(self):
        """Stop the stream.  
        The stream can be restarted with the start_stream method."""
        pass

    @abc.abstractmethod
    def close(self):
        """Close the stream."""
        pass

    @abc.abstractmethod
    def is_stopped(self) -> bool:
        """Check if the stream is stopped. 
        Returns True if the stream is stopped, False otherwise."""
        pass


class StreamFactoryInterface(abc.ABC):
    
        @abc.abstractmethod
        def get_stream(self) -> StreamInterface:
            """Get the stream object"""
            pass


class PyAudioStream(StreamFactoryInterface):

    def __init__(self, 
                 rate: int = 16000, 
                 frames_per_buffer: int = 4000, 
                 channels: int = 1, 
                 format = pyaudio.paInt16, 
                 input_device_index: int = 0):
        """Initialize the PyAudioStream object.
        Parameters:
        - rate: the sample rate in Hz.
        - frames_per_buffer: the number of frames to read at a time.
        - channels: the number of channels to read.
        - format: the format of the audio data (default is pyaudio.paInt16).
        - input_device_index: the index of the input device to use (default is 0).
        """
        if rate % frames_per_buffer != 0:
            raise ValueError("The rate should be divisible by the frames per buffer without a remainder.")
            
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.channels = channels
        self.format = format
        self.input_device_index = input_device_index

    def get_stream(self) -> StreamInterface:
        """Get the stream object for the PyAudio library."""
        p = pyaudio.PyAudio()
        stream = p.open(
            format=self.format, 
            channels=self.channels, 
            rate=self.rate, 
            input=True, 
            frames_per_buffer=self.frames_per_buffer,
            input_device_index=self.input_device_index
            )
        return stream

