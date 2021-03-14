import unittest
import background_separator

from unittest.mock import patch


class TestNormalizer(unittest.TestCase):
    def test_main(self):
        with patch('spleeter.separator.Separator.separate_to_file') as mock_separate_to_file:
            background_separator.main(['-input_path', 'input.wav', '-output_directory', 'output_dir'])
            mock_separate_to_file.assert_called_once_with('input.wav', 'output_dir')

    def test_main_missing_arg(self):
        with patch('background_separator.main') as mock_main:
            background_separator.main('-input_path', 'input.wav')
            mock_main.assert_called_once_with('-input_path', 'input.wav')

        with self.assertRaises(Exception) as context:
            background_separator.main('-input_path', 'input.wav')
            self.assertTrue('the following arguments are required: -input_path/--input_path' in context.exception)


if __name__ == '__main__':
    unittest.main()
