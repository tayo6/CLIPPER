import os
import subprocess

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


app = FastAPI(
    title="Clipper API",
    version="1.0.1"
)


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")

INPUT_FILE = os.path.join(
    TEMP_DIR,
    "input.mp4"
)

CLIP_FILE = os.path.join(
    TEMP_DIR,
    "clip-from-api.mp4"
)


os.makedirs(TEMP_DIR, exist_ok=True)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Home / health check
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Ad3, new code is running"
    }


# --------------------------------------------------
# Prepare YouTube video
# --------------------------------------------------

@app.post("/api/prepare")
def prepare_video(data: dict):

    video_url = data.get("url")
    start = data.get("start")
    end = data.get("end")

    if not video_url:
        return {
            "success": False,
            "error": "No video URL was provided."
        }

    if start is None or end is None:
        return {
            "success": False,
            "error": "Start and end times are required."
        }

    duration = float(end) - float(start)

    if duration <= 0:
        return {
            "success": False,
            "error": "End time must be greater than start time."
        }

    if duration > 90:
        return {
            "success": False,
            "error": "Clips cannot be longer than 90 seconds."
        }

    return {
        "success": True,
        "message": "Video request received.",
        "url": video_url,
        "start": start,
        "end": end,
        "duration": duration
    }


# --------------------------------------------------
# Trim uploaded video
# --------------------------------------------------

@app.post("/api/trim")
async def trim_video(
    video: UploadFile = File(...),
    start: float = Form(...),
    end: float = Form(...)
):

    duration = end - start

    if duration <= 0:
        return {
            "success": False,
            "error": "End time must be greater than start time."
        }

    if duration > 90:
        return {
            "success": False,
            "error": "Maximum clip length is 90 seconds."
        }

    try:

        # Read the uploaded file ONCE.
        video_data = await video.read()

        if not video_data:
            return {
                "success": False,
                "error": "The uploaded video is empty."
            }

        # Save uploaded video.
        with open(INPUT_FILE, "wb") as file:
            file.write(video_data)

        # Remove an old clip if one exists.
        if os.path.exists(CLIP_FILE):
            os.remove(CLIP_FILE)

        # Create the trimmed clip with FFmpeg.
        command = [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-i",
            INPUT_FILE,
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            CLIP_FILE
        ]

        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )

        return {
            "success": True,
            "message": "Clip created successfully.",
            "file": CLIP_FILE,
            "start": start,
            "end": end,
            "duration": duration
        }

    except subprocess.CalledProcessError as error:

        return {
            "success": False,
            "error": "FFmpeg failed.",
            "details": error.stderr[-1000:]
        }

    except Exception as error:

        return {
            "success": False,
            "error": "An unexpected error occurred.",
            "details": str(error)
        }


# --------------------------------------------------
# Download trimmed clip
# --------------------------------------------------

@app.get("/api/download")
def download_clip():

    if not os.path.exists(CLIP_FILE):
        return {
            "success": False,
            "error": "No trimmed clip is available."
        }

    return FileResponse(
        CLIP_FILE,
        media_type="video/mp4",
        filename="clip.mp4"
    )
