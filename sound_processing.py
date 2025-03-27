from scipy import signal
import numpy as np
import audio_settings as audio_set
import pyaudio

audio = audio_set.AudioSettings()


def apply_equalizer(data, samplerate):
    """Applies an equalizer to the input signal."""
    eq_bands = audio.eq_bands  # Get current equalizer settings

    if not eq_bands:
        return data  # No EQ bands set, return original data

    equalized_data = np.zeros_like(data, dtype=np.float32)

    # Apply each band filter and add the result to the output
    for band_id, (freq, gain, q) in eq_bands.items():
        # Calculate bandwidth using Q factor
        bandwidth = freq / q
        low_freq = freq - (bandwidth / 2)  # Lower edge of the band
        high_freq = freq + (bandwidth / 2)  # Upper edge of the band

        # Nyquist frequency
        nyquist = samplerate / 2

        # Normalize frequencies
        low = low_freq / nyquist
        high = high_freq / nyquist

        if not (0 <= low < high <= 1):
            raise ValueError(f"Invalid filter band limits: low={low}, high={high}")

        # Design bandpass filter
        b, a = signal.butter(N=4, Wn=[low, high], btype='bandpass', fs=samplerate)

        # Apply filter and gain
        band_filtered = signal.filtfilt(b, a, data, axis=0)
        equalized_data += band_filtered * (10 ** (gain / 20))  # Convert dB to linear gain

    return equalized_data

class AudioStreamer:
    def __init__(self, rate=44100, chunk=1024):
        self.rate = rate
        self.chunk = chunk
        self.stream = None
        self.audio = pyaudio.PyAudio()

    def callback(self, in_data, frame_count, time_info, status):
        """Process streaming audio data."""
        processed_data =apply_equalizer(in_data, self.rate)  # Equalization logic
        return processed_data, pyaudio.paContinue

    def start_stream(self):
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            output=True,
            frames_per_buffer=self.chunk,
            stream_callback=self.callback
        )
        self.stream.start_stream()

    def stop_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()


