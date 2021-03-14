import bandfilter
import unittest

from scipy.io import wavfile


class TestBandfilter(unittest.TestCase):
    def test_filter_noise(self):
        input_path = 'test_data/test.wav'
        output_path = 'test_data/bandfilter_output.wav'
        lowcut = 100
        highcut = 6000
        expected_output_samplerate, expected_output_data = wavfile.read('test_data/expected_bandfilter_output.wav')

        bandfilter.filter_noise(input_path, output_path, lowcut, highcut)
        output_samplerate, output_data = wavfile.read('test_data/bandfilter_output.wav')

        self.assertEqual(expected_output_samplerate, output_samplerate)
        self.assertTrue((expected_output_data == output_data).all())

    def test_filter_noise_invalid_input_path(self):
        input_path = 'test_data/invalid_audio.wav'
        output_path = 'test_data/bandfilter_output.wav'
        lowcut = 100
        highcut = 6000

        with self.assertRaises(FileNotFoundError):
            bandfilter.filter_noise(input_path, output_path, lowcut, highcut)
