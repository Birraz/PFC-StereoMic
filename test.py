import wave
import pyaudio
import numpy as np
import time
import sys

# Get the file path from command-line arguments or user input
if len(sys.argv) < 2:
    file_path = input("Enter the path to the .wav file: ")
else:
    file_path = sys.argv[1]

# Open the wave file
try:
    wf = wave.open(file_path, 'rb')
except FileNotFoundError:
    print(f"Error: File not found at {file_path}")
    sys.exit(-1)
except wave.Error:
    print(f"Error: Unable to open the file at {file_path}. Ensure it is a valid .wav file.")
    sys.exit(-1)

# Print the number of channels for debugging
print(f"Number of channels: {wf.getnchannels()}")

# Audio stream parameters
FORMAT = pyaudio.paInt16
CHANNELS = wf.getnchannels()  # Number of channels
RATE = wf.getframerate()      # Sample rate (e.g., 44100 or 48000 Hz)
FRAMES_PER_BUFFER = 1024      # Buffer size

# Convert stereo to mono
def stereo_to_mono(audio_data):
    audio_data = np.frombuffer(audio_data, dtype=np.int16)
    audio_data = audio_data.reshape(-1, 2)  # Assuming stereo (2 channels)
    mono_data = np.mean(audio_data, axis=1).astype(np.int16)
    return mono_data.tobytes()

# Callback for processing the audio.
def callback(in_data, frame_count, time_info, status):
    # Read the next chunk of frames from the file
    data = wf.readframes(frame_count)
    if len(data) == 0:
        # No more data, signal stream completion
        return (data, pyaudio.paComplete)
    
    # Convert stereo to mono if necessary
    if CHANNELS == 2:
        data = stereo_to_mono(data)
    
    # Convert byte data to a NumPy array for processing.
    audio_data = np.frombuffer(data, dtype=np.int16)
    
    # Example processing: simply pass through the data.
    processed_data = audio_data  # No changes
    
    # Convert back to bytes for playback.
    return (processed_data.tobytes(), pyaudio.paContinue)

# Initialize PyAudio.
p = pyaudio.PyAudio()

# Open an output stream. (Input is not needed here.)
stream = p.open(format=FORMAT,
                channels=1 if CHANNELS == 2 else CHANNELS,  # Output mono if input is stereo
                rate=RATE,
                output=True,
                frames_per_buffer=FRAMES_PER_BUFFER,
                stream_callback=callback)

# Start the stream.
stream.start_stream()
print("Playing and processing the file. Press Ctrl+C to stop early.")
print(wf.getnchannels(), "Channel")

# Keep the stream active until playback is complete.
while stream.is_active():
    time.sleep(0.1)

# Cleanup: stop the stream and terminate PyAudio.
stream.stop_stream()
stream.close()
p.terminate()
wf.close()