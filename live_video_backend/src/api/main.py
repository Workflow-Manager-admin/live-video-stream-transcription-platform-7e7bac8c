from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable


app = FastAPI(
    title="Live Video Backend API",
    description="Backend for extracting video transcripts and serving video data. Provides endpoints to fetch YouTube video transcripts.",
    version="0.1.1",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health and diagnostics"
        },
        {
            "name": "transcript",
            "description": "Endpoints for transcript extraction from YouTube videos."
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["health"])
def health_check():
    """PUBLIC_INTERFACE
    Simple health check endpoint to verify API status.
    Returns:
        JSON containing a health message.
    """
    return {"message": "Healthy"}


# Response model for transcript extraction
class TranscriptLine(BaseModel):
    text: str = Field(..., description="Transcript line as spoken in the video.")
    start: float = Field(..., description="Start time of the line in seconds.")
    duration: float = Field(..., description="Display duration of the line in seconds.")


class TranscriptResponse(BaseModel):
    video_id: str = Field(..., description="YouTube video id.")
    transcript: List[TranscriptLine] = Field(..., description="List of transcript lines with time offsets.")


# PUBLIC_INTERFACE
@app.get(
    "/extract_transcript",
    response_model=TranscriptResponse,
    summary="Extract transcript from YouTube video",
    description="""
Fetch the transcript from a YouTube video given its URL. Will return an error if a transcript is not available for the video.
""",
    tags=["transcript"],
    responses={
        200: {"description": "Transcript successfully extracted"},
        400: {"description": "Invalid URL or no transcript found"},
        500: {"description": "Internal server error"},
    }
)
def extract_transcript(url: str = Query(..., description="The full YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)")):
    """
    PUBLIC_INTERFACE
    Extracts the transcript for a YouTube video using its URL.

    Parameters:
        url: str - The YouTube video URL

    Returns:
        TranscriptResponse: Structured transcript with time offsets.
    """
    import re

    # Regular expression to get the YouTube video ID
    def _extract_video_id(yt_url: str) -> str:
        # Matches typical YouTube formats
        match = re.match(
            r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w\-]+)",
            yt_url
        )
        if not match:
            return None
        return match.group(1)

    video_id = _extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid or unsupported YouTube URL format.")

    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = [TranscriptLine(**line) for line in transcript_list]
        return TranscriptResponse(video_id=video_id, transcript=transcript)
    except (TranscriptsDisabled, NoTranscriptFound):
        raise HTTPException(status_code=400, detail="Transcript not found or disabled for this video.")
    except VideoUnavailable:
        raise HTTPException(status_code=400, detail="YouTube video not found or is unavailable.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transcript: {str(e)}")

