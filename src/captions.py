from moviepy.editor import TextClip, CompositeVideoClip
import json
import os

def create_caption_clip(text, start_time, duration, fontsize=70, color='yellow', stroke_color='black', stroke_width=2, method='caption'):
    """Create a single MoviePy TextClip"""
    # Use distinct font if available, else default
    font = "Arial-Bold" 
    
    # Create text clip
    txt_clip = TextClip(
        text, 
        fontsize=fontsize, 
        color=color, 
        font=font, 
        stroke_color=stroke_color, 
        stroke_width=stroke_width,
        method=method,
        size=(1080, None) if method=='caption' else None
    )
    
    txt_clip = txt_clip.set_position(('center', 'center')).set_start(start_time).set_duration(duration)
    return txt_clip

def generate_word_level_captions(audio_metadata, video_duration):
    """
    Generate a list of TextClips from EdgeTTS timestamp metadata.
    audio_metadata: List of dicts (word, start, end) from EdgeTTS or localized logic.
    """
    if not audio_metadata:
        return []
        
    clips = []
    
    # Process each word
    for i, item in enumerate(audio_metadata):
        word = item.get('word', '')
        start = item.get('start', 0)
        end = item.get('end', 0)
        
        # Correction: Ensure end time is valid
        if end <= start:
            if i < len(audio_metadata) - 1:
                end = audio_metadata[i+1]['start']
            else:
                end = start + 0.5 # Default duration
        
        duration = end - start
        
        # Skip empty words or punctuation-only if desired, but keep for rhythm
        if not word.strip():
            continue
            
        # Highlight style (Yellow with black stroke)
        # We can alternate colors or emphasize keywords if we had keyword logic
        color = 'yellow'
        
        # Create clip
        clip = create_caption_clip(
            word, 
            start_time=start, 
            duration=duration,
            fontsize=80 if len(word) < 8 else 60, # Dynamic sizing
            color=color
        )
        clips.append(clip)
        
    return clips
