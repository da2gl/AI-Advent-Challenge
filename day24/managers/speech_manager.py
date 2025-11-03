"""
Speech Manager for voice input functionality.
Handles audio recording from microphone and transcription via Groq Whisper API.
"""

import os
import tempfile
import wave
import threading
import pyaudio
from typing import Optional
from groq import Groq
from rich.console import Console


class SpeechManager:
    """
    Manages voice input: recording audio from microphone and transcribing
    it to text using Groq Whisper API.
    """

    # Audio recording parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000  # 16kHz is optimal for speech recognition

    def __init__(self, api_key: str, console: Optional[Console] = None):
        """
        Initialize Speech Manager.

        Args:
            api_key: Groq API key for Whisper access
            console: Rich console for output (optional)
        """
        self.api_key = api_key
        self.console = console or Console()
        self.groq_client = Groq(api_key=api_key)
        self._is_recording = False
        self._frames = []

    def record_audio(self) -> Optional[str]:
        """
        Record audio from microphone until Enter is pressed.
        Returns path to temporary WAV file or None if recording failed.

        Returns:
            Path to temporary WAV file with recorded audio, or None on failure
        """
        self._frames = []
        self._is_recording = True

        # Initialize PyAudio
        audio = pyaudio.PyAudio()

        try:
            # Open audio stream
            stream = audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )

            self.console.print(
                "[red]🔴 Recording...[/red] [dim]Press Enter to stop[/dim]"
            )

            # Start recording in separate thread
            def record_thread():
                while self._is_recording:
                    try:
                        data = stream.read(self.CHUNK, exception_on_overflow=False)
                        self._frames.append(data)
                    except Exception as e:
                        self.console.print(f"[red]Recording error: {e}[/red]")
                        break

            thread = threading.Thread(target=record_thread, daemon=True)
            thread.start()

            # Wait for Enter key
            input()
            self._is_recording = False
            thread.join(timeout=1.0)

            # Stop and close stream
            stream.stop_stream()
            stream.close()

            if not self._frames:
                self.console.print("[yellow]No audio recorded[/yellow]")
                return None

            # Save to temporary WAV file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".wav"
            )
            temp_path = temp_file.name
            temp_file.close()

            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(audio.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(self._frames))

            self.console.print("[green]✓ Recording stopped[/green]")
            return temp_path

        except Exception as e:
            self.console.print(f"[red]Error during recording: {e}[/red]")
            return None

        finally:
            audio.terminate()

    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file using Groq Whisper API.

        Args:
            audio_file_path: Path to audio file (WAV format)

        Returns:
            Transcribed text or None if transcription failed
        """
        try:
            self.console.print("[dim]Transcribing audio...[/dim]")

            with open(audio_file_path, "rb") as audio_file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(audio_file_path, audio_file.read()),
                    model="whisper-large-v3",
                    response_format="text",
                    language="en",  # Can be changed or auto-detected
                    temperature=0.0
                )

            # Groq returns text directly when response_format="text"
            transcribed_text = transcription.strip()

            if transcribed_text:
                self.console.print(
                    f"[cyan]📝 Recognized:[/cyan] {transcribed_text}"
                )
                return transcribed_text
            else:
                self.console.print("[yellow]No speech detected[/yellow]")
                return None

        except Exception as e:
            self.console.print(f"[red]Transcription error: {e}[/red]")
            return None

    def record_and_transcribe(self) -> Optional[str]:
        """
        Convenience method: record audio and transcribe it in one call.
        Automatically cleans up temporary audio file.

        Returns:
            Transcribed text or None if failed
        """
        audio_path = None
        try:
            # Record audio
            audio_path = self.record_audio()
            if not audio_path:
                return None

            # Transcribe
            text = self.transcribe_audio(audio_path)
            return text

        finally:
            # Clean up temporary file
            if audio_path and os.path.exists(audio_path):
                try:
                    os.unlink(audio_path)
                except Exception as e:
                    self.console.print(
                        f"[yellow]Warning: Could not delete temp file: {e}[/yellow]"
                    )
