"""Stoppable microphone session using a preloaded VoiceInput model."""
import json
import threading


class VoiceSession:
    """Capture speech in a worker thread and stop cleanly on user request."""

    def __init__(self, voice_input, on_started, on_finished):
        self.voice_input = voice_input
        self.on_started = on_started
        self.on_finished = on_finished
        self._stop_requested = threading.Event()
        self._thread = threading.Thread(target=self._capture, name="AuraPlanVoiceCapture", daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_requested.set()

    def _capture(self):
        audio = None
        stream = None
        transcript_parts = []
        transcript = ""
        error = None
        try:
            import pyaudio
            from vosk import KaldiRecognizer

            audio = pyaudio.PyAudio()
            recognizer = KaldiRecognizer(self.voice_input.model, float(self.voice_input.sample_rate))
            try:
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.voice_input.sample_rate,
                    input=True,
                    input_device_index=self.voice_input.device_index,
                    frames_per_buffer=self.voice_input.chunk_size,
                )
            except Exception as exc:
                hint = (f" (device index {self.voice_input.device_index})"
                        if self.voice_input.device_index is not None else "")
                raise RuntimeError(
                    f"Could not open microphone{hint} at {self.voice_input.sample_rate} Hz. "
                    "Check microphone permissions and input devices."
                ) from exc

            self.on_started()
            while not self._stop_requested.is_set():
                try:
                    data = stream.read(self.voice_input.chunk_size, exception_on_overflow=False)
                except Exception as exc:
                    if self._stop_requested.is_set():
                        break
                    raise RuntimeError(f"Could not read microphone audio: {exc}") from exc
                if recognizer.AcceptWaveform(data):
                    phrase = json.loads(recognizer.Result()).get("text", "").strip()
                    if phrase:
                        transcript_parts.append(phrase)

            final_phrase = json.loads(recognizer.FinalResult()).get("text", "").strip()
            if final_phrase:
                transcript_parts.append(final_phrase)
            transcript = " ".join(transcript_parts).strip()
        except Exception as exc:
            error = str(exc)
        finally:
            try:
                if stream is not None:
                    if stream.is_active():
                        stream.stop_stream()
                    stream.close()
            finally:
                if audio is not None:
                    audio.terminate()
        self.on_finished(transcript, error)
