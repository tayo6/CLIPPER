from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Clipper API",
    version="1.0.0"
)

# Allow our frontend to communicate with the backend.
# During development we keep this open.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "status": "online",
        "message": "Clipper backend is running"
    }


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