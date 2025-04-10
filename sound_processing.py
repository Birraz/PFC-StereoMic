import scipy.signal as signal
import soundfile as sf
import numpy as np
import audio_settings


def get_audio_properties(file_path):
    """Retrieve bit depth, format, sampling rate, and channels from an audio file."""
    with sf.SoundFile(file_path) as audio_file:
        bit_depth = audio_file.subtype_info  # Subtype gives the precise bit depth
        channels = audio_file.channels  # Number of audio channels
        rate = audio_file.samplerate  # Sampling rate
        return bit_depth, channels, rate

def band_pass_filter(audio_data, low_freq, high_freq, sample_rate, order=4):

    low_freq = low_freq / (sample_rate / 2)
    high_freq = high_freq / (sample_rate / 2)

    sos = signal.butter(order, (low_freq, high_freq), btype='bandpass', output='sos')
    filtered_audio: np.ndarray = signal.sosfilt(sos, audio_data)
    #b, a = signal.butter(6, (low_freq + 0.01 ,high_freq),btype="bandpass", analog=False)
    #filtered_audio: np.ndarray = signal.filtfilt(b,a, audio_data, axis=0)

    return filtered_audio

def apply_equalizer(data, samplerate, bit_depth, audio_set=audio_settings.AudioSettings()):
    eq_bands = audio_set.eq_bands

    if not eq_bands:
        print("No equalizer bands set, returning original data.")
        return data

    nyquist = samplerate / 2
    equalized_data = np.array(data, dtype=np.float64)  # Start from original audio

    for band_id, (freq, gain, q) in eq_bands.items():
        # Pass the gain from dB to linear
        linear_gain = 10 ** (gain / 20)

        # Calculate the bandwidth based on the q factor
        bandwidth = freq / q

        # Calculate the lower and upper frequency of the band pass filter
        low_freq = (freq - (bandwidth / 2)) / nyquist
        high_freq = (freq + (bandwidth / 2)) / nyquist

        if not (0 < low_freq < high_freq < 1):
            raise ValueError(f"Invalid frequency band limits: {low_freq * nyquist}Hz to {high_freq * nyquist}Hz")

        #sos = signal.butter(N=4, Wn=(low_freq, high_freq), btype='bandpass', output='sos')
        #filtered_band = signal.sosfilt(sos, data)
        b, a = signal.butter(4, (low_freq, high_freq), btype="bandpass", analog=False, output="ba")
        signal.freqz(b, a)
        # Apply this filter to your audio data
        filtered_band: np.ndarray = signal.filtfilt(b, a, data, axis=0)

        # Modify only incremental gains, avoid replacing content
        equalized_data += filtered_band  * linear_gain

        return equalized_data











