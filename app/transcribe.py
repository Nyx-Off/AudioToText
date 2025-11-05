import os
import uuid
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
            print("pyannote.audio not available")
            return None

        if self.pyannote_pipeline is None:
            try:
                print("Loading speaker diarization pipeline...")

                # Try to load HuggingFace token from multiple sources
                hf_token = None

                # 1. Try from environment variable
                hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')

                # 2. Try from .env file
                if not hf_token:
                    env_file = Path('.env')
                    if env_file.exists():
                        with open(env_file, 'r') as f:
                            for line in f:
                                line = line.strip()
                                if line.startswith('HF_TOKEN=') or line.startswith('HUGGINGFACE_TOKEN='):
                                    hf_token = line.split('=', 1)[1].strip().strip('"').strip("'")
                                    break

                # 3. Try from config file
                if not hf_token:
                    config_file = Path('hf_token.txt')
                    if config_file.exists():
                        with open(config_file, 'r') as f:
                            hf_token = f.read().strip()

                if hf_token:
                    print(f"Using HuggingFace token (length: {len(hf_token)})")
                    self.pyannote_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
                else:
                    print("No HuggingFace token found, trying without authentication...")
                    print("\nTo enable speaker diarization:")
                    print("1. Create a HuggingFace account: https://huggingface.co/join")
                    print("2. Accept model conditions: https://huggingface.co/pyannote/speaker-diarization-3.1")
                    print("3. Get your token: https://huggingface.co/settings/tokens")
                    print("4. Create a file 'hf_token.txt' with your token")
                    print("   OR set environment variable: export HF_TOKEN='your_token_here'\n")

                    # Try without token anyway
                    self.pyannote_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1"
                    )

                # Move to GPU if available
                if torch.cuda.is_available():
                    self.pyannote_pipeline.to(torch.device("cuda"))
                print("Speaker diarization pipeline loaded successfully")
            except Exception as e:
                print(f"Warning: Could not load speaker diarization pipeline: {e}")
                print("\n⚠️  SOLUTION: Pour activer la détection de plusieurs interlocuteurs:")
                print("1. Visitez: https://huggingface.co/join (créer un compte)")
                print("2. Acceptez: https://huggingface.co/pyannote/speaker-diarization-3.1")
                print("3. Token: https://huggingface.co/settings/tokens")
                print("4. Créez le fichier 'hf_token.txt' avec votre token\n")
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
            print("Diarization pipeline not available, skipping...")
            return None

        try:
            print(f"Starting speaker diarization on {audio_path}")

            # Perform diarization directly on the audio file
            print("Running diarization...")
            diarization = pipeline(audio_path)

            # Convert to list of segments
            segments = []
            speaker_map = {}
            speaker_counter = 1

            print("Processing diarization results with pyannote v3.1+ API...")

            # Check if diarization has speaker_diarization attribute (DiarizeOutput)
            if hasattr(diarization, 'speaker_diarization'):
                print("Using DiarizeOutput.speaker_diarization")
                annotation = diarization.speaker_diarization
            else:
                # Fallback: assume diarization is directly an Annotation object
                print("Using Annotation directly")
                annotation = diarization

            # Iterate through the annotation
            # itertracks yields (Segment, track_name, label)
            for turn, _, speaker_label in annotation.itertracks(yield_label=True):
                # Map speaker label to speaker number
                if speaker_label not in speaker_map:
                    speaker_map[speaker_label] = speaker_counter
                    speaker_counter += 1

                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": f"Speaker {speaker_map[speaker_label]}"
                })

            print(f"Diarization complete: found {len(speaker_map)} speakers in {len(segments)} segments")
            return segments

        except Exception as e:
            print(f"Speaker diarization failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def assign_speakers_to_segments(self, whisper_segments: List[Dict], speaker_segments: Optional[List]) -> List[TranscriptionSegment]:
        """Assign speaker labels to Whisper segments based on diarization"""
        if not speaker_segments:
            # No speaker diarization available
            print("No speaker diarization data, assigning all to Speaker 1")
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
            assigned_speaker = "Speaker 1"
            max_overlap = 0

            for speaker_seg in speaker_segments:
                # Calculate overlap
                overlap_start = max(whisper_seg["start"], speaker_seg["start"])
                overlap_end = min(whisper_seg["end"], speaker_seg["end"])
                overlap_duration = max(0, overlap_end - overlap_start)

                if overlap_duration > max_overlap:
                    max_overlap = overlap_duration
                    assigned_speaker = speaker_seg["speaker"]

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

            print(f"\n{'='*60}")
            print(f"Starting transcription for {os.path.basename(file_path)}")
            print(f"Model: {model_size}, Detect speakers: {detect_speakers}")
            print(f"{'='*60}\n")

            # Preprocess audio
            print("Preprocessing audio...")
            processed_audio_path = self.preprocess_audio(file_path)

            try:
                # Transcribe with Whisper
                print("Starting Whisper transcription...")
                whisper_result = self.transcribe_with_whisper(processed_audio_path, model_size, language)
                print(f"Whisper transcription complete: {len(whisper_result['segments'])} segments")

                # Get speaker diarization if requested
                speaker_segments = None
                num_speakers = 1

                if detect_speakers and PYANNOTE_AVAILABLE:
                    print("\nStarting speaker diarization...")
                    speaker_segments = self.diarize_speakers(processed_audio_path)
                    if speaker_segments:
                        # Count unique speakers
                        speakers = set(seg["speaker"] for seg in speaker_segments)
                        num_speakers = len(speakers)
                        print(f"Detected {num_speakers} speaker(s)")
                    else:
                        print("Speaker diarization failed or returned no results")
                else:
                    if detect_speakers:
                        print("Speaker detection requested but pyannote not available")

                # Create transcription segments with speaker labels
                print("\nAssigning speakers to segments...")
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
                        "speaker_diarization": detect_speakers and PYANNOTE_AVAILABLE and speaker_segments is not None
                    },
                    task_id=task_id,
                    created_at=datetime.now()
                )

                print(f"\n{'='*60}")
                print("Transcription complete!")
                print(f"Duration: {audio_duration:.1f}s")
                print(f"Speakers: {num_speakers}")
                print(f"Segments: {len(transcription_segments)}")
                print(f"{'='*60}\n")

                return result

            finally:
                # Clean up temporary files
                if os.path.exists(processed_audio_path):
                    os.unlink(processed_audio_path)

        except Exception as e:
            print(f"\nERROR during transcription: {str(e)}")
            import traceback
            traceback.print_exc()
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
