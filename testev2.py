import wave
import pyaudio
import sys
import time
import numpy as np
import bluetooth

def start_bluetooth_server():
    """
    Starts a Bluetooth server to listen for incoming connections.
    """
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]
    uuid = "00001101-0000-1000-8000-00805F9B34FB"  # Standard SerialPortService ID

    bluetooth.advertise_service(server_sock, "PythonBluetoothServer", service_id=uuid)

    print("Waiting for connection on RFCOMM channel", port)

    client_sock, client_info = server_sock.accept()
    print("Accepted connection from", client_info)

    try:
        while True:
            data = client_sock.recv(1024)
            if not data:
                break
            print("Received:", data.decode())
            client_sock.send("Message received!")
    except IOError:
        pass

    print("Disconnected.")

    client_sock.close()
    server_sock.close()

# Start the Bluetooth server in a separate thread
import threading
bluetooth_thread = threading.Thread(target=start_bluetooth_server)
bluetooth_thread.daemon = True
bluetooth_thread.start()
def open_audio_file(filename):
    """
    Opens a WAV audio file and retrieves its parameters.

    Args:
        filename (str): The path to the WAV audio file.

    Returns:
        tuple: A tuple containing:
            - wf: The opened wave file object.
            - channels (int): Number of audio channels.
            - sample_width (int): Sample width in bytes.
            - rate (int): Sampling rate in Hz.
    """
    try:
        wf = wave.open(filename, 'rb')
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        rate = wf.getframerate()
        return wf, channels, sample_width, rate
    except FileNotFoundError:
        print(f"Error: File not found at {filename}")
        sys.exit(-1)
    except wave.Error:
        print(f"Error: Unable to open the file at {filename}. Ensure it is a valid .wav file.")
        sys.exit(-1)

def get_numpy_dtype(sample_width):
    """
    Returns the appropriate NumPy data type based on sample width.

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
        return np.int16  # Default to 16-bit if sample width is unknown

def create_audio_stream(p, format, channels, rate, callback):
    """
    Creates and returns a PyAudio stream for audio playback.

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
    processed_data = audio_data  # No processing, just pass through
    return (processed_data.tobytes(), pyaudio.paContinue)

# Get the file path from command-line arguments or user input
if len(sys.argv) < 2:
    file_path = input("Enter the path to the .wav file: ")
else:
    file_path = sys.argv[1]

# Open the audio file
wf, channels, sample_width, RATE = open_audio_file(file_path)

# Initialize PyAudio
p = pyaudio.PyAudio()
FORMAT = p.get_format_from_width(sample_width)
np_dtype = get_numpy_dtype(sample_width)

# Create and start the stream
stream = create_audio_stream(p, FORMAT, channels, RATE, callback)
stream.start_stream()

print("Playing audio with callback...")
print(f"Sample width: {sample_width} bytes per sample")
print(f"Number of channels: {channels}")
print(f"Sample rate: {RATE} Hz")

# Keep the script running until the stream finishes
while stream.is_active():
    time.sleep(0.1)

print("Playback finished.")

# Clean up
stream.stop_stream()
stream.close()
p.terminate()
wf.close()