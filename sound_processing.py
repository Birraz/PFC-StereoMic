import time

from scipy import signal
import soundfile as sf
import numpy as np
import pyaudio

import audio_settings
import recording_settings



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

    equalized_data = np.zeros_like(data, dtype=np.int16)

    # Apply each band filter and add the result to the output
    for band_id, (freq, gain, q) in eq_bands.items():
        # Calculate bandwidth using Q factor
        bandwidth = freq / q
        low_freq :int = freq - (bandwidth / 2)  # Lower edge of the band
        high_freq :int = freq + (bandwidth / 2)  # Upper edge of the band

        # Nyquist frequency
        nyquist = samplerate / 2

        # Normalize frequencies
        low = low_freq / nyquist
        high = high_freq / nyquist

        if not (0 <= low < high <= 1):
            raise ValueError(f"Invalid filter band limits: low={low}, high={high}")

        # Design bandpass filter
        Wn = np.array((low_freq, high_freq))
        b, a = signal.butter(N=4, Wn=Wn, btype='bandpass', fs=samplerate)

        # Apply filter and gain
        band_filtered = signal.filtfilt(b, a, data, axis=0)
        equalized_data = band_filtered * (10 ** (gain / 20))  # Convert dB to linear gain

    return equalized_data

audio_set = audio_settings.AudioSettings()


class AudioStreamer:
    def __init__(self, rec_set = recording_settings.RecordingSettings()) :
        """
        Initializes the AudioRecorder object, sets up audio recording parameters,
        and prepares the PyAudio instance for handling audio recording. This class
        uses the settings provided to configure audio channels, sampling rate,
        chunk size, and file paths for storing recorded audio data.

        Parameters
        ----------
        rec_set : RecordingSettings, optional
            An object that provides configuration settings for the audio recording.
            Includes sampling frequency, chunk size, input data bytes, file name,
            and file path. If not provided, defaults to an instance of the
            RecordingSettings class.
        """
        self.rec_set = rec_set
        self.audio = pyaudio.PyAudio()

        self.rate = rec_set.sampling_freq
        self.chunk = rec_set.chunk
        self.stream = None
        self.audio_file = rec_set.file_name  # FLAC file object for saving data
        self.file_path = rec_set.full_path_name  # Dynamic FLAC file path for

        self.channels = 2
        self.full_audio =rec_set.in_data_bytes
        self.frame_number = 0


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

        # Convert Full Audio file in bytes to np array
        full_audio = np.frombuffer(self.rec_set.in_data_bytes, dtype=np.int16)

        # Calculate start and end indices for this chunk
        start = self.frame_number
        end = start + (frame_count * self.channels)

        # Ensure we don't go past the audio buffer length
        if end > len(full_audio):
            end = len(full_audio)

        # Extract the chunk
        audio_np = full_audio[start:end]

        # Reshape for stereo audio if needed
        if self.channels > 1:
            audio_np = audio_np.reshape(-1, self.channels)  # Shape (samples, channels)

        # Update position tracker for the next callback
        self.frame_number = end

        # Applies an equalizer in real time
        #equalized_audio_np = apply_equalizer(audio_np, self.rate)

        # Store data in queue for later saving
        self.rec_set.add_to_audio_queue(audio_np)

        # Convert equalized data to bytes
        out_data_bytes = audio_np.tobytes()
        out_data_bytes = np.frombuffer(audio_np, dtype=np.int16)
        # Streams raw equalized data
        return (audio_np, pyaudio.paContinue)


    def start_stream(self):
        """
        Starts the audio stream with the specified configurations.

        This method initializes and starts the audio stream using the
        PyAudio interface. It configures the stream with the provided
        audio settings like format, channels, rate, input/output mode, and
        chunk size. The `stream_callback` function is used to handle the
        data processing during the streaming process.

        Attributes
        ----------
        self.stream : pyaudio.Stream
            Represents the audio stream object which is initialized and
            started by this method.

        Raises
        ------
        OSError
            If the audio input/output device cannot be accessed or fails
            to initialize.
        """
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.chunk ,
            stream_callback= self.callback
        )
        print("Starting stream... (@start_stream)")
        self.stream.start_stream()

    def streaming(self):
        """
        streaming(self)

        Manages real-time audio streaming that includes recording and live playback in
        a continuous loop. The method runs until interrupted, ensuring proper execution
        and handling of exceptions during the streaming process.

        Raises
        ------
        KeyboardInterrupt
            Raised when the user interrupts the streaming process manually.
        Exception
            Captures and outputs any unexpected errors that occur during streaming.
        """
        try:
            while self.stream.is_active():
                #print("Recording and live playback in progress... (@streaming)")
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("Streaming stopped via KeyboardInterrupt. (@streaming)")
            self.stop_stream()
        except Exception as e:
            print(f"Unexpected streaming error: {e} (@streaming)")

    def stop_stream(self):
        """
        Stops the audio stream and terminates the PortAudio instance.

        This method is responsible for stopping the currently active
        audio stream (if it exists), closing it, and terminating the
        PortAudio instance. It ensures the proper release of audio
        resources and handles cleanup processes for the audio stream
        and related components.

        Attributes
        ----------
        stream : Optional[Any]
            Represents the audio stream object. It must provide `stop_stream`
            and `close` methods to allow proper stopping and release of
            the stream.
        audio : Optional[Any]
            Represents the audio interface instance. It must provide the
            `terminate` method to allow proper termination of audio-related
            operations.

        Examples
        --------
        This function is used as part of audio handling workflows to ensure
        resources are released correctly when the stream is no longer needed.
        """
        if self.stream:
            print("Stopping stream... (@stop_stream)")
            self.stream.stop_stream()
            print("Closing stream... (@stop_stream)")
            self.stream.close()
        if self.audio:
            print("Closing PortAudio... (@stop_stream)")
            self.audio.terminate()






