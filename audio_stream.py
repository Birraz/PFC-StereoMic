import numpy as np
import time
import recording_settings
import pyaudio
import sound_processing
import audio_settings
from collections.abc import Mapping




class AudioStreamer:
    """
    Handles audio streaming and recording with real-time processing and playback functionality.

    This class is designed for managing audio streams using the PyAudio library. It allows
    recording of audio data, applying real-time processing such as equalization, and playback.
    The class provides methods to start, stop, and manage the lifecycle of audio streaming,
    along with callback mechanisms for processing the streaming data.

    Attributes
    ----------
    rec_set : RecordingSettings
        Configuration settings for recording, such as sampling frequency, chunk
        size, and file paths.
    audio : pyaudio.PyAudio
        PyAudio interface instance used for handling audio operations.
    rate : int
        Sampling frequency for audio recording.
    frame_size : int
        Size of audio chunks for processing.
    stream : Optional[pyaudio.Stream]
        Represents the active audio stream when initialized.
    audio_file : str
        Name of the audio file used for saving the recorded data.
    file_path : str
        File path of the recorded file.
    channels : int
        Number of audio channels (e.g., 2 for stereo).
    full_audio : bytes
        Full-length audio data in bytes.
    frame_start_index : int
        Tracks the current audio frame position during streaming.
    """
    def __init__(self, rec_set = recording_settings.RecordingSettings(), audio_set = audio_settings.AudioSettings()) :
        """
        Initializes the AudioRecorder object, sets up audio recording parameters,
        and prepares the PyAudio instance for handling audio recording. This class
        uses the settings provided to configure audio channels, sampling rate,
        frame_size size, and file paths for storing recorded audio data.

        Parameters
        ----------
        rec_set : RecordingSettings, optional
            An object that provides configuration settings for the audio recording.
            Includes sampling frequency, frame_size size, input data bytes, file name,
            and file path. If not provided, defaults to an instance of the
            RecordingSettings class.
        """

        #Local Class Variables
        self.rec_set = rec_set
        self.audio_set = audio_set
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frame_start_index = 0

        #Record Settings Class Variables
        self.rate = rec_set.sampling_freq
        self.frame_size = rec_set.frame_size
        self.audio_file = rec_set.file_name
        self.file_path = rec_set.full_path_name
        self.full_audio = rec_set.in_data_bytes
        self.channels = rec_set.channels
        self.bit_depth = rec_set.bit_depth
        self.byte_depth = int(self.bit_depth / 8)

    def callback(self,in_data: bytes | None,frame_count: int,time_info: Mapping[str, float],status: int) -> tuple[bytes | None, int] | None:

        """
        Processes a frame_size of audio data, applies transformations, and streams the processed audio data.

        This method serves as a callback function for handling audio data chunks during
        real-time audio streaming. It fetches a segment of audio data from an internal
        buffer, reshapes it for stereo audio (if applicable), updates the frame position,
        and optionally applies transformations like equalization. The processed audio
        data is subsequently queued for further processing or saving and returned as
        a bytes object for streaming purposes.

        Parameters
        ----------
        in_data : bytes
            The audio input data, typically provided by the audio input stream.
        frame_count : int
            The number of frames to process in the current callback call.
        time_info : dict
            Timing information dictionary, provided by the audio back-end, containing
            data about the timing of the audio stream.
        status : int
            The status flag indicating the current status of the audio stream.

        Returns
        -------
        tuple
            A tuple containing:
                - out_data_bytes (bytes): The processed audio data in bytes format,
                  ready to be streamed back through the audio output stream.
                - int: A constant indicating whether the audio stream should continue
                  (e.g., `pyaudio.paContinue`).

        """

        # Convert Full Audio file in bytes to np array
        full_audio = np.frombuffer(self.rec_set.in_data_bytes, dtype=np.int16)
        full_audio_length = len(full_audio)

        # Calculate start and end indices for this frame
        start = self.frame_start_index
        end = start + (frame_count * self.channels)

        # Ensure the frame end index is smaller than the end of data
        if end > full_audio_length:
            print("End of audio reached. (@callback)")
            end = full_audio_length

        # Separates the full audio data inputted to the callback in frames
        frame_np = full_audio[start:end]

        # Update position tracker for the next callback
        self.frame_start_index = end



        #frame_equalized = sound_processing.band_pass_filter(frame_np, 1000 , 7000, self.rate).astype(np.int16)
        frame_equalized = sound_processing.apply_equalizer(frame_np, self.rate,self.bit_depth).astype(np.int16)

        # Store data in queue for later saving
        self.rec_set.add_to_audio_queue(frame_equalized)

        # Convert output data to bytes
        out_data_bytes = frame_equalized.tobytes()

        # Streams raw equalized data
        return out_data_bytes, pyaudio.paContinue


    def start_stream(self):
        """
        Starts the audio stream with the specified configurations.

        This method initializes and starts the audio stream using the
        PyAudio interface. It configures the stream with the provided
        audio settings like format, channels, rate, input/output mode, and
        frame_size size. The `stream_callback` function is used to handle the
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
            format=self.audio.get_format_from_width(self.byte_depth),
            channels=self.channels,
            rate=self.rate,
            output=True,
            frames_per_buffer=self.frame_size,
            stream_callback= self.callback,
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
        Stops the audio stream and releases associated resources.

        This method ensures that any audio stream currently active is stopped,
        and all resources related to the PortAudio interface are properly
        released. It is particularly useful for cleanup operations to prevent
        resource leaks and ensure the audio system is in a stable state.

        See Also
        --------
        stream.stop_stream : Stops the current audio stream.
        stream.close : Closes the audio stream.
        audio.terminate : Closes the PortAudio instance, releasing resources.

        """
        if self.stream:
            print("Stopping stream... (@stop_stream)")
            self.stream.stop_stream()
            print("Closing stream... (@stop_stream)")
            self.stream.close()
        if self.audio:
            print("Closing PortAudio... (@stop_stream)")
            self.audio.terminate()