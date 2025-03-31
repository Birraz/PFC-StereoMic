from scipy import signal
import numpy as np
import audio_settings
import pyaudio
import recording_settings
import time
import soundfile as sf
#import sound_processing


def get_audio_properties(file_path):
    """Retrieve bit depth, format, sampling rate, and channels from an audio file."""
    with sf.SoundFile(file_path) as audio_file:
        bit_depth = audio_file.subtype_info  # Subtype gives the precise bit depth
        channels = audio_file.channels  # Number of audio channels
        rate = audio_file.samplerate  # Sampling rate
        return bit_depth, channels, rate


def apply_equalizer(data, samplerate):
    """
    Applies an equalizer to the input audio data based on defined equalizer band
    settings. The function iterates through each equalizer band, calculates the
    bandwidth using the Q factor, designs corresponding bandpass filters, and
    applies them to the input data. The results of each bandpass filter are
    combined to produce the equalized audio output.

    Parameters
    ----------
    data : np.ndarray
        The input audio sample data as a NumPy array. Each element represents
        an audio sample in the time domain.
    samplerate : int
        The sample rate of the input audio data in Hz. Used to calculate the
        Nyquist frequency and normalize frequency bands.

    Returns
    -------
    np.ndarray
        A NumPy array containing the equalized audio data. The array has the same
        shape as the input data but with the equalizer bands applied.

    Raises
    ------
    ValueError
        If the calculated filter band limits are invalid (e.g., not in the range
        [0, 1] or if the lower frequency is not less than the higher frequency).
    """
    eq_bands = audio_set.eq_bands  # Get current equalizer settings

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
        b, a = signal.butter(N=4, Wn=[low_freq, high_freq], btype='bandpass', fs=samplerate)

        # Apply filter and gain
        band_filtered = signal.filtfilt(b, a, data, axis=0)
        equalized_data += band_filtered * (10 ** (gain / 20))  # Convert dB to linear gain

    return equalized_data

audio_set = audio_settings.AudioSettings()


class AudioStreamer:
    def __init__(self, rec_set = recording_settings.RecordingSettings()) :
        self.rec_set = rec_set
        self.audio = pyaudio.PyAudio()

        self.rate = rec_set.sampling_freq
        self.chunk = rec_set.chunk
        self.stream = None
        self.audio_file = rec_set.file_name  # FLAC file object for saving data
        self.file_path = rec_set.full_path_name  # Dynamic FLAC file path for

        self.channels = 2
        self.in_data =rec_set.in_data_bytes


    def callback(self, in_data, frame_count, time_info, status):
        """
        Processes incoming audio data in real-time, applies an equalizer effect, and prepares it
        for playback while storing the processed data.

        This function serves as a callback in a real-time audio processing pipeline. It converts the
        incoming raw audio data to a numpy array, processes it using a specified equalizer function,
        stores the processed audio for later use, and then converts the processed data back to
        byte format for playback. The function ensures that the audio remains continuous in the
        real-time processing setup by returning the playback data and a continue signal.

        Parameters
        ----------
        in_data : bytes
            Raw audio data in bytes received from the input device.
        frame_count : int
            Number of audio frames in the input data to be processed.
        time_info : dict
            Metadata about the time and stream, provided by the PyAudio framework.
        status : int
            Status flag indicating the state of the audio input/output.

        Returns
        -------
        tuple
            A tuple containing:
            - processed_audio_byte : bytes
                Processed audio data in byte format ready for playback.
            - int
                A signal indicating whether the audio processing should continue (e.g.,
                pyaudio.paContinue).
        """

        # Convert raw bytes to numpy array
        audio_np = np.frombuffer(in_data, dtype=np.float32)

        # Applies an equalizer in real time
        #equalized_audio_np = sound_processing.apply_equalizer(audio_np, self.rate)
        #Print(equalized_audio_np.shape)

        # Store data in queue for later saving
        self.rec_set.add_to_audio_queue(audio_np.copy())

        out_data_bytes = audio_np.tobytes()

        return out_data_bytes, pyaudio.paContinue


    def start_stream(self):
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.rate,
            input=True,
            output=True,
            frames_per_buffer=self.chunk,
            stream_callback= self.callback
        )
        self.stream.start_stream()

    def stop_stream(self):
        """Stop and clean up the audio stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

    def streaming(self):
        """Runs the streaming loop with proper exception handling."""
        try:
            while self.stream.is_active():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Streaming stopped via KeyboardInterrupt.")
        except Exception as e:
            print(f"Unexpected streaming error: {e}")
        finally:
            self.stop_stream()



