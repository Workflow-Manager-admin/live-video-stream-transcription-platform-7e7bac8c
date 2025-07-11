#!/bin/bash
cd /home/kavia/workspace/code-generation/live-video-stream-transcription-platform-7e7bac8c/live_video_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

