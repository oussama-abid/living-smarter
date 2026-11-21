import asyncio
from collections.abc import Callable

from deepgram import (
    DeepgramClient,
    LiveOptions,
    LiveTranscriptionEvents,
    Microphone,
)

from config import settings


class SpeechToText:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.deepgram_api_key
        if not self.api_key:
            raise ValueError("Deepgram API key is required")

        self.deepgram = DeepgramClient(self.api_key)
        self.dg_connection = None
        self.microphone = None
        self.is_listening = False
        self.transcription_callback = None
        self.final_transcription = ""
        self.interim_transcription = ""

    def set_transcription_callback(self, callback: Callable[[str, bool], None]):
        self.transcription_callback = callback

    async def start_listening(self):
        if self.is_listening:
            print("Already listening...")
            return

        try:
            self.dg_connection = self.deepgram.listen.asynclive.v("1")

            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="1000",
                vad_events=True,
                endpointing=300,
            )

            self.dg_connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.dg_connection.on(LiveTranscriptionEvents.Warning, self._on_warning)
            self.dg_connection.on(LiveTranscriptionEvents.Metadata, self._on_metadata)
            self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, self._on_speech_started)
            self.dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, self._on_utterance_end)
            self.dg_connection.on(LiveTranscriptionEvents.Close, self._on_close)

            if not await self.dg_connection.start(options):
                print("Failed to connect to Deepgram")
                return False

            self.microphone = Microphone(self.dg_connection.send)
            self.microphone.start()

            self.is_listening = True
            print("🎤 Started listening... Speak into your microphone!")
            return True

        except Exception as e:
            print(f"Error starting transcription: {e}")
            return False

    async def stop_listening(self):
        if not self.is_listening:
            return

        self.is_listening = False

        if self.microphone:
            self.microphone.finish()
            self.microphone = None

        if self.dg_connection:
            await self.dg_connection.finish()
            self.dg_connection = None

        print("🔇 Stopped listening")

    def _on_open(self, open_msg):
        print("Connection opened")

    def _on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript

        if len(sentence) == 0:
            return

        is_final = result.is_final

        if is_final:
            self.final_transcription = sentence
            print(f"Final: {sentence}")
            if self.transcription_callback:
                self.transcription_callback(sentence, True)
        else:
            self.interim_transcription = sentence
            print(f"Interim: {sentence}")
            if self.transcription_callback:
                self.transcription_callback(sentence, False)

    def _on_speech_started(self, speech_started_msg):
        print("Speech started")

    def _on_utterance_end(self, utterance_end_msg):
        print("Utterance ended")

    def _on_error(self, error, **kwargs):
        print(f"Error: {error}")

    def _on_warning(self, warning, **kwargs):
        print(f"Warning: {warning}")

    def _on_metadata(self, metadata, **kwargs):
        print(f"Metadata: {metadata}")

    def _on_close(self, close_msg):
        print("Connection closed")

    def get_latest_transcription(self, final_only: bool = True) -> str:
        if final_only:
            return self.final_transcription
        else:
            return self.final_transcription or self.interim_transcription


def run_speech_to_text_demo():

    def transcription_handler(text: str, is_final: bool):
        status = "Final" if is_final else "Interim"
        print(f"[{status}] Transcription: {text}")

    async def demo():
        stt = SpeechToText()
        stt.set_transcription_callback(transcription_handler)

        await stt.start_listening()

        await asyncio.sleep(10)

        await stt.stop_listening()

        print(f"Final result: {stt.get_latest_transcription()}")

    asyncio.run(demo())


if __name__ == "__main__":
    run_speech_to_text_demo()
