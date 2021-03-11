import collections
import contextlib
import sys
import wave
import webrtcvad
import librosa
import soundfile
from pydub import AudioSegment


def read_wave(path):
    ''' Reading a wav file from the given path.

    Args:
        path (str): The path to the wav file.

    Returns:
        bytes: The wav pcm data.
        int: Sample rate
    '''
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000, 48000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    """ Write a wav file

    Args:
        path (str): The path to the wav file.
        audio (bytes): pcm audio data.
        sample_rate (int): the sample rate of the pcm audio data.
    """
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)

def convert_wave_to_meet_vad(original_path, output_path):
    ''' Convert the wav data to the formats that meets webrtc requirements:
    1. sample rate reformat to either [8000, 16000, 32000, 48000]
    2. Convert to mono audio
    3. Convert to 16-bits format

    Args:
        original_path (str): Path to original wav file.
        output_path (str): Path to output wav file.
    '''
    resample_wave(original_path, output_path)
    convert_to_mono(output_path)
    convert_to_16bit(output_path)

def convert_to_16bit(path):
    ''' Convert the wav audio file to 16-bits format.

    This will overwrite the given file.

    Args:
        path (str): Path to the audio file.
    '''
    data,  samplerate = soundfile.read(path)
    soundfile.write(path, data, samplerate, subtype='PCM_16')

def convert_to_mono(path):
    ''' Convert the wav file to monophonic records.

    This will overwrite the given file.

    Args:
        path (str): Path to the audio file.
    '''
    print('convert to mono')
    sound = AudioSegment.from_wav(path)
    sound = sound.set_channels(1)
    sound.export(path, format="wav")
    print('finish convert to mono')

def resample_wave(original_path, output_path):
    ''' Resample the wav audio to the sample rate that will meet the webrtcvad requirement.

    Use Librosa to convert the original sample rate to the closest of either [8000, 16000, 32000, 48000].
    The new audio will be written to the given output path.

    Args:
        original_path (str): Path to the original wav file.
        output_path (str): Path to the new wav file.
    '''
    print('resample wave')
    available_sample_rate = [8000, 16000, 32000, 48000]
    current_closest = 0

    data, audio_sample_rate = librosa.load(original_path)
    current_diff = audio_sample_rate

    print(audio_sample_rate)
    for sr in available_sample_rate:
        if abs(sr - audio_sample_rate) < current_diff:
            current_diff = abs(sr - audio_sample_rate)
            current_closest = sr
    print(current_closest)
    data = librosa.resample(data, audio_sample_rate, current_closest)
    librosa.output.write_wav(output_path, data, current_closest)
    print('finish resample wave')


class Frame(object):
    ''' This is a class used for separating the audio data into smaller pieces of data.

    Args:
        bytes (bytes): pcm audio data.
        timestamp (float): The starting timestamp of the original audio.
        duration (float): The duration of this frame.

    '''
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """ Generates audio frames from PCM audio data.

    Separate the audio data into frames that contains the pcm audio data of given duration.
    To meet the requirement of webrtc, the duration must be either 10, 20 or 30 milliseconds,
    sample rate must be either 8000, 16000, 32000 or 48000.

    Args:
        frame_duration_ms (int): The duration of each frame in milliseconds.
        audio (bytes): The pcm audio data that will be separated into frames.
        sample_rate (int): The sample rate of the given audio.

    Yields:
        Frame: The Frames created after separating the audio data.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames):
    ''' Filter out the silenced audio frames.

    Using Webrtcvad to detect whether a given frame contains voice.
    Using sliding-window algorithm to pass the frames to Vad.
    Once there are 90% continuous frames that are detected
    as unsilenced, it will start yielding the audio data from the frames.
    Once there are over 90% of continuous frames that are detected as silenced, it will stop yielding the audio data.

    Args:
        sample_rate (int): The sample rate of the audio data.
        frame_duration_ms (int): The audio duration of each frame.
        padding_duration_ms (int): The amount of padding frames.
        vad (webrtcvad.Vad): An instance of Vad.
        frames (list(Frame)): A list of frames that were generated from a wav audio.

    Yields:
         bytes: PCM audio data.
    '''
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        sys.stdout.write('1' if is_speech else '0')
        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])
            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > 0.95 * ring_buffer.maxlen:
                triggered = True
                sys.stdout.write('+(%s)' % (ring_buffer[0][0].timestamp,))
                # We want to yield all the audio we see from now until
                # we are NOTTRIGGERED, but we have to start with the
                # audio that's already in the ring buffer.
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.95 * ring_buffer.maxlen:
                sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []
    if triggered:
        sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
    sys.stdout.write('\n')
    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])

def generate_solo_audio(input_path, output_path, aggressiveness):
    ''' Remove the silence audio segments from the audio file.

    From vocals.wav of the given podcast name, convert the audio file:
    1. to monophonic sound
    2. the sample rate to one of [8000, 16000, 32000, 48000]
    3. to 16-bits format

    The new audio file will be written into 'non-silenced' directory.

    Args:
        input_path (str): The path to the original audio file.
        output_path (str): The path to the new audio file.
        aggressiveness (int): The aggressiveness of the silence detector. This must be either 0, 1, 2 or 3, while 3 is
                              the most aggressive mode.
    '''
    original_path = input_path
    output_path = output_path
    convert_wave_to_meet_vad(original_path, output_path)
    audio, sample_rate = read_wave(output_path)
    vad = webrtcvad.Vad(aggressiveness)
    frames = frame_generator(30, audio, sample_rate)
    frames = list(frames)
    segments = vad_collector(sample_rate, 30, 600, vad, frames)

    concataudio = [segment for segment in segments]

    joinedaudio = b"".join(concataudio)

    write_wave(output_path, joinedaudio, sample_rate)