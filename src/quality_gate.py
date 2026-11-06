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
    if len(title.strip()) > 100:
        raise ValueError("Video title exceeds YouTube's 100-character limit.")
    if not isinstance(scenes, list):
        raise ValueError("Script scenes must be a list.")
    description = script_data.get("description")
    if description is not None and (not isinstance(description, str) or len(description) > 5000):
        raise ValueError("Video description must be text and stay within 5,000 characters.")
    tags = script_data.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or len(tags) > 30:
            raise ValueError("Video tags must be a list of no more than 30 entries.")
        if any(not isinstance(tag, str) or len(tag) > 30 for tag in tags):
            raise ValueError("Each video tag must be text no longer than 30 characters.")

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
        "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
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
    if videos[0].get("codec_name") not in (None, "h264"):
        raise ValueError(f"Video codec must be H.264; found {videos[0].get('codec_name')}.")
    if audios[0].get("codec_name") not in (None, "aac"):
        raise ValueError(f"Audio codec must be AAC; found {audios[0].get('codec_name')}.")

    width, height = videos[0].get("width", 0), videos[0].get("height", 0)
    if not width or not height:
        raise ValueError("Video dimensions are missing.")
    if is_short and (width < 720 or height < 1280):
        raise ValueError(f"Shorts output must be at least 720x1280; found {width}x{height}.")
    if not is_short and (width < 1280 or height < 720):
        raise ValueError(f"Long-form output must be at least 1280x720; found {width}x{height}.")
    if is_short and height <= width:
        raise ValueError(f"Shorts output must be portrait; found {width}x{height}.")
    if not is_short and width <= height:
        raise ValueError(f"Long-form output must be landscape; found {width}x{height}.")

    try:
        duration = float(metadata["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Video duration is missing or invalid.") from exc
    if duration <= 0:
        raise ValueError("Video duration must be greater than zero.")
    if is_short and duration > 180:
        raise ValueError(f"Shorts output is {duration:.1f}s; maximum is 180s.")
    if not is_short and duration < 360:
        raise ValueError(
            f"Long-form output is {duration:.1f}s; minimum quality threshold is 360s."
        )

    return {
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "size_bytes": size,
    }
