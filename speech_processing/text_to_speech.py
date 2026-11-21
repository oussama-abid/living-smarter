# speechprocessing/text_to_speech.py
import asyncio
import io

import pygame
from deepgram import DeepgramClient, SpeakOptions

from config import settings


class TextToSpeech:
    def __init__(self, api_key: str | None = None):
        """
        Initialize the Text-to-Speech handler with Deepgram

        Args:
            api_key: Deepgram API key. If None, will use DEEPGRAM_API_KEY env var
        """
        self.api_key = api_key or settings.deepgram_api_key
        if not self.api_key:
            raise ValueError("Deepgram API key is required")

        self.deepgram = DeepgramClient(self.api_key)

        # Initialize pygame mixer for audio playback
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        # Default voice settings
        self.voice_model = "aura-asteria-en"  # You can change this to other voices
        self.sample_rate = 24000

    def set_voice(self, voice_model: str):
        """
        Set the voice model for text-to-speech

        Available voices:
        - aura-asteria-en (default)
        - aura-luna-en
        - aura-stella-en
        - aura-athena-en
        - aura-hera-en
        - aura-orion-en
        - aura-arcas-en
        - aura-perseus-en
        - aura-angus-en
        - aura-orpheus-en
        - aura-helios-en
        - aura-zeus-en
        """
        self.voice_model = voice_model

    async def speak_async(self, text: str, save_to_file: str | None = None) -> bool:
        """
        Convert text to speech and play it asynchronously

        Args:
            text: Text to convert to speech
            save_to_file: Optional file path to save the audio

        Returns:
            True if successful, False otherwise
        """
        try:
            # Configure speech options
            options = SpeakOptions(
                model=self.voice_model,
                encoding="linear16",
                container="wav",
                sample_rate=self.sample_rate,
            )

            # Generate speech
            response = await self.deepgram.speak.asyncrest.v("1").stream({"text": text}, options)

            # Get audio data
            audio_data = b""
            async for chunk in response.aiter_bytes():
                audio_data += chunk

            # Save to file if requested
            if save_to_file:
                with open(save_to_file, "wb") as f:
                    f.write(audio_data)
                print(f"Audio saved to: {save_to_file}")

            # Play audio
            await self._play_audio_async(audio_data)

            return True

        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return False

    def speak(self, text: str, save_to_file: str | None = None) -> bool:
        """
        Convert text to speech and play it synchronously

        Args:
            text: Text to convert to speech
            save_to_file: Optional file path to save the audio

        Returns:
            True if successful, False otherwise
        """
        return asyncio.run(self.speak_async(text, save_to_file))

    async def _play_audio_async(self, audio_data: bytes):
        """Play audio data using pygame mixer"""
        try:
            # Create a BytesIO object from audio data
            audio_io = io.BytesIO(audio_data)

            # Load and play the audio
            pygame.mixer.music.load(audio_io)
            pygame.mixer.music.play()

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error playing audio: {e}")

    def stop_playback(self):
        """Stop current audio playback"""
        pygame.mixer.music.stop()

    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        return pygame.mixer.music.get_busy()

    def set_volume(self, volume: float):
        """
        Set playback volume

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    async def generate_audio_file(self, text: str, output_path: str) -> bool:
        """
        Generate audio file from text without playing it

        Args:
            text: Text to convert to speech
            output_path: Path where to save the audio file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Configure speech options
            options = SpeakOptions(
                model=self.voice_model,
                encoding="linear16",
                container="wav",
                sample_rate=self.sample_rate,
            )

            # Generate speech
            response = await self.deepgram.speak.asyncrest.v("1").stream({"text": text}, options)

            # Save audio data to file
            with open(output_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

            print(f"Audio file generated: {output_path}")
            return True

        except Exception as e:
            print(f"Error generating audio file: {e}")
            return False

    def cleanup(self):
        """Clean up pygame mixer"""
        pygame.mixer.quit()


def run_text_to_speech_demo():
    """Demo function to test text-to-speech functionality"""

    async def demo():
        tts = TextToSpeech()

        # Test different voices
        voices = ["aura-asteria-en", "aura-luna-en", "aura-stella-en"]

        test_text = "Hello! This is a test of the text-to-speech functionality using Deepgram."

        for voice in voices:
            print(f"Testing voice: {voice}")
            tts.set_voice(voice)
            await tts.speak_async(f"Testing {voice}. {test_text}")
            await asyncio.sleep(1)  # Small pause between voices

        # Test saving to file
        await tts.generate_audio_file("This audio will be saved to a file", "test_output.wav")

        tts.cleanup()

    asyncio.run(demo())


if __name__ == "__main__":
    run_text_to_speech_demo()
