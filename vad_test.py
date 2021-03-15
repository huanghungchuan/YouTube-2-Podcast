import unittest
import vad
import wave

from unittest.mock import patch, ANY


class TestVad(unittest.TestCase):
    def test_read_wave(self):
        test_audio_path = 'test_data/test.wav'
        data = wave.open(test_audio_path, 'rb')
        with patch('wave.Wave_read.getnchannels', return_value=1):
            with patch('wave.Wave_read.getsampwidth', return_value=2):
                with patch('wave.Wave_read.getframerate', return_value=16000):
                    pcm_data, sample_rate = vad.read_wave(test_audio_path)
                    self.assertEqual(pcm_data, data.readframes(data.getnframes()))

    def test_read_wave_invalid_path(self):
        fake_audio_path = 'test_data/invalid.wav'
        with self.assertRaises(FileNotFoundError):
            vad.read_wave(fake_audio_path)

    def test_write_wave(self):
        test_audio_path = 'test_data/test.wav'
        output_audio_path = 'test_data/vad_output.wav'
        expected_wave_read = wave.open(test_audio_path, 'rb')
        expected_sample_rate = expected_wave_read.getframerate()
        expected_pcm_data = expected_wave_read.readframes(expected_wave_read.getnframes())

        vad.write_wave(output_audio_path, expected_pcm_data, expected_sample_rate)
        wave_read = wave.open(output_audio_path, 'rb')
        sample_rate = wave_read.getframerate()
        pcm_data = wave_read.readframes(wave_read.getnframes())

        self.assertEqual(expected_sample_rate, sample_rate)
        self.assertEqual(expected_pcm_data, pcm_data)

    def test_write_wave_invalid_path(self):
        invalid_path = 'invalid/file/path.wav'
        wave_read = wave.open('test_data/test.wav', 'rb')
        sample_rate = wave_read.getframerate()
        pcm_data = wave_read.readframes(wave_read.getnframes())
        with self.assertRaises(FileNotFoundError):
            with self.assertRaises(AttributeError):
                vad.write_wave(invalid_path, pcm_data, sample_rate)

    def test_write_wave_invalid_pcm_data_type(self):
        test_audio_path = 'test_data/test.wav'
        output_audio_path = 'test_data/vad_output.wav'
        wave_read = wave.open(test_audio_path, 'rb')
        sample_rate = wave_read.getframerate()
        invalid_data = "invalid data"

        with self.assertRaises(TypeError):
            with self.assertRaises(AttributeError):
                vad.write_wave(output_audio_path, invalid_data, sample_rate)

    def test_convert_to_16bit(self):
        test_audio_path = 'test_data/test.wav'
        output_audio_path = 'test_data/vad_convert_to_16bit.wav'
        expected_wave_read = wave.open(test_audio_path, 'rb')
        expected_sample_rate = expected_wave_read.getframerate()
        expected_pcm_data = expected_wave_read.readframes(expected_wave_read.getnframes())
        expected_sample_width = 2
        expected_num_channels = expected_wave_read.getnchannels()

        vad.convert_to_16bit(test_audio_path, output_audio_path)
        wave_read = wave.open(output_audio_path, 'rb')
        sample_rate = wave_read.getframerate()
        pcm_data = wave_read.readframes(wave_read.getnframes())
        sample_width = wave_read.getsampwidth()
        num_channels = wave_read.getnchannels()

        self.assertEqual(expected_pcm_data, pcm_data)
        self.assertEqual(expected_sample_rate, sample_rate)
        self.assertEqual(expected_sample_width, sample_width)
        self.assertEqual(expected_num_channels, num_channels)

    def test_convert_to_16_bit_invalid_input_path(self):
        invalid_input_path = 'invalid/file/path.wav'
        valid_output_path = 'test_data/valid_output.wav'

        with self.assertRaises(RuntimeError):
            vad.convert_to_16bit(invalid_input_path, valid_output_path)

    def test_convert_to_16_bit_invalid_outut_path(self):
        valid_input_path = 'test_data/test.wav'
        invalid_output_path = 'invalid/file/path.wav'

        with self.assertRaises(RuntimeError):
            vad.convert_to_16bit(valid_input_path, invalid_output_path)

    def test_convert_to_mono(self):
        test_audio_path = 'test_data/test.wav'
        output_audio_path = 'test_data/vad_convert_to_mono.wav'
        expected_wave_read = wave.open(test_audio_path, 'rb')
        expected_sample_rate = expected_wave_read.getframerate()
        expected_sample_width = expected_wave_read.getsampwidth()
        expected_num_channels = 1

        vad.convert_to_mono(test_audio_path, output_audio_path)
        wave_read = wave.open(output_audio_path, 'rb')
        sample_rate = wave_read.getframerate()
        sample_width = wave_read.getsampwidth()
        num_channels = wave_read.getnchannels()

        self.assertEqual(expected_sample_rate, sample_rate)
        self.assertEqual(expected_sample_width, sample_width)
        self.assertEqual(expected_num_channels, num_channels)

    def test_convert_to_mono_invalid_input_path(self):
        invalid_input_path = 'invalid/file/path.wav'
        valid_output_path = 'test_data/valid_output.wav'

        with self.assertRaises(FileNotFoundError):
            vad.convert_to_mono(invalid_input_path, valid_output_path)

    def test_convert_to_mono_invalid_outut_path(self):
        valid_input_path = 'test_data/test.wav'
        invalid_output_path = 'invalid/file/path.wav'

        with self.assertRaises(FileNotFoundError):
            vad.convert_to_mono(valid_input_path, invalid_output_path)

    def test_resample_wave(self):
        test_audio_path = 'test_data/test.wav'
        output_audio_path = 'test_data/vad_resample.wav'
        expected_sample_rate = 16000
        with patch('librosa.output.write_wav', return_value=1) as mock_write_wav:
            vad.resample_wave(test_audio_path, output_audio_path)
            mock_write_wav.assert_called_once_with(output_audio_path, ANY, expected_sample_rate)
