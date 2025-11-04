import os
import uuid
import asyncio
import aiofiles
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import magic

from app.models import TranscriptionRequest, TaskStatus
from app.transcribe import transcriber
from app.exceptions import (
    FileValidationError,
    UnsupportedFormatError,
    FileSizeError,
    TranscriptionError,
    TaskNotFoundError
)

# Initialize FastAPI app
app = FastAPI(
    title="AudioToText",
    description="Convert audio to text with speaker detection",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global task storage (in production, use Redis or database)
active_tasks: Dict[str, TaskStatus] = {}

# Configuration
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm']

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def validate_audio_file(file: UploadFile) -> bool:
    """Validate uploaded file is a supported audio format"""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_FORMATS:
        return False

    # Check MIME type if possible
    try:
        file_content = file.file.read(1024)
        file.file.seek(0)
        mime_type = magic.from_buffer(file_content, mime=True)

        allowed_mimes = [
            'audio/mpeg', 'audio/wav', 'audio/x-wav',
            'audio/mp4', 'audio/m4a', 'audio/flac',
            'audio/ogg', 'audio/webm'
        ]
        return mime_type in allowed_mimes
    except:
        # If mime detection fails, trust the file extension
        return True


async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file to disk"""
    file_id = str(uuid.uuid4())
    file_ext = Path(upload_file.filename).suffix.lower()
    filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / filename

    async with aiofiles.open(file_path, 'wb') as f:
        content = await upload_file.read()
        await f.write(content)

    return str(file_path)


def cleanup_file(file_path: str):
    """Clean up temporary files"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {e}")


async def process_transcription_task(task_id: str, file_path: str, request: TranscriptionRequest):
    """Background task for processing transcription"""
    try:
        # Update task status to processing
        active_tasks[task_id].status = "processing"
        active_tasks[task_id].progress = 0.1
        active_tasks[task_id].message = "Loading transcription model..."

        # Perform transcription
        result = transcriber.transcribe_audio(
            file_path=file_path,
            detect_speakers=request.detect_speakers,
            model_size=request.model_size,
            language=request.language,
            task_id=task_id
        )

        # Update task status with result
        active_tasks[task_id].status = "completed"
        active_tasks[task_id].progress = 1.0
        active_tasks[task_id].message = "Transcription completed"
        active_tasks[task_id].result = result

        # Save result to file
        output_path = OUTPUT_DIR / f"{task_id}.{request.output_format}"
        formatted_output = transcriber.format_output(result, request.output_format)

        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(formatted_output)

    except Exception as e:
        # Update task status with error
        active_tasks[task_id].status = "failed"
        active_tasks[task_id].error = str(e)
        active_tasks[task_id].message = f"Transcription failed: {str(e)}"

    finally:
        # Clean up uploaded file
        cleanup_file(file_path)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    return FileResponse("templates/index.html")


@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    detect_speakers: bool = Form(True),
    model_size: str = Form("base"),
    language: Optional[str] = Form(None),
    output_format: str = Form("json")
):
    """Upload and process audio file"""

    # Validate file size
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit"
        )

    # Validate file format
    if not validate_audio_file(file):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Create task ID
    task_id = str(uuid.uuid4())

    # Create transcription request
    request = TranscriptionRequest(
        detect_speakers=detect_speakers,
        model_size=model_size,
        language=language,
        output_format=output_format
    )

    # Create task status
    task_status = TaskStatus(
        task_id=task_id,
        status="pending",
        progress=0.0,
        message="File uploaded, starting transcription...",
        created_at=datetime.now()
    )
    active_tasks[task_id] = task_status

    try:
        # Save uploaded file
        file_path = await save_upload_file(file)

        # Start background processing
        background_tasks.add_task(
            process_transcription_task,
            task_id,
            file_path,
            request
        )

        return JSONResponse({
            "success": True,
            "task_id": task_id,
            "message": "File uploaded successfully. Processing started."
        })

    except Exception as e:
        # Clean up on error
        if task_id in active_tasks:
            del active_tasks[task_id]
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get transcription task status"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = active_tasks[task_id]
    return JSONResponse({
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "error": task.error,
        "created_at": task.created_at.isoformat()
    })


@app.get("/result/{task_id}")
async def get_transcription_result(task_id: str, format: str = "json"):
    """Get transcription result"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = active_tasks[task_id]

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")

    if task.result is None:
        raise HTTPException(status_code=404, detail="Result not available")

    # Return result in requested format
    if format == "json":
        # Use mode='json' to properly serialize datetime objects
        return JSONResponse(task.result.model_dump(mode='json'))
    else:
        # Serve file for other formats
        output_path = OUTPUT_DIR / f"{task_id}.{format}"
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Result file not found")

        return FileResponse(
            output_path,
            media_type="text/plain",
            filename=f"transcription.{format}"
        )


@app.get("/download/{task_id}")
async def download_result(task_id: str, format: str = "txt"):
    """Download transcription result as file"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = active_tasks[task_id]

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")

    output_path = OUTPUT_DIR / f"{task_id}.{format}"
    if not output_path.exists():
        # Generate the file on-demand
        formatted_output = transcriber.format_output(task.result, format)
        async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
            await f.write(formatted_output)

    return FileResponse(
        output_path,
        media_type="text/plain",
        filename=f"transcription_{task_id[:8]}.{format}"
    )


@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """Delete task and associated files"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    # Remove task from memory
    del active_tasks[task_id]

    # Clean up associated files
    for format in ["json", "txt", "srt"]:
        output_path = OUTPUT_DIR / f"{task_id}.{format}"
        cleanup_file(str(output_path))

    return JSONResponse({"success": True, "message": "Task deleted successfully"})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len(active_tasks)
    })


@app.get("/models")
async def get_available_models():
    """Get available transcription models"""
    return JSONResponse({
        "whisper_models": ["tiny", "base", "small", "medium"],
        "current_model": "base",
        "speaker_diarization": True
    })


# Cleanup old tasks (run periodically)
async def cleanup_old_tasks():
    """Clean up old completed tasks"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            current_time = datetime.now()

            tasks_to_remove = []
            for task_id, task in active_tasks.items():
                # Remove tasks older than 24 hours
                if (current_time - task.created_at).total_seconds() > 86400:
                    tasks_to_remove.append(task_id)

            for task_id in tasks_to_remove:
                # Delete task and files
                await delete_task(task_id)

        except Exception as e:
            print(f"Error during cleanup: {e}")


# Start cleanup task
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks"""
    asyncio.create_task(cleanup_old_tasks())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
