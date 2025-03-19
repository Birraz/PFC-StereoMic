import wave
import pyaudio
import sys
import time
import numpy as np
from scipy import signal

def open_audio_file(filename):
    """
    Opens a WAV audio file and retrieves its parameters.
    """
    wf = wave.open(filename, 'rb')
    channels = wf.getnchannels()
    sample_width = wf.getsampwidth()
    rate = wf.getframerate()
    return wf, channels, sample_width, rate

def get_numpy_dtype(sample_width):
    """
    Returns the appropriate NumPy data type based on sample width.
    """
    if sample_width == 1:
        return np.int8
    elif sample_width == 2:
        return np.int16
    else:
        return np.int16  

def create_audio_stream(p, format, channels, rate, callback):
    """
    Creates and returns a PyAudio stream for audio playback.
    """
    return p.open(format=format,
                  channels=channels,
                  rate=rate,
                  output=True,
                  frames_per_buffer=1024,
                  stream_callback=callback)

class LowPassFilter:
    def __init__(self, cutoff_freq, sample_rate, order=4):
        """
        Initialize a low-pass filter.
        
        Args:
            cutoff_freq (float): Cutoff frequency in Hz
            sample_rate (int): Sampling rate in Hz
            order (int): Filter order
        """
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff_freq / nyquist
        self.b, self.a = signal.butter(order, normal_cutoff, btype='low')
        self.zi = None  # Filter state
        self.channels = None
    
    def process(self, audio_data, channels):
        """
        Process audio data through the filter.
        
        Args:
            audio_data (numpy.ndarray): Audio data
            channels (int): Number of channels
            
        Returns:
            numpy.ndarray: Filtered audio data
        """
        # Initialize state if not already done or if channels changed
        if self.zi is None or self.channels != channels:
            self.channels = channels
            self.zi = [signal.lfilter_zi(self.b, self.a) for _ in range(channels)]
        
        # Process each channel separately
        if channels > 1:
            # Split interleaved audio data into separate channels
            channel_data = [audio_data[i::channels] for i in range(channels)]
            filtered_channels = []
            
            for i, data in enumerate(channel_data):
                filtered, self.zi[i] = signal.lfilter(self.b, self.a, data, zi=self.zi[i])
                filtered_channels.append(filtered)
            
            # Interleave channels back together
            filtered_data = np.empty(audio_data.shape, dtype=audio_data.dtype)
            for i, channel in enumerate(filtered_channels):
                filtered_data[i::channels] = channel
            
            return filtered_data
        else:
            # Single channel case
            filtered_data, self.zi[0] = signal.lfilter(self.b, self.a, audio_data, zi=self.zi[0])
            return filtered_data

class HighPassFilter:
    def __init__(self, cutoff_freq, sample_rate, order=4):
        """
        Initialize a high-pass filter.
        
        Args:
            cutoff_freq (float): Cutoff frequency in Hz
            sample_rate (int): Sampling rate in Hz
            order (int): Filter order
        """
        nyquist = 0.5 * sample_rate
        normal_cutoff = cutoff_freq / nyquist
        self.b, self.a = signal.butter(order, normal_cutoff, btype='high')
        self.zi = None  # Filter state
        self.channels = None
    
    def process(self, audio_data, channels):
        """
        Process audio data through the filter.
        
        Args:
            audio_data (numpy.ndarray): Audio data
            channels (int): Number of channels
            
        Returns:
            numpy.ndarray: Filtered audio data
        """
        # Initialize state if not already done or if channels changed
        if self.zi is None or self.channels != channels:
            self.channels = channels
            self.zi = [signal.lfilter_zi(self.b, self.a) for _ in range(channels)]
        
        # Process each channel separately
        if channels > 1:
            # Split interleaved audio data into separate channels
            channel_data = [audio_data[i::channels] for i in range(channels)]
            filtered_channels = []
            
            for i, data in enumerate(channel_data):
                filtered, self.zi[i] = signal.lfilter(self.b, self.a, data, zi=self.zi[i])
                filtered_channels.append(filtered)
            
            # Interleave channels back together
            filtered_data = np.empty(audio_data.shape, dtype=audio_data.dtype)
            for i, channel in enumerate(filtered_channels):
                filtered_data[i::channels] = channel
            
            return filtered_data
        else:
            # Single channel case
            filtered_data, self.zi[0] = signal.lfilter(self.b, self.a, audio_data, zi=self.zi[0])
            return filtered_data

