import numpy as np
import pyaudio
import soundfile as sf
import recording_settings
import sound_processing
import time

if __name__ == "__main__":
    rec_set = recording_settings.RecordingSettings()

    input_file = "musica1.wav"

    bit_depth_in, channels_in, sample_in = sound_processing.get_audio_properties(input_file)
    print("Input File Params", bit_depth_in, channels_in, sample_in)

    input_data, samplerate = sf.read(input_file, dtype='int16', always_2d=True)
    if samplerate != sample_in:
        print("Warning: Input file sample rate does not match the expected sample rate given by"
              "@get_audio_properties.")
        exit(-1)
    print("Read File Params", input_data.shape[1], samplerate)
    rec_set.in_data_bytes = input_data.tobytes()

    #Update sampling frequency and number of channels in rec_set
    rec_set.sampling_freq = samplerate
    rec_set.channels = channels_in

    #Creat a Streaming Class that receives our recording settings Class as Parameter
    audio_streamer = sound_processing.AudioStreamer(rec_set)

    print("Starting stream...")
    audio_streamer.start_stream()

    print("Recording and live playback in progress... (@main)")
    audio_streamer.streaming()

    # Retrieve processed audio after stopping the stream
    recorded_audio = rec_set.get_concatenated_audio()
    #Convert recorded audio to np array
    recorded_raw = recorded_audio.tobytes()

    #Write the queue to a file
    sf.write("output.flac", recorded_audio, rec_set.sampling_freq, format='FLAC')

    print("Audio recording saved successfully.")