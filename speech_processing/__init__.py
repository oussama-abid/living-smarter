# speechprocessing/__init__.py
from .speech_to_text import SpeechToText
from .text_to_speech import TextToSpeech
from .audio_handler import AudioHandler

__all__ = ['SpeechToText', 'TextToSpeech', 'AudioHandler']