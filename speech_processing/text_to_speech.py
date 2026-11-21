import asyncio
import io

import pygame
from deepgram import DeepgramClient, SpeakOptions

from config import settings


class TextToSpeech:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.deepgram_api_key
        if not self.api_key:
            raise ValueError("Deepgram API key is required")

        self.deepgram = DeepgramClient(self.api_key)

        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

        self.voice_model = "aura-asteria-en"
        self.sample_rate = 24000

    def set_voice(self, voice_model: str):
        self.voice_model = voice_model

    async def speak_async(self, text: str, save_to_file: str | None = None) -> bool:
        try:
            options = SpeakOptions(
                model=self.voice_model,
                encoding="linear16",
                container="wav",
                sample_rate=self.sample_rate,
            )

            response = await self.deepgram.speak.asyncrest.v("1").stream({"text": text}, options)

            audio_data = b""
            async for chunk in response.aiter_bytes():
                audio_data += chunk

            if save_to_file:
                with open(save_to_file, "wb") as f:
                    f.write(audio_data)
                print(f"Audio saved to: {save_to_file}")

            await self._play_audio_async(audio_data)

            return True

        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return False

    def speak(self, text: str, save_to_file: str | None = None) -> bool:
        return asyncio.run(self.speak_async(text, save_to_file))

    async def _play_audio_async(self, audio_data: bytes):
        try:
            audio_io = io.BytesIO(audio_data)

            pygame.mixer.music.load(audio_io)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Error playing audio: {e}")

    def stop_playback(self):
        pygame.mixer.music.stop()

    def is_playing(self) -> bool:
        return pygame.mixer.music.get_busy()

    def set_volume(self, volume: float):
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    async def generate_audio_file(self, text: str, output_path: str) -> bool:
        try:
            options = SpeakOptions(
                model=self.voice_model,
                encoding="linear16",
                container="wav",
                sample_rate=self.sample_rate,
            )

            response = await self.deepgram.speak.asyncrest.v("1").stream({"text": text}, options)

            with open(output_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)

            print(f"Audio file generated: {output_path}")
            return True

        except Exception as e:
            print(f"Error generating audio file: {e}")
            return False

    def cleanup(self):
        pygame.mixer.quit()


def run_text_to_speech_demo():

    async def demo():
        tts = TextToSpeech()

        voices = ["aura-asteria-en", "aura-luna-en", "aura-stella-en"]

        test_text = "Hello! This is a test of the text-to-speech functionality using Deepgram."

        for voice in voices:
            print(f"Testing voice: {voice}")
            tts.set_voice(voice)
            await tts.speak_async(f"Testing {voice}. {test_text}")
            await asyncio.sleep(1)

        await tts.generate_audio_file("This audio will be saved to a file", "test_output.wav")

        tts.cleanup()

    asyncio.run(demo())


if __name__ == "__main__":
    run_text_to_speech_demo()
