import numpy as np
import pyaudio
import soundfile as sf
import recording_settings
import sound_processing
import time

if __name__ == "__main__":
    rec_set = recording_settings.RecordingSettings()
    audio_streamer = sound_processing.AudioStreamer(rec_set)

    input_file = "C:\\Users\\dadoa\\Desktop\\ISEL\\Final Project\\Musica\\whiteNoise1.flac"
    bit_depth_in, channels_in, sample_in = sound_processing.get_audio_properties(input_file)
    print("Input File Params", bit_depth_in, channels_in, sample_in)

    input_data_float32, samplerate = sf.read(input_file, dtype='float32')
    rec_set.in_data_bytes = input_data_float32.tobytes()

    rec_set.sampling_freq = samplerate
    rec_set.channels = channels_in

    try:
        print("Starting stream...")
        audio_streamer.start_stream()

        print("Recording and live playback in progress... Press Ctrl+C to stop.")
        audio_streamer.streaming()

    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Stopping stream...")

    except Exception as general_e:
        print(f"An unexpected exception occurred: {general_e}")

    finally:
        # Retrieve processed audio after stopping the stream
        recorded_audio = rec_set.get_concatenated_audio()

        # Safe conversion and scaling before saving to file
        if recorded_audio.dtype in (np.float32, np.float64):
            recorded_audio = np.clip(recorded_audio, -1.0, 1.0)
            recorded_audio = (recorded_audio * np.iinfo(np.int16).max).astype(np.int16)

        sf.write("C:\\Users\\dadoa\\Desktop\\ISEL\\Final Project\\Musica\\output.flac", recorded_audio, rec_set.sampling_freq, format='FLAC')

        print("Audio recording saved successfully.")