class BandFilter:
    def __init__(self, low_freq, high_freq, sample_rate, gain_db=0, order=4):
        """
        Initialize a band filter with adjustable gain.
        
        Args:
            low_freq (float): Lower cutoff frequency in Hz
            high_freq (float): Higher cutoff frequency in Hz
            sample_rate (int): Sampling rate in Hz
            gain_db (float): Gain in decibels to apply to this band
            order (int): Filter order
        """
        nyquist = 0.5 * sample_rate
        low_normal = low_freq / nyquist
        high_normal = high_freq / nyquist
        self.b, self.a = signal.butter(order, [low_normal, high_normal], btype='band')
        self.gain = 10 ** (gain_db / 20)  # Convert dB to linear gain
        self.zi = None  # Filter state
        self.channels = None
    
    def process(self, audio_data, channels):
        """
        Process audio data through the filter with gain applied.
        
        Args:
            audio_data (numpy.ndarray): Audio data
            channels (int): Number of channels
            
        Returns:
            numpy.ndarray: Filtered audio data with gain applied
        """
        # Initialize state if not already done or if channels changed
        if self.zi is None or self.channels != channels:
            self.channels = channels
            self.zi = [signal.lfilter_zi(self.b, self.a) for _ in range(channels)]
        
        # Process each channel separately
        if channels > 1:
            # Split interleaved audio data into separate channels
            channel_data = [audio_data[i::channels] for i in range(channels)]
            filtered_channels = []
            
            for i, data in enumerate(channel_data):
                filtered, self.zi[i] = signal.lfilter(self.b, self.a, data, zi=self.zi[i])
                filtered_channels.append(filtered * self.gain)  # Apply gain
            
            # Interleave channels back together
            filtered_data = np.empty(audio_data.shape, dtype=audio_data.dtype)
            for i, channel in enumerate(filtered_channels):
                filtered_data[i::channels] = channel
            
            return filtered_data
        else:
            # Single channel case
            filtered_data, self.zi[0] = signal.lfilter(self.b, self.a, audio_data, zi=self.zi[0])
            return filtered_data * self.gain  # Apply gain

class Equalizer:
    def __init__(self, sample_rate):
        """
        Initialize a multi-band equalizer.
        
        Args:
            sample_rate (int): Sampling rate in Hz
        """
        self.sample_rate = sample_rate
        self.bands = []
    
    def add_band(self, low_freq, high_freq, gain_db):
        """
        Add a frequency band to the equalizer.
        
        Args:
            low_freq (float): Lower cutoff frequency in Hz
            high_freq (float): Higher cutoff frequency in Hz
            gain_db (float): Gain in decibels to apply to this band
        """
        band = BandFilter(low_freq, high_freq, self.sample_rate, gain_db)
        self.bands.append(band)
    
    def process(self, audio_data, channels):
        """
        Process audio data through all equalizer bands.
        
        Args:
            audio_data (numpy.ndarray): Audio data
            channels (int): Number of channels
            
        Returns:
            numpy.ndarray: Equalized audio data
        """
        # Create a copy of the input to avoid modifying it
        result = np.zeros_like(audio_data, dtype=np.float32)
        
        # Process through each band and accumulate the results
        for band in self.bands:
            result += band.process(audio_data.astype(np.float32), channels)
        
        # Convert back to original data type with clipping
        if audio_data.dtype == np.int16:
            result = np.clip(result, -32768, 32767).astype(np.int16)
        elif audio_data.dtype == np.int8:
            result = np.clip(result, -128, 127).astype(np.int8)
        
        return result

def create_equalizer(sample_rate, eq_settings=None):
    """
    Create and configure an equalizer with standard bands.
    
    Args:
        sample_rate (int): Sampling rate in Hz
        eq_settings (dict, optional): Dictionary of band gains in dB
        
    Returns:
        Equalizer: Configured equalizer
    """
    # Default EQ settings (all flat)
    default_settings = {
        "20-60": 0,       # Sub bass
        "60-200": 0,      # Bass
        "200-600": 0,     # Low mids
        "600-2000": 0,    # Mids
        "2000-6000": 0,   # High mids
        "6000-20000": 0   # Highs
    }
    
    # Use provided settings or defaults
    settings = eq_settings if eq_settings is not None else default_settings
    
    # Create equalizer
    eq = Equalizer(sample_rate)
    
    # Add bands based on settings
    for band, gain in settings.items():
        low, high = map(float, band.split("-"))
        eq.add_band(low, high, gain)
    
    return eq

