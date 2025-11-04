from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class TranscriptionSegment(BaseModel):
    text: str
    start_time: float
    end_time: float
    speaker: Optional[str] = None
    confidence: Optional[float] = None


class TranscriptionResult(BaseModel):
    segments: List[TranscriptionSegment]
    full_text: str
    duration: float
    num_speakers: int
    language: Optional[str] = None
    metadata: Dict[str, Any] = {}
    task_id: str
    created_at: datetime


class TranscriptionRequest(BaseModel):
    detect_speakers: bool = True
    model_size: str = "base"  # tiny, base, small, medium
    language: Optional[str] = None
    output_format: str = "json"  # json, txt, srt


class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0
    message: Optional[str] = None
    result: Optional[TranscriptionResult] = None
    error: Optional[str] = None
    created_at: datetime
