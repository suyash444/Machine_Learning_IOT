#Importing the libraries

import os
import numpy as np
import tensorflow as tf
import sounddevice as sd
from scipy.io.wavfile import write
from preprocessing import MelSpectrogram
from time import time

# Set basic parameters for audio processing
resolution = 'int16'
sample_rate = 16000  # Sampling rate remains the same
frame_length = 0.035  # Frame length increased to 0.035 seconds
frame_step = 0.05
num_mel_bins = 12  # Number of Mel bins increased to 12
lower_frequency = 0  # Lower frequency remains the same
upper_frequency = 7500  # Upper frequency reduced to 7500 Hz

channels = 1
duration = 0.5  # Duration set to half a second
dbfsthres = -42  # dbFS Threshold changed to -42
duration_thres = 0.12  # Duration Threshold increased to 0.12 seconds
blocksize = int(duration * sample_rate)
audio_buffer = np.zeros(shape=(sample_rate, 1))

# Class for Voice Activity Detection
class VAD:
    def __init__(self, sampling_rate, frame_length_in_s, num_mel_bins, lower_frequency, upper_frequency, dbFSthres, duration_thres):
        self.frame_length_in_s = frame_length_in_s
        self.mel_spec_processor = MelSpectrogram(sampling_rate, frame_length_in_s, frame_length_in_s, num_mel_bins, lower_frequency, upper_frequency)
        self.dbFSthres = dbFSthres
        self.duration_thres = duration_thres

    def detect_silence(self, audio_sample):
        audio_reader = AudioReader(tf.int16, sample_rate)
        processed_audio = audio_reader.process_input(audio_sample)
        mel_spec_processor = MelSpectrogram(sample_rate, frame_length, frame_step, num_mel_bins, lower_frequency, upper_frequency)
        log_mel_spectrogram = self.mel_spec_processor.get_mel_spec(processed_audio)
        decibels_full_scale = 20 * log_mel_spectrogram
        average_energy = tf.math.reduce_mean(decibels_full_scale, axis=1)

        is_voiced = average_energy > self.dbFSthres
        voiced_frame_count = tf.math.reduce_sum(tf.cast(is_voiced, tf.float32))
        voiced_duration = (voiced_frame_count + 1) * self.frame_length_in_s

        return False if voiced_duration > self.duration_thres else True

# Class to handle audio data
class AudioReader:
    def __init__(self, resolution, sampling_rate):
        self.resolution = resolution
        self.sampling_rate = sampling_rate

    def process_input(self, input_data):
        audio_tensor = tf.convert_to_tensor(input_data, dtype=tf.float32)
        audio_tensor_squeezed = tf.squeeze(audio_tensor)
        normalized_audio = audio_tensor_squeezed / tf.int16.max
        return normalized_audio

audio_reader = AudioReader(tf.int16, sample_rate)

def analyze_audio_frame(input_frame):
    processed_frame = audio_reader.process_input(input_frame)
    mel_spec_processor = MelSpectrogram(sample_rate, frame_length, frame_step, num_mel_bins, lower_frequency, upper_frequency)
    log_mel_spectrogram = mel_spec_processor.get_mel_spec(processed_frame)
    decibels_full_scale = 20 * log_mel_spectrogram
    average_energy = tf.math.reduce_mean(decibels_full_scale, axis=1)
    is_voiced = average_energy > dbfsthres
    voiced_frame_count = tf.math.reduce_sum(tf.cast(is_voiced, tf.float32))
    voiced_duration = (voiced_frame_count + 1) * frame_length

    return False if voiced_duration > duration_thres else True

def begin_audio_recording():
    with sd.InputStream(device=0, channels=1, dtype='int16', samplerate=sample_rate, blocksize=blocksize, callback=audio_callback):
        while True:
            user_input = input()
            if user_input.lower() == 'q':
                print('Ending audio recording session.')
                break

def audio_callback(input_data, frame_count, time_info, status):
    global audio_buffer, store_audio
    audio_buffer = np.roll(audio_buffer, blocksize)
    audio_buffer[blocksize:, :] = input_data
    store_audio_decision = vad.detect_silence(audio_buffer)

    if not store_audio_decision:
        current_time = time()
        output_filename = f'{current_time}.wav'
        write(output_filename, 16000, input_data)
        file_size = os.path.getsize(output_filename) / 1024
        print(f'Recorded File Size: {file_size:.2f} KB')

if __name__ == "__main__":
    try:
        store_audio = True
        vad = VAD(sample_rate, frame_length, num_mel_bins, lower_frequency, upper_frequency, dbfsthres, duration_thres)
        begin_audio_recording()
    except KeyboardInterrupt:
        print('Audio recording has been stopped.')
