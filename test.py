import wave
import pyaudio
import numpy as np
import time
import sys

# Ensure you pass the filename of a stereo wave file
if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} C:\\Users\\dadoa\\Downloads\\bush_infiltrate.wav")
    sys.exit(-1)

# Open the stereo wave file
wf = wave.open(sys.argv[1], 'rb')

# Check that the file is stereo
if wf.getnchannels() != 1:
    print("Error: The file is not stereo!")
    sys.exit(-1)

# Audio stream parameters
FORMAT = pyaudio.paInt16
CHANNELS = wf.getnchannels()  # 2 channels
RATE = wf.getframerate()      # e.g., 44100 or 48000 Hz
FRAMES_PER_BUFFER = 1024      # Buffer size

# Callback for processing the audio.
def callback(in_data, frame_count, time_info, status):
    # Read the next chunk of frames from the file
    data = wf.readframes(frame_count)
    if len(data) == 0:
        # No more data, signal stream completion
        return (data, pyaudio.paComplete)
    
    # Convert byte data to a NumPy array for processing.
    # For stereo 16-bit audio, the samples are interleaved.
    audio_data = np.frombuffer(data, dtype=np.int8)
    
    # Example processing: simply pass through the data.
    # Insert your custom processing logic here.
    processed_data = audio_data  # No changes
    
    # Convert back to bytes for playback.
    return (processed_data.tobytes(), pyaudio.paContinue)

# Initialize PyAudio.
p = pyaudio.PyAudio()

# Open an output stream. (Input is not needed here.)
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                output=True,
                frames_per_buffer=FRAMES_PER_BUFFER,
                stream_callback=callback)

# Start the stream.
stream.start_stream()
print("Playing and processing the stereo file. Press Ctrl+C to stop early.")
print(wf.getnchannels() ,"Channel")


# Keep the stream active until playback is complete.

while stream.is_active():
    time.sleep(0.1)


# Cleanup: stop the stream and terminate PyAudio.
stream.stop_stream()
stream.close()
p.terminate()
wf.close()