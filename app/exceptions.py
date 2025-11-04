"""Custom exceptions for AudioToText application"""


class AudioToTextException(Exception):
    """Base exception for AudioToText application"""
    pass


class FileValidationError(AudioToTextException):
    """Raised when file validation fails"""
    pass


class UnsupportedFormatError(FileValidationError):
    """Raised when file format is not supported"""
    pass


class FileSizeError(FileValidationError):
    """Raised when file size exceeds limit"""
    pass


class TranscriptionError(AudioToTextException):
    """Raised when transcription fails"""
    pass


class ModelLoadError(TranscriptionError):
    """Raised when model loading fails"""
    pass


class AudioProcessingError(TranscriptionError):
    """Raised when audio processing fails"""
    pass


class SpeakerDiarizationError(TranscriptionError):
    """Raised when speaker diarization fails"""
    pass


class TaskNotFoundError(AudioToTextException):
    """Raised when task is not found"""
    pass


class TaskTimeoutError(AudioToTextException):
    """Raised when task times out"""
    pass


class ResourceError(AudioToTextException):
    """Raised when system resources are insufficient"""
    pass


class MemoryError(ResourceError):
    """Raised when memory is insufficient"""
    pass


class DiskSpaceError(ResourceError):
    """Raised when disk space is insufficient"""
    pass


class ConfigurationError(AudioToTextException):
    """Raised when configuration is invalid"""
    pass