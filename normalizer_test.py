import unittest
import normalizer

from pydub import AudioSegment, effects
from pydub.audio_segment import AudioSegment
from unittest.mock import Mock
from unittest.mock import patch
from unittest.mock import MagicMock

class TestNormalizer(unittest.TestCase):

    def test_normalize_audio(self):
        data = AudioSegment.from_file('test_data/test.wav', 'wav')
        with patch('pydub.AudioSegment.from_file', return_value = data) as mock_from_file:
            with patch('pydub.effects.normalize', return_value = data) as mock_normalized:
                with patch('pydub.AudioSegment.export') as mock_export:
                    normalizer.normalize_audio('path_in', 'path_out', 'audio_format')
                    mock_from_file.assert_called_once_with('path_in', 'audio_format')
                    mock_normalized.assert_called_once_with(data)
                    mock_export.assert_called_once_with('path_out', format='audio_format')

    def normalize_audio_with_target_dBFS(self):
        data = AudioSegment.from_file('test_data/test.wav', 'wav')
        data.dBFS = 10
        with patch('pydub.AudioSegment.from_file', return_value = data) as mock_from_file:
            with patch('pydub.AudioSegment.apply_gain', return_value = data) as mock_apply_gain:
                with patch('pydub.AudioSegment.export') as mock_export:
                    normalizer.normalize_audio('path_in', 'path_out', 'audio_format', 20)
                    mock_from_file.assert_called_once_with('path_in', 'audio_format')
                    mock_apply_gain.assert_called_once_with(10)
                    mock_export.assert_called_once_with('path_out', format='audio_format')