def callback(in_data, frame_count, time_info, status):
    """
    Callback function for processing audio frames during playback.
    """
    data = wf.readframes(frame_count)
    if len(data) == 0:
        return (data, pyaudio.paComplete)
    
    # Convert to numpy array
    audio_data = np.frombuffer(data, dtype=np_dtype)
    
    # Apply filters based on selected mode
    if filter_mode == "lowpass":
        processed_data = lowpass_filter.process(audio_data, channels)
    elif filter_mode == "highpass":
        processed_data = highpass_filter.process(audio_data, channels)
    elif filter_mode == "equalizer":
        processed_data = equalizer.process(audio_data, channels)
    else:
        processed_data = audio_data
    
    return (processed_data.tobytes(), pyaudio.paContinue)

# Main code execution
if __name__ == "__main__":
    # Check if the file was passed as an argument
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} audio_file.wav [filter_type] [parameters]")
        print("Filter types: lowpass, highpass, equalizer")
        print("Examples:")
        print(f"  {sys.argv[0]} music.wav lowpass 1000")
        print(f"  {sys.argv[0]} music.wav highpass 300")
        print(f"  {sys.argv[0]} music.wav equalizer \"bass+6 mid-3 high+2\"")
        sys.exit(-1)

    # Initialize PyAudio
    p = pyaudio.PyAudio()

    # Open the audio file
    wf, channels, sample_width, RATE = open_audio_file(sys.argv[1])
    FORMAT = p.get_format_from_width(sample_width)
    np_dtype = get_numpy_dtype(sample_width)

    # Default to no filter
    filter_mode = "none"
    lowpass_filter = None
    highpass_filter = None
    equalizer = None

    # Parse filter arguments
    if len(sys.argv) > 2:
        filter_mode = sys.argv[2].lower()
        
        if filter_mode == "lowpass" and len(sys.argv) > 3:
            cutoff_freq = float(sys.argv[3])
            lowpass_filter = LowPassFilter(cutoff_freq, RATE)
            print(f"Applying lowpass filter with cutoff: {cutoff_freq} Hz")
            
        elif filter_mode == "highpass" and len(sys.argv) > 3:
            cutoff_freq = float(sys.argv[3])
            highpass_filter = HighPassFilter(cutoff_freq, RATE)
            print(f"Applying highpass filter with cutoff: {cutoff_freq} Hz")
            
        elif filter_mode == "equalizer":
            # Create a standard equalizer
            eq_settings = {
                "20-60": 0,      # Sub bass
                "60-200": 0,     # Bass
                "200-600": 0,    # Low mids
                "600-2000": 0,   # Mids
                "2000-6000": 0,  # High mids
                "6000-20000": 0  # Highs
            }
            
            # Process EQ argument if provided
            if len(sys.argv) > 3:
                eq_arg = sys.argv[3]
                
                # Parse equalizer settings
                # Format: "bass+6 mid-3 high+2"
                eq_parts = eq_arg.split()
                for part in eq_parts:
                    if "bass" in part.lower():
                        gain = float(part.replace("bass", ""))
                        eq_settings["60-200"] = gain
                    elif "mid" in part.lower():
                        gain = float(part.replace("mid", ""))
                        eq_settings["600-2000"] = gain
                    elif "high" in part.lower():
                        gain = float(part.replace("high", ""))
                        eq_settings["6000-20000"] = gain
            
            equalizer = create_equalizer(RATE, eq_settings)
            print(f"Applying equalizer with settings: {eq_settings}")
        else:
            print("Invalid filter parameters. Running in pass-through mode.")
            filter_mode = "none"
    else:
        print("No filter specified. Running in pass-through mode.")

    # Create and start the stream
    stream = create_audio_stream(p, FORMAT, channels, RATE, callback)
    stream.start_stream()

    print("Playing audio...")
    print(f"Sample width: {sample_width} bytes per sample")
    print(f"Sample rate: {RATE} Hz")
    print(f"Channels: {channels}")

    # Keep the script running until the stream ends
    while stream.is_active():
        time.sleep(0.1)

    print("Playback finished.")

    # Close everything at the end
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()