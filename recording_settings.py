from threading import Lock
import constant
import os



class RecordingSettings:

    def __init__(self):
        self._lock = Lock()

        self._bit_depth = constant.DEFAULT_BIT_DEPTH  # default bit depth (24bit HifiBerry DAC2 ADC Pro)
        self._sampling_freq = constant.DEFAULT_SAMPLING_FREQ  # default sampling rate (194kHz HifiBerry DAC2 ADC Pro)
        self._directory = "path\\to\\save\\audio"  # path to save audio (SD Card)
        self._file_name = "default_audio.flac"  # default file name
        self._session_number = 0  # default number of session
        self._session_name = "Default_Session"  # name of default session

        # Recording Controls
        self._recording_active = False  # recording state (inactive by default)
        self._recording_start_time = None  # Start time of the recording
        self._recording_duration = 0  # Duration of the recording

    # Bit_Depth Accessors
    "get bit depth"
    @property
    def bit_depth(self):
        with self._lock:
            return self._bit_depth

    "set bit depth"

    @bit_depth.setter
    def bit_depth(self, value):
        if value not in (16, 24):
            raise ValueError("bit_depth must be either 16 or 24. (bit_depth.setter)")
        with self._lock:
            self._bit_depth = value

    # Sampling Frequency Accessors
    "get sampling frequency"

    @property
    def sampling_freq(self):
        with self._lock:
            return self._sampling_freq

    "set sampling frequency"

    @sampling_freq.setter
    def sampling_freq(self, fs):
        if not (constant.MIN_FREQ<= fs <= constant.MAX_FREQ):
            raise ValueError("sampling frequency must be between max and min frq (sampling_freq_.setter)")
        with self._lock:
            self._sampling_freq = fs

    # Directory and Filename Accessors
    @property
    def directory(self):
        """get output directory"""
        with self._lock:
            return self._directory

    @directory.setter
    def directory(self, directory_path):
        """set output directory path"""
        if not os.path.isdir(directory_path):
            raise ValueError(f"{directory_path} is not a valid directory. (directory.setter)")
        with self._lock:
            self._directory = directory_path

    @property
    def file_name(self):
        """get file name"""
        with self._lock:
            return self._file_name

    @file_name.setter
    def file_name(self, name):
        """set file name"""
        if not (0 < len(name) < 20):
            raise ValueError("Name of output file is too long or too short. (file_name.setter)")
        with self._lock:
            self._file_name = name

    @property
    def full_path_name(self):
        with self._lock:
            return f"{self._directory}/{self._file_name}"

    # Session Number/Name Accessors
    @property
    def session_number(self):
        with self._lock:
            return self._session_number

    @session_number.setter
    def session_number(self, n_session):
        if not (0 < n_session < 999):
            raise ValueError("Number os session is negative or above 999. (session_number.setter)")
        with self._lock:
            self._session_number = n_session

    @property
    def session_name(self):
        with self._lock:
            return self._session_name

    @session_name.setter
    def session_name(self, name):
        if not (0 < len(name) < 20):
            raise ValueError("Session name is too long or too short. (file_name.setter)")
        with self._lock:
            self._session_name = name


# Global instance of RecordingSettings (Singleton)
rec_set: RecordingSettings = RecordingSettings()