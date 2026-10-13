import os
import json
import pyaudio
from vosk import Model, KaldiRecognizer

class VoiceInput:
    def __init__(self, model_path: str = "model"):
        """
        Initializes the Vosk offline speech recognition engine.
        Make sure a valid Vosk model directory is placed at `model_path`.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Vosk model directory not found at '{model_path}'. "
                "Download a model from https://alphacephei.com/vosk/models and extract it here."
            )
        self.model = Model(model_path)
        self.sample_rate = 16000

    def listen_once(self) -> str:
        """
        Captures microphone input until speech is recognized or an error occurs,
        then returns the resulting text string.
        """
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=8000
            )
            stream.start_stream()
            
            recognizer = KaldiRecognizer(self.model, self.sample_rate)
            print("[VoiceInput] Listening for command...")

            while True:
                data = stream.read(4000, exception_on_overflow=False)
                if not data:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        print(f"[VoiceInput] Recognized: {text}")
                        return text

        except Exception as e:
            print(f"[VoiceInput] Microphone error: {e}")
            return ""
        finally:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            p.terminate()

        # Fallback for final buffer
        final_result = json.loads(recognizer.FinalResult())
        return final_result.get("text", "").strip()

if __name__ == "__main__":
    # Test script for voice input
    print("Initializing Voice Input Test...")
    try:
        voice = VoiceInput(model_path="model")
        command = voice.listen_once()
        print(f"Final Output: '{command}'")
    except Exception as err:
        print(f"Setup Error: {err}")