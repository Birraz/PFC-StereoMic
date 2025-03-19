import wave
import pyaudio
import sys
import time
import numpy as np

def open_audio_file(filename):
    """
    Opens a WAV audio file and retrieves its parameters.

    This function opens a WAV file in read-binary mode and extracts essential audio parameters:
    number of channels, sample width, and sample rate.

    Args:
        filename (str): The path to the WAV audio file.

    Returns:
        tuple: A tuple containing:
            - wf: The opened wave file object.
            - channels (int): Number of audio channels.
            - sample_width (int): Sample width in bytes.
            - rate (int): Sampling rate in Hz.
    """
    wf = wave.open(filename, 'rb')
    channels = wf.getnchannels()
    sample_width = wf.getsampwidth()
    rate = wf.getframerate()
    return wf, channels, sample_width, rate

def get_numpy_dtype(sample_width):
    """
    Returns the appropriate NumPy data type based on sample width.

    This function maps the audio sample width (in bytes) to a corresponding NumPy data type.
    Common formats include 8-bit integers for 1-byte samples and 16-bit integers for 2-byte samples.

    Args:
        sample_width (int): The width of each audio sample in bytes.

    Returns:
        numpy.dtype: The corresponding NumPy data type (e.g., np.int8, np.int16).
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

    This function initializes a PyAudio stream with the specified audio format, channels,
    sampling rate, and callback function. It returns the configured stream.

    Args:
        p (pyaudio.PyAudio): The PyAudio instance.
        format (int): The audio format.
        channels (int): Number of audio channels.
        rate (int): Sampling rate in Hz.
        callback (function): The callback function for audio processing.

    Returns:
        pyaudio.Stream: A PyAudio stream object.
    """
    return p.open(format=format,
                  channels=channels,
                  rate=rate,
                  output=True,
                  frames_per_buffer=1024,
                  stream_callback=callback)

def callback(in_data, frame_count, time_info, status):
    """
    Callback function for processing audio frames during playback.

    This function is called by PyAudio whenever audio frames are needed. It reads frames from
    the audio file, converts them to a NumPy array for processing, and returns the processed
    audio data as bytes. Playback ends when there are no more frames to read.

    Args:
        in_data (bytes): Unused input data (required by PyAudio).
        frame_count (int): Number of frames to read.
        time_info (dict): Timing information (required by PyAudio).
        status (int): Status flag (required by PyAudio).

    Returns:
        tuple: A tuple containing processed audio data and a flag indicating whether to continue playback.
    """
    data = wf.readframes(frame_count)
    if len(data) == 0:
        return (data, pyaudio.paComplete)
    audio_data = np.frombuffer(data, dtype=np_dtype)
    processed_data = audio_data
    return (processed_data.tobytes(), pyaudio.paContinue)

# Verifica se o arquivo foi passado como argumento
if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} stereo_file.wav")
    sys.exit(-1)

# Inicializa PyAudio
p = pyaudio.PyAudio()

# Abre o arquivo de áudio
wf, channels, sample_width, RATE = open_audio_file(sys.argv[1])
FORMAT = p.get_format_from_width(sample_width)
np_dtype = get_numpy_dtype(sample_width)

# Cria e inicia o stream
stream = create_audio_stream(p, FORMAT, channels, RATE, callback)
stream.start_stream()

print("Playing audio with callback...")
print(f"Sample width: {sample_width} bytes per sample")

# Mantém o script rodando até o stream terminar
while stream.is_active():
    time.sleep(0.1)

print("Playback finished.")

# Fecha tudo no final
stream.stop_stream()
stream.close()
p.terminate()
wf.close()
