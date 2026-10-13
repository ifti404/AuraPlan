"""Offline microphone speech recognition with Vosk and PyAudio.

Install dependencies with: python -m pip install -r requirements.txt
Download and extract a Vosk model into ./model, then run this file.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


class VoiceInput:
    """Capture microphone audio and transcribe it locally with Vosk."""

    def __init__(self, model_path: str | Path = "model", sample_rate: int = 16_000,
                 device_index: int | None = None, chunk_size: int = 4_000) -> None:
        self.model_path = Path(model_path)
        self.sample_rate = sample_rate
        self.device_index = device_index
        self.chunk_size = chunk_size
        if sample_rate <= 0 or chunk_size <= 0:
            raise ValueError("sample_rate and chunk_size must be positive.")
        if not self.model_path.is_dir():
            raise FileNotFoundError(
                f"Vosk model directory not found: {self.model_path.resolve()}\n"
                "Download a model from https://alphacephei.com/vosk/models "
                "and extract it into that directory."
            )
        try:
            from vosk import Model, SetLogLevel
        except ImportError as exc:
            raise RuntimeError(
                "Vosk is not installed in this Python environment. "
                "Run: python -m pip install -r requirements.txt"
            ) from exc

        SetLogLevel(-1)
        try:
            self.model = Model(str(self.model_path))
        except Exception as exc:
            raise RuntimeError(
                f"Could not load the Vosk model at {self.model_path.resolve()}. "
                "Check that it was fully extracted and matches your platform."
            ) from exc

    @staticmethod
    def list_input_devices() -> list[dict[str, Any]]:
        """Return available microphone input devices."""
        try:
            import pyaudio
        except ImportError as exc:
            raise RuntimeError(
                "PyAudio is not installed. Run: python -m pip install -r requirements.txt"
            ) from exc
        audio = pyaudio.PyAudio()
        try:
            devices = []
            for index in range(audio.get_device_count()):
                info = audio.get_device_info_by_index(index)
                if info.get("maxInputChannels", 0) > 0:
                    devices.append({
                        "index": index,
                        "name": info.get("name", "Unknown"),
                        "channels": int(info.get("maxInputChannels", 0)),
                        "default_sample_rate": int(info.get("defaultSampleRate", 0)),
                    })
            return devices
        finally:
            audio.terminate()

    def listen(self, timeout: float | None = None) -> None:
        """Continuously print phrases until Ctrl+C or the optional timeout."""
        try:
            import pyaudio
            from vosk import KaldiRecognizer
        except ImportError as exc:
            raise RuntimeError(
                "PyAudio or Vosk is not installed. "
                "Run: python -m pip install -r requirements.txt"
            ) from exc
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be greater than zero or None.")

        audio = pyaudio.PyAudio()
        stream = None
        recognizer = KaldiRecognizer(self.model, float(self.sample_rate))
        started_at = time.monotonic()
        try:
            try:
                stream = audio.open(
                    format=pyaudio.paInt16, channels=1, rate=self.sample_rate,
                    input=True, input_device_index=self.device_index,
                    frames_per_buffer=self.chunk_size,
                )
            except Exception as exc:
                hint = f" (device index {self.device_index})" if self.device_index is not None else ""
                raise RuntimeError(
                    f"Could not open microphone{hint} at {self.sample_rate} Hz. "
                    "Run with --list-devices, check microphone permissions, and "
                    "try a supported sample rate."
                ) from exc

            print("[VoiceInput] Listening... Press Ctrl+C to stop.")
            while timeout is None or time.monotonic() - started_at < timeout:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                except Exception as exc:
                    raise RuntimeError(f"Could not read microphone audio: {exc}") from exc
                if recognizer.AcceptWaveform(data):
                    text = json.loads(recognizer.Result()).get("text", "").strip()
                    if text:
                        print(f"[VoiceInput] Recognized: {text}")
                        continue

            # Preserve speech that did not yet trigger Vosk's endpoint detector.
            text = json.loads(recognizer.FinalResult()).get("text", "").strip()
            if text:
                print(f"[VoiceInput] Recognized: {text}")
            else:
                print("[VoiceInput] No speech recognized.")
            return text
        except KeyboardInterrupt:
            text = json.loads(recognizer.FinalResult()).get("text", "").strip()
            print(f"\n[VoiceInput] Recognized: {text}" if text else "\n[VoiceInput] Listening stopped.")
            return text
        finally:
            if stream is not None:
                try:
                    if stream.is_active():
                        stream.stop_stream()
                finally:
                    stream.close()
            audio.terminate()


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline Vosk microphone transcription.")
    parser.add_argument("--model", default="model", help="Extracted Vosk model directory")
    parser.add_argument("--rate", type=int, default=16_000, help="Microphone sample rate (default: 16000)")
    parser.add_argument("--device", type=int, help="Input device index (default: system default)")
    parser.add_argument("--timeout", type=float, help="Stop listening after this many seconds")
    parser.add_argument("--list-devices", action="store_true", help="List microphone devices and exit")
    args = parser.parse_args()
    try:
        if args.list_devices:
            for d in VoiceInput.list_input_devices():
                print(f"{d['index']}: {d['name']} (inputs: {d['channels']}, default rate: {d['default_sample_rate']} Hz)")
            return 0
        voice = VoiceInput(args.model, args.rate, args.device)
        voice.listen(args.timeout)
        return 0
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())