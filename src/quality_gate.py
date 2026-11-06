"""Pre-upload validation for scripts and generated video files."""
import json
import os
import re
import subprocess


def validate_script_data(script_data, is_short=False):
    """Reject malformed, empty or obviously repetitive LLM output."""
    if not isinstance(script_data, dict):
        raise ValueError("Script response must be a JSON object.")
    title = script_data.get("title")
    scenes = script_data.get("scenes")
    if not isinstance(title, str) or len(title.strip()) < 8:
        raise ValueError("Script title is missing or too short.")
    if not isinstance(scenes, list):
        raise ValueError("Script scenes must be a list.")

    minimum_scenes = 7 if is_short else 24
    maximum_scenes = 12 if is_short else 40
    if not minimum_scenes <= len(scenes) <= maximum_scenes:
        raise ValueError(
            f"Expected {minimum_scenes}-{maximum_scenes} scenes; received {len(scenes)}."
        )

    spoken = []
    visual_prompts = []
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise ValueError(f"Scene {index} is not an object.")
        narration = scene.get("text")
        visual = scene.get("visual_prompt")
        if not isinstance(narration, str) or len(narration.strip()) < 12:
            raise ValueError(f"Scene {index} has missing or trivial narration.")
        if not isinstance(visual, str) or len(visual.strip()) < 12:
            raise ValueError(f"Scene {index} has no useful visual direction.")
        spoken.append(narration.strip())
        visual_prompts.append(visual.strip().lower())

    normalized = [re.sub(r"[^a-z0-9]+", " ", text.lower()).strip() for text in spoken]
    if len(set(normalized)) / len(normalized) < 0.8:
        raise ValueError("Script repeats scene narration; refusing low-value output.")

    words = sum(len(text.split()) for text in spoken)
    if is_short and not 65 <= words <= 190:
        raise ValueError(f"Short script must contain 65-190 spoken words; found {words}.")
    if not is_short and not 850 <= words <= 2200:
        raise ValueError(
            f"Long-form script must contain 850-2200 spoken words; found {words}."
        )

    if len(set(visual_prompts)) / len(visual_prompts) < 0.75:
        raise ValueError("Visual prompts are too repetitive.")
    return {"scenes": len(scenes), "words": words}


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
