import abc
import asyncio
import azure.cognitiveservices.speech as speechsdk

class TTSProvider(abc.ABC):

    @abc.abstractmethod
    async def generate(self, prompt: str) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def build_speech_config(self) -> any:
        raise NotImplementedError




class AzureTTSProvider(TTSProvider):
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint

    def build_speech_config(self):
        pass

    def _synthesize_sync(self, prompt: str) -> dict:
        speech_config = speechsdk.SpeechConfig(subscription=self.api_key, endpoint=self.endpoint)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

        result = synthesizer.speak_ssml_async(prompt).get()  # ← this line

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return {"state": "Success", "audio": result.audio_data}

        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            return {
                "state": f"Speech synthesis canceled: {cancellation_details.error_details}",
                "audio": None,
            }

    async def generate(self, prompt: str) -> dict:
        return await asyncio.to_thread(self._synthesize_sync, prompt)