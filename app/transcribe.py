import os
import uuid
import asyncio
import subprocess
import tempfile
from datetime import datetime
from typing import List, Optional, Dict, Any
import whisper
import torch
import torchaudio
import numpy as np
from pathlib import Path

try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    print("Warning: pyannote.audio not available. Speaker diarization will be disabled.")

from app.models import TranscriptionResult, TranscriptionSegment, TaskStatus


class AudioTranscriber:
    def __init__(self):
        self.whisper_models = {}
        self.pyannote_pipeline = None
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm']

    def load_whisper_model(self, model_size: str = "base"):
        """Load Whisper model if not already loaded"""
        if model_size not in self.whisper_models:
            print(f"Loading Whisper model: {model_size}")
            self.whisper_models[model_size] = whisper.load_model(model_size)
        return self.whisper_models[model_size]

    def load_pyannote_pipeline(self):
        """Load pyannote.audio pipeline for speaker diarization"""
        if not PYANNOTE_AVAILABLE:
            return None

        if self.pyannote_pipeline is None:
            try:
                print("Loading speaker diarization pipeline...")
                # Note: Pour utiliser le modèle, vous pouvez avoir besoin d'un token HuggingFace
                # Obtenez-en un sur https://huggingface.co/pyannote/speaker-diarization
                self.pyannote_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1"
                    # Si vous avez un token HuggingFace, décommentez la ligne suivante :
                    # token="your_huggingface_token_here"
                )
                # Move to GPU if available
                if torch.cuda.is_available():
                    self.pyannote_pipeline.to(torch.device("cuda"))
            except Exception as e:
                print(f"Warning: Could not load speaker diarization pipeline: {e}")
                return None
        return self.pyannote_pipeline

    def preprocess_audio(self, file_path: str) -> str:
        """Convert audio to 16kHz WAV format required by Whisper"""
        try:
            # Create temporary file for processed audio
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_path = temp_file.name
            temp_file.close()

            # Convert audio using ffmpeg
            cmd = [
                'ffmpeg', '-i', file_path,
                '-ar', '16000',  # Sample rate
                '-ac', '1',      # Mono
                '-c:a', 'pcm_s16le',  # 16-bit PCM
                '-y', temp_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"FFmpeg conversion failed: {result.stderr}")

            return temp_path
        except Exception as e:
            raise Exception(f"Audio preprocessing failed: {str(e)}")

    def transcribe_with_whisper(self, audio_path: str, model_size: str = "base", language: Optional[str] = None) -> Dict:
        """Transcribe audio using Whisper"""
        model = self.load_whisper_model(model_size)

        options = {
            "task": "transcribe",
            "fp16": torch.cuda.is_available(),
            "verbose": False
        }

        if language:
            options["language"] = language

        try:
            result = model.transcribe(audio_path, **options)
            return result
        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}")

    def diarize_speakers(self, audio_path: str) -> Optional[List]:
        """Perform speaker diarization using pyannote.audio"""
        pipeline = self.load_pyannote_pipeline()
        if pipeline is None:
            return None

        try:
            # Load audio file using torchaudio
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Resample to 16kHz if needed
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
                sample_rate = 16000

            # Export to temporary wav file for pyannote
            temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_audio_path = temp_audio.name
            temp_audio.close()

            torchaudio.save(temp_audio_path, waveform, sample_rate)

            # Perform diarization
            diarization = pipeline(temp_audio_path)

            # Convert to list of segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": f"Speaker {speaker.split('_')[-1]}"
                })

            # Clean up temporary file
            os.unlink(temp_audio_path)

            return segments

        except Exception as e:
            print(f"Speaker diarization failed: {str(e)}")
            return None

    def assign_speakers_to_segments(self, whisper_segments: List[Dict], speaker_segments: Optional[List]) -> List[TranscriptionSegment]:
        """Assign speaker labels to Whisper segments based on diarization"""
        if not speaker_segments:
            # No speaker diarization available
            return [
                TranscriptionSegment(
                    text=segment["text"].strip(),
                    start_time=segment["start"],
                    end_time=segment["end"],
                    speaker="Speaker 1"
                )
                for segment in whisper_segments
            ]

        transcription_segments = []

        for whisper_seg in whisper_segments:
            # Find which speaker segment this whisper segment belongs to
            assigned_speaker = "Speaker Unknown"

            for speaker_seg in speaker_segments:
                if (whisper_seg["start"] >= speaker_seg["start"] and
                    whisper_seg["end"] <= speaker_seg["end"]):
                    assigned_speaker = speaker_seg["speaker"]
                    break
                # Handle overlapping cases
                elif (whisper_seg["start"] < speaker_seg["end"] and
                      whisper_seg["end"] > speaker_seg["start"]):
                    # If there's overlap, use the speaker with maximum overlap
                    overlap_start = max(whisper_seg["start"], speaker_seg["start"])
                    overlap_end = min(whisper_seg["end"], speaker_seg["end"])
                    if overlap_end > overlap_start:
                        assigned_speaker = speaker_seg["speaker"]
                        break

            transcription_segments.append(
                TranscriptionSegment(
                    text=whisper_seg["text"].strip(),
                    start_time=whisper_seg["start"],
                    end_time=whisper_seg["end"],
                    speaker=assigned_speaker
                )
            )

        return transcription_segments

    def transcribe_audio(self, file_path: str, detect_speakers: bool = True, model_size: str = "base",
                        language: Optional[str] = None, task_id: Optional[str] = None) -> TranscriptionResult:
        """Main transcription function"""
        if task_id is None:
            task_id = str(uuid.uuid4())

        try:
            # Validate file exists and is supported
            if not os.path.exists(file_path):
                raise Exception("Audio file not found")

            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                raise Exception(f"Unsupported file format: {file_ext}")

            # Preprocess audio
            processed_audio_path = self.preprocess_audio(file_path)

            try:
                # Transcribe with Whisper
                whisper_result = self.transcribe_with_whisper(processed_audio_path, model_size, language)

                # Get speaker diarization if requested
                speaker_segments = None
                num_speakers = 1

                if detect_speakers and PYANNOTE_AVAILABLE:
                    speaker_segments = self.diarize_speakers(processed_audio_path)
                    if speaker_segments:
                        # Count unique speakers
                        speakers = set(seg["speaker"] for seg in speaker_segments)
                        num_speakers = len(speakers)

                # Create transcription segments with speaker labels
                transcription_segments = self.assign_speakers_to_segments(
                    whisper_result["segments"], speaker_segments
                )

                # Build full text
                full_text = " ".join([seg.text for seg in transcription_segments])

                # Get audio duration
                audio_duration = whisper_result.get("segments", [])[-1]["end"] if whisper_result.get("segments") else 0

                # Create result
                result = TranscriptionResult(
                    segments=transcription_segments,
                    full_text=full_text,
                    duration=audio_duration,
                    num_speakers=num_speakers,
                    language=whisper_result.get("language"),
                    metadata={
                        "model_size": model_size,
                        "original_file": os.path.basename(file_path),
                        "file_format": file_ext,
                        "speaker_diarization": detect_speakers and PYANNOTE_AVAILABLE
                    },
                    task_id=task_id,
                    created_at=datetime.now()
                )

                return result

            finally:
                # Clean up temporary files
                if os.path.exists(processed_audio_path):
                    os.unlink(processed_audio_path)

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    def format_output(self, result: TranscriptionResult, output_format: str = "json") -> str:
        """Format transcription result in different formats"""
        if output_format == "json":
            return result.model_dump_json(indent=2)

        elif output_format == "txt":
            lines = []
            for segment in result.segments:
                timestamp = f"[{int(segment.start_time//60):02d}:{int(segment.start_time%60):02d}]"
                speaker = f"{segment.speaker}:" if segment.speaker else ""
                lines.append(f"{timestamp} {speaker} {segment.text}")
            return "\n".join(lines)

        elif output_format == "srt":
            # SRT subtitle format
            srt_lines = []
            for i, segment in enumerate(result.segments, 1):
                start_time = self._format_srt_time(segment.start_time)
                end_time = self._format_srt_time(segment.end_time)

                srt_lines.append(str(i))
                srt_lines.append(f"{start_time} --> {end_time}")

                if segment.speaker:
                    srt_lines.append(f"{segment.speaker}: {segment.text}")
                else:
                    srt_lines.append(segment.text)

                srt_lines.append("")  # Empty line between segments

            return "\n".join(srt_lines)

        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _format_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


# Global transcriber instance
transcriber = AudioTranscriber()
