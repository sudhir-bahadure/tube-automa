"""Pre-upload validation for generated video files."""
import json
import os
import subprocess


def validate_video(path, is_short=False, min_bytes=10000):
    """Raise ValueError unless the render has valid video and audio streams."""
    if not os.path.isfile(path):
        raise ValueError(f"Video file does not exist: {path}")
    size = os.path.getsize(path)
    if size < min_bytes:
        raise ValueError(f"Video file is unexpectedly small ({size} bytes).")

    command = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,width,height",
        "-of", "json", path,
    ]
    try:
        result = subprocess.run(
            command, check=True, capture_output=True, text=True, timeout=30
        )
        metadata = json.loads(result.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise ValueError(f"ffprobe could not validate the rendered video: {exc}") from exc

    streams = metadata.get("streams", [])
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if not videos:
        raise ValueError("Rendered file has no video stream.")
    if not audios:
        raise ValueError("Rendered file has no audio stream.")

    width, height = videos[0].get("width", 0), videos[0].get("height", 0)
    if not width or not height:
        raise ValueError("Video dimensions are missing.")
    if is_short and height <= width:
        raise ValueError(f"Shorts output must be portrait; found {width}x{height}.")

    try:
        duration = float(metadata["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Video duration is missing or invalid.") from exc
    if duration <= 0:
        raise ValueError("Video duration must be greater than zero.")
    if is_short and duration > 180:
        raise ValueError(f"Shorts output is {duration:.1f}s; maximum is 180s.")

    return {
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "size_bytes": size,
    }
