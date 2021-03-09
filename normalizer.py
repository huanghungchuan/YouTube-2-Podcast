from pydub import AudioSegment, effects

def normalize_audio(path_in, path_out, audio_format):
    ''' Normalize the audio volume.

    Args:
        path_in (str): The path to the original wav file.
        path_out (str): The path to the new wav file.
        audio_format (str): Audio encoding format, such as mp3, wav, etc.
    '''
    data = AudioSegment.from_file(path_in, audio_format)
    normalized_data = effects.normalize(data)
    normalized_data.export(path_out, format=audio_format)

def normalize_audio_with_target_dBFS(path_in, path_out, audio_format, target_dBFS):
    ''' Normalize the audio volume to the targeted dBFS.

    Args:
        path_in (str): The path to the original wav file.
        path_out (str): The path to the new wav file.
        audio_format (str): Audio encoding format, such as mp3, wav, etc.
        target_dBFS (float): Target dBFS the audio is going to be normalized.
    '''
    data = AudioSegment.from_file(path_in, audio_format)
    change_in_dBFS = target_dBFS - data.dBFS
    normalized_data = data.apply_gain(change_in_dBFS)
    normalized_data.export(path_out, format=audio_format)