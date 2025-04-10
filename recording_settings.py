import queue
from threading import Lock
import constant
import os
import numpy as np


class RecordingSettings:
    def __init__(self):
        self._lock = Lock()

        # Default values
        self._bit_depth = getattr(constant, "DEFAULT_BIT_DEPTH", 24)  # Default bit depth
        self._sampling_freq = getattr(constant, "DEFAULT_SAMPLING_FREQ", 192000)  # Default sampling rate
        self._directory = "path\\to\\save\\audio"  # Path to save audio
        self._file_name = "default_audio.flac"  # Default file name
        self._session_number = 0  # Default session number
        self._session_name = "Default_Session"  # Default session name
        self._frame_size = 1024
        self._in_data_bytes = None
        self._audio_queue = queue.Queue()

        # Recording controls
        self._recording_active = False
        self._recording_start_time = None
        self._recording_duration = 0

    @property
    def audio_queue_size(self):
        """Returns the size of the audio queue in a thread-safe manner."""
        with self._lock:
            return self._audio_queue.qsize()

    @property
    def audio_queue(self):
        """Get frame_size size."""
        with self._lock:
            return self._audio_queue

    @property
    def is_audio_queue_empty(self):
        """Checks if the audio queue is empty in a thread-safe manner."""
        with self._lock:
            return self._audio_queue.empty()

    def add_to_audio_queue(self, item):
        """Adds an item to the audio queue in a thread-safe manner."""
        with self._lock:
            self._audio_queue.put(item)

    def get_from_audio_queue(self):
        """Gets and removes an item from the audio queue in a thread-safe manner."""
        with self._lock:
            try:
                return self._audio_queue.get_nowait()
            except queue.Empty:
                return None

    def get_concatenated_audio(self):
        """Concatenate and return all audio data (NumPy arrays) in the queue."""
        with self._lock:
            if self._audio_queue.empty():  # Check queue's emptiness
                return np.array([], dtype=np.int16)  # Return empty array
            return np.concatenate(list(self._audio_queue.queue))  # Concatenate queue contents safely

    @property
    def frame_size(self):
        """Get frame_size size."""
        with self._lock:
            return self._frame_size

    @frame_size.setter
    def frame_size(self, value):
        """Set frame_size size."""
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Chunk size must be a positive integer.")
        with self._lock:
            self._frame_size = value

    @property
    def in_data_bytes(self):
        """Get in_data_bits."""
        with self._lock:
            return self._in_data_bytes

    @in_data_bytes.setter
    def in_data_bytes(self, value):
        """Set in_data_bits."""
        if value is not None and not isinstance(value, (bytes, bytearray)):
            raise ValueError("in_data_bits must be a bytes object or None.")
        with self._lock:
            self._in_data_bytes = value

    @property
    def bit_depth(self):
        """Get bit depth."""
        with self._lock:
            return self._bit_depth

    @bit_depth.setter
    def bit_depth(self, value):
        """Set bit depth."""
        if value != (16 or 24):
            raise ValueError("bit_depth must be either 16 or 24.")
        with self._lock:
            self._bit_depth = value

    @property
    def sampling_freq(self):
        """Get sampling frequency."""
        with self._lock:
            return self._sampling_freq

    @sampling_freq.setter
    def sampling_freq(self, fs):
        """Set sampling frequency."""
        if not (getattr(constant, "MIN_FREQ", 8000) <= fs <= getattr(constant, "MAX_FREQ", 384000)):
            raise ValueError("Sampling frequency must be within allowed range.")
        with self._lock:
            self._sampling_freq = fs

    @property
    def directory(self):
        """Get output directory."""
        with self._lock:
            return self._directory

    @directory.setter
    def directory(self, directory_path):
        """Set output directory path."""
        if not os.path.isdir(directory_path):
            raise ValueError(f"{directory_path} is not a valid directory.")
        if not os.access(directory_path, os.W_OK):
            raise ValueError(f"{directory_path} is not writable.")
        with self._lock:
            self._directory = directory_path

    @property
    def file_name(self):
        """Get file name."""
        with self._lock:
            return self._file_name

    @file_name.setter
    def file_name(self, name):
        """Set file name."""
        with self._lock:
            self._file_name = name

    @property
    def full_path_name(self):
        """Get full path name."""
        with self._lock:
            return os.path.join(self._directory, self._file_name)

    @full_path_name.setter
    def full_path_name(self, path):
        with self._lock:
            self.full_path_name = path

    @property
    def session_number(self):
        """Get session number."""
        with self._lock:
            return self._session_number

    @session_number.setter
    def session_number(self, n_session):
        """Set session number."""
        if not (0 < n_session < 999):
            raise ValueError("Session number must be between 1 and 998.")
        with self._lock:
            self._session_number = n_session

    @property
    def session_name(self):
        """Get session name."""
        with self._lock:
            return self._session_name

    @session_name.setter
    def session_name(self, name):
        """Set session name."""
        if not (0 < len(name) < 20):
            raise ValueError("Session name must be between 1 and 19 characters.")
        with self._lock:
            self._session_name = name


# Global instance of RecordingSettings (Singleton)
rec_set: RecordingSettings = RecordingSettings()