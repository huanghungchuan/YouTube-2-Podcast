import numpy as np
from scipy.signal import butter, lfilter
from scipy.io import wavfile


def butter_bandpass(lowcut, highcut, samplerate, order=5):
    nyq = 0.5 * samplerate
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, samplerate, order=5):
    b, a = butter_bandpass(lowcut, highcut, samplerate, order=order)
    y = lfilter(b, a, data)
    return y


def bandpass_filter(buffer, lowcut, highcut, samplerate):
    return butter_bandpass_filter(buffer, lowcut, highcut, samplerate, order=6)


def filter_noise(input_path, output_path, lowcut, highcut):
    ''' Use band-pass filter to filter noise.

    Args:
        input_path (str): The path to the original wav file.
        output_path (str): The path to the new wav file.
        lowcut (int): Low-end Hz rate of the filter.
        highcut (ing): High-end Hz rate of the filter.
    '''
    samplerate, data = wavfile.read(input_path)
    filtered_data = np.apply_along_axis(bandpass_filter, 0, data, lowcut, highcut, samplerate).astype('int16')
    wavfile.write(output_path, samplerate, filtered_data)
