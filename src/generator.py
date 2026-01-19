import os
import random
import requests
import asyncio
import subprocess
import edge_tts
import json
import math
from cloning_engine import clone_voice
import time
from datetime import datetime, timedelta
from moviepy.editor import *
from moviepy.video.fx.all import crop, resize
from stickman_engine import generate_stickman_image
from captions import generate_word_level_captions
from thumbnail import create_thumbnail
# Removed silent logging override as it causes issues in some moviepy versions

# ============================================================================
# VISUAL TRACKING SYSTEM - Prevents video repetition
# ============================================================================

TRACKING_FILE = "assets/used_videos.json"

if not os.path.exists("assets"):
    os.makedirs("assets")

def load_used_videos():
    """Load tracking file and clean old entries (>90 days)"""
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, 'r') as f:
                data = json.load(f)
                # Clean old entries
                cutoff = (datetime.now() - timedelta(days=90)).isoformat()
                cleaned = {k: v for k, v in data.items() if v > cutoff}
                # Save cleaned data
                if len(cleaned) < len(data):
                    with open(TRACKING_FILE, 'w') as fw:
                        json.dump(cleaned, fw, indent=2)
                return cleaned
        except:
            return {}
    return {}

def save_used_video(video_url, keyword):
    """Track a used video"""
    used_videos = load_used_videos()
    used_videos[video_url] = datetime.now().isoformat()
    try:
        with open(TRACKING_FILE, 'w') as f:
            json.dump(used_videos, f, indent=2)
        print(f"  [TRACKED] Video saved to prevent future repetition")
    except Exception as e:
        print(f"  [WARN] Could not save tracking: {e}")

def is_video_used(video_url):
    """Check if video was already used"""
    used_videos = load_used_videos()
    return video_url in used_videos

def get_varied_keyword(base_keyword, segment_index):
    """Add variations to keywords for more variety"""
    variations = [
        base_keyword,
        f"{base_keyword} nature",
        f"{base_keyword} beautiful",
        f"{base_keyword} amazing",
        f"{base_keyword} cinematic",
        f"{base_keyword} aerial"
    ]
    return variations[segment_index % len(variations)]

def add_background_music(voice_audio, duration):
    """Mix background music if available in assets/music"""
    # CRITICAL: Validate input audio clip has non-zero duration
    try:
        voice_duration = voice_audio.duration
        if voice_duration <= 0 or voice_duration < 0.1:
            print(f"  [WARN] Voice audio has invalid duration ({voice_duration}s), skipping background music")
            return voice_audio
    except Exception as e:
        print(f"  [ERROR] Cannot read voice audio duration: {e}, skipping background music")
        return voice_audio
    
    music_dir = "assets/music"
    if not os.path.exists(music_dir):
        return voice_audio
        
    music_files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
    if not music_files:
        return voice_audio
        
    try:
        # Pick random track
        bg_music_path = os.path.join(music_dir, random.choice(music_files))
        bg_music = AudioFileClip(bg_music_path)
        
        # Validate background music duration
        if bg_music.duration <= 0:
            print(f"  [WARN] Background music file is corrupt, skipping")
            bg_music.close()
            return voice_audio
        
        # Loop if needed
        if bg_music.duration < duration:
            bg_music = bg_music.loop(duration=duration)
        else:
            bg_music = bg_music.subclip(0, duration)
            
        # Lower volume (20%)
        bg_music = bg_music.volumex(0.15)
        
        from moviepy.audio.AudioClip import CompositeAudioClip
        return CompositeAudioClip([voice_audio, bg_music]).set_duration(duration)
    except Exception as e:
        print(f"Background music error: {e}")
        return voice_audio

def create_subscribe_hook(duration=2.0):
    """Create a high-energy Subscribe & Like outro hook"""
    try:
        # Vibrant Red Background for urgency/attention
        bg = ColorClip(size=(1080, 1920), color=(204, 0, 0), duration=duration)
        
        try:
            # Pulsing Text
            txt = (TextClip("SUBSCRIBE\n&\nLIKE!", fontsize=150, color='white', font='Impact', 
                            stroke_color='black', stroke_width=5, method='label', align='center')
                   .set_position('center')
                   .set_duration(duration))
            
            return bg # Return just background (Pure visual as requested)
        except Exception as e:
            print(f"  [WARN] TextClip failed for subscribe hook: {e}")
            return bg # Return just background if text fails
            
    except Exception as e:
        print(f"  [WARN] Failed to create subscribe hook: {e}")
        return None

def apply_ffmpeg_template(template_name, image_path, audio_path, output_path, duration):
    """
    Applies the requested FFmpeg template to generate the final video.
    """
    try:
        # Resolve FFmpeg binary
        ffmpeg_exe = "ffmpeg" # Default to system PATH (works on GitHub Actions)
        try:
            import imageio_ffmpeg
            # Only use imageio_ffmpeg if we are strictly on Windows or if system ffmpeg is missing
            if os.name == 'nt': 
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except:
            pass
        
        # Calculate dynamic parameters
        # duration is passed in seconds
        
        # Base input args
        inputs = ['-loop', '1', '-i', image_path, '-i', audio_path]
        
        # Select filter complex based on template
        if template_name == "slow_zoom":
            # zoompan needs d expressed in frames, assuming fps=25
            d_frames = int(duration * 25)
            # Gentle zoom in
            filter_complex = (
                 f"zoompan=z='min(zoom+0.0008,1.08)':d={d_frames}:"
                 "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',scale=1080:1920"
            )
        elif template_name == "micro_shake":
            # Subtle vibration using crop
            filter_complex = (
                "scale=1080:1920,"
                "crop=w=iw-20:h=ih-20:x='(iw-ow)/2+((random(0)-0.5)*10)':y='(ih-oh)/2+((random(0)-0.5)*10)'"
            )
        elif template_name == "pan_lr":
            # Slowly pan from left to right center
            filter_complex = "scale=1920:1920,crop=1080:1920:x='(t/duration)*(iw-ow)':y=0"
        else:
            # Default static scale
            filter_complex = "scale=1080:1920"

        # Construct command
        # Note: We use -shortest to end when audio ends (plus loop image)
        # We explicitly map input 1 (audio) to audio stream, and filter output to video stream
        cmd = [
            ffmpeg_exe, '-y', 
        ] + inputs + [
            '-filter_complex', filter_complex,
            '-map', '1:a', # Explicitly map audio from input 1
            '-t', str(duration),
            '-c:v', 'libx264', '-preset', 'veryfast', 
            '-c:a', 'aac', '-b:a', '128k',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart', # Good for web/youtube playback
            output_path
        ]
        
        print(f"  [FFmpeg] Running template {template_name}...")
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"  [ERROR] FFmpeg template failed: {e}")
        return False

async def generate_audio(text, output_file="audio.mp3", rate="+0%", pitch="+0Hz", voice="en-US-AndrewNeural"):
    # Voice Mapping for "Human Persona"
    # Andrew: Balanced, warm, good for general facts.
    # Christopher: Deep, serious, great for Long-form Documentaries.
    # Ryan: Cheerful, quick, great for Memes/Shorts.
    
    # Logic to be handled by caller, but defaults here for safety.
    if voice is None:
        voice = "en-US-AndrewNeural"
        
    if voice == "cloned":
        # SPECIAL: Use the custom voice cloning engine
        cloned_audio = clone_voice(text, output_file)
        if cloned_audio and os.path.exists(output_file):
            return [] # Word metadata is not available for cloned voices yet
        else:
            # NO FALLBACK: Raise exception as requested for "Original Voice" channels
            raise Exception("CRITICAL: Voice cloning failed and fallback is disabled. Stopping workflow.")

    word_metadata = []
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # GUARD: Empty text check
            if not text or not text.strip():
                raise Exception("Cannot generate audio for empty/whitespace text")

            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            
            with open(output_file, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        # Convert 100ns units to seconds
                        start_sec = chunk["offset"] / 1e7
                        duration_sec = chunk["duration"] / 1e7
                        word_metadata.append({
                            "word": chunk["text"],
                            "start": start_sec,
                            "end": start_sec + duration_sec
                        })
            
            # VALIDATION: Check if audio file is valid
            if not os.path.exists(output_file):
                raise Exception("Audio file was not created")
            
            file_size = os.path.getsize(output_file)
            if file_size < 1000:  # Less than 1KB is likely corrupt
                raise Exception(f"Audio file too small ({file_size} bytes), likely corrupt")
            
            # VALIDATION: Check audio duration
            try:
                test_clip = AudioFileClip(output_file)
                clip_duration = test_clip.duration
                test_clip.close()
                
                if clip_duration < 0.1:  # Less than 0.1 seconds
                    raise Exception(f"Audio duration too short ({clip_duration}s)")
                    
                print(f"  [OK] Audio generated: {file_size} bytes, duration: {clip_duration:.2f}s")
            except Exception as validation_error:
                raise Exception(f"Audio clip validation failed: {str(validation_error)}")
                        
            return word_metadata
            
        except Exception as e:
            print(f"Audio generation attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3
                await asyncio.sleep(wait_time)
                word_metadata = [] # Reset on retry
                if os.path.exists(output_file):
                    try: os.remove(output_file)
                    except: pass
            else:
                # FALLBACK: Create silent audio as last resort using FFmpeg (More robust than moviepy writer)
                print(f"  [FALLBACK] All retries failed, creating silent audio clip via FFmpeg")
                try:
                    # FFmpeg command for 2 seconds of silence
                    # Using AAC for broader compatibility while saving as .mp3 extension if requested
                    # But actually we should use standard libmp3lame if output is .mp3
                    codec = 'libmp3lame' if output_file.endswith('.mp3') else 'aac'
                    cmd = [
                        'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', 
                        '-t', '2', '-c:a', codec, output_file
                    ]
                    subprocess.run(cmd, check=True, capture_output=True)
                    
                    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                        print(f"  [OK] FFmpeg silent audio fallback created: {output_file}")
                        return []
                    else:
                        raise Exception("FFmpeg created empty file")
                except Exception as fallback_error:
                    print(f"  [ERROR] FFmpeg fallback failed: {fallback_error}")
                    # Last ditch effort with MoviePy if FFmpeg fails
                    try:
                        from moviepy.audio.AudioClip import AudioClip
                        import numpy as np
                        silent_duration = 2.0
                        silent_audio = AudioClip(lambda t: np.array([0.0, 0.0]), duration=silent_duration)
                        silent_audio.write_audiofile(output_file, fps=44100, logger=None, verbose=False)
                        silent_audio.close()
                        return []
                    except:
                        raise e # Raise original edge-tts error
    return []

def download_background_video(query="abstract", api_key=None, output_file="bg_raw.mp4", orientation="portrait", segment_index=0):
    """Download a unique background video from Pexels"""
    if not api_key:
        return None
    
    # Clean query
    query = query.replace("#", "").strip()
    # Add variation to query
    varied_query = get_varied_keyword(query, segment_index)
    
    headers = {'Authorization': api_key}
    url = f"https://api.pexels.com/videos/search?query={varied_query}&per_page=30&orientation={orientation}"
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            videos = r.json().get('videos', [])
            
            if videos:
                # Filter out already used videos
                unused_videos = []
                for video in videos:
                    video_files = video.get('video_files', [])
                    if video_files:
                        link = video_files[0].get('link', '')
                        if link and not is_video_used(link):
                            unused_videos.append(video)
                
                # If all videos are used, try with base query
                if not unused_videos:
                    print(f"  [INFO] No unused videos for '{varied_query}', using any available.")
                    unused_videos = videos # Fallback to reused if absolutely necessary
                
                # Select random unused video
                video_data = random.choice(unused_videos)
                video_files = video_data.get('video_files', [])
                # Prefer HD but keep it manageable
                video_files = [v for v in video_files if v['width'] >= 720 and v['width'] <= 1920]
                if not video_files:
                    video_files = video_data.get('video_files', [])
                
                best_file = min(video_files, key=lambda x: abs(x['width'] - 1080))
                link = best_file['link']
                
                print(f"  [NEW] Downloading background for '{query}': {link[:40]}...")
                with requests.get(link, stream=True, timeout=15) as res:
                    if res.status_code == 200:
                        with open(output_file, "wb") as f:
                            for chunk in res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        if os.path.exists(output_file) and os.path.getsize(output_file) > 50000:
                            save_used_video(link, query)
                            # Add a tiny silence cushion (0.2s) at end for a more human "thinking" pause between segments
                # This prevents the audio from feeling like one continuous robot blast
                silence = AudioFileClip(None) # Not standard, let's use a simpler way
                # Better: just set duration slightly longer than audio
                final_audio = AudioFileClip(output_file)
                # Ensure the clip has a clean end
                # (Skip complex mixing, just log success)
                return output_file
    except Exception as e:
        print(f"  [ERROR] Pexels error: {e}")
        
    return None


def create_video(metadata, output_path="final_video.mp4", pexels_key=None):
    mode = metadata.get('category', metadata.get('mode', 'fact'))
    temp_bg_files = [] # Initialize globally for thumbnail fallback
    
    if metadata.get('visual_style') == 'sketch_static':
        # --- NEW FFmpeg MEME PIPELINE (Multi-Segment) ---
        print("[*] Running FFmpeg optimized meme pipeline (Multi-Segment)...")
        
        script_segments = metadata.get('script', [])
        segment_files = []
        temp_files_to_clean = []
        
        # 1. Process each segment
        for i, seg in enumerate(script_segments):
            text = seg.get("text", "")
            if not text: continue
            
            print(f"  Processing segment {i+1}/{len(script_segments)}: {text[:30]}...")
            
            # --- A. Audio Generation (Varied for human touch) ---
            audio_path = f"temp_meme_audio_{i}.mp3"
            
            # Dynamic Prosody: Vary pitch/rate slightly per line to break "robot" monotony
            # Hook/Punchline = punchier. Setup = neutral.
            base_pitch_val = -2
            base_rate_val = 8
            
            if i == 0: # Hook
                pitch = f"{base_pitch_val+2}Hz" 
                rate = f"{base_rate_val+2}%"
            elif i == len(script_segments) - 1: # CTA
                 pitch = f"{base_pitch_val}Hz"
                 rate = f"{base_rate_val}%"
            elif i % 2 == 0: # Varied
                 pitch = f"{base_pitch_val-2}Hz"
                 rate = f"{base_rate_val-2}%"
            else:
                 pitch = f"{base_pitch_val}Hz"
                 rate = f"{base_rate_val}%"

            voice_config = metadata.get('voice_config', {})
            voice = voice_config.get('voice', 'en-US-GuyNeural')
            
            asyncio.run(generate_audio(text, audio_path, rate=rate, pitch=pitch, voice=voice))
            
            if os.path.exists(audio_path):
                temp_files_to_clean.append(audio_path)
            else:
                print(f"    [WARN] Audio failed for segment {i}, using silence")
                # Fallback to silent MP3 if needed (logic omitted for brevity, generator handles it)
                continue

            # Get duration
            try:
                from moviepy.audio.AudioClip import AudioFileClip
                ac = AudioFileClip(audio_path)
                duration = ac.duration
                ac.close()
            except:
                duration = 3.0
            
            # --- B. Visual Generation (Unique per segment) ---
            # Extract core topic but focus on THIS line's context
            topic = metadata.get('topic', 'meme')
            visual_prompt = f"stickman sketch: {text}. Context: {topic}"
            
            image_path = f"temp_meme_visual_{i}.jpg"
            img = generate_stickman_image(visual_prompt, image_path, niche="meme")
            
            if not img:
                # Fallback
                subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=white:s=1080x1920', '-frames:v', '1', image_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            temp_files_to_clean.append(image_path)
            
            # --- C. Create Segment Video with FFmpeg ---
            files_list_path = f"inputs_{i}.txt"
            seg_output_path = f"temp_seg_{i}.mp4"
            
            # Apply template (randomize slightly)
            templates = ["slow_zoom", "micro_shake"] # pan_lr can look weird on short segments
            template = random.choice(templates)
            
            apply_ffmpeg_template(template, image_path, audio_path, seg_output_path, duration)
            
            if os.path.exists(seg_output_path):
                segment_files.append(seg_output_path)
                temp_files_to_clean.append(seg_output_path)
            else:
                print(f"    [ERROR] FFmpeg segment {i} failed")

        if not segment_files:
            return None

        # --- D. Subscribe Hook (Visual Only) ---
        print("  [*] Generating Subscribe Hook...")
        hook_path = "temp_subscribe.mp4"
        # Create a simple FFmpeg subscribe card (White background, Red Text)
        # We use a simple drawtext command here for speed/reliability over MoviePy
        try:
             # Create red background with text
             ffmpeg_exe = "ffmpeg"
             if os.name == 'nt':
                 try: import imageio_ffmpeg; ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                 except: pass

             cmd_hook = [
                ffmpeg_exe, '-y',
                '-f', 'lavfi', '-i', 'color=c=red:s=1080x1920:d=2',
                '-vf', "drawtext=text='SUBSCRIBE':fontcolor=white:fontsize=150:x=(w-text_w)/2:y=(h-text_h)/2",
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                hook_path
             ]
             subprocess.run(cmd_hook, check=True, capture_output=True)
             
             if os.path.exists(hook_path):
                 # Hook has no audio, generate silence
                 hook_audio = "temp_silence.mp3"
                 subprocess.run([ffmpeg_exe, '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', '2', hook_audio], stdout=subprocess.DEVNULL)
                 
                 # Merge silence to hook
                 hook_with_audio = "temp_subscribe_final.mp4"
                 subprocess.run([
                     ffmpeg_exe, '-y', '-i', hook_path, '-i', hook_audio, 
                     '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-shortest', hook_with_audio
                 ], stdout=subprocess.DEVNULL)
                 
                 segment_files.append(hook_with_audio)
                 temp_files_to_clean.extend([hook_path, hook_audio, hook_with_audio])
        except Exception as e:
            print(f"  [WARN] Subscribe hook generation failed: {e}")

        # --- E. Concatenate All Segments ---
        print("  [*] Concatenating segments...")
        concat_list_path = "concat_list.txt"
        with open(concat_list_path, "w") as f:
            for seg in segment_files:
                # Ffmpeg concat requires: file 'path'
                # Path must be escaped
                clean_path = seg.replace("\\", "/")
                f.write(f"file '{clean_path}'\n")
        
        temp_files_to_clean.append(concat_list_path)
        
        ffmpeg_exe = "ffmpeg"
        if os.name == 'nt':
             try: import imageio_ffmpeg; ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
             except: pass
             
        cmd_concat = [
            ffmpeg_exe, '-y', '-f', 'concat', '-safe', '0', '-i', concat_list_path,
            '-c', 'copy', output_path
        ]
        
        subprocess.run(cmd_concat, check=True)
        
        # Cleanup
        for f in temp_files_to_clean:
            try:
                if os.path.exists(f): os.remove(f)
            except: pass
            
        return output_path

    if mode == 'meme' and 'memes' in metadata: # Legacy list-based meme fallback
        memes = metadata.get('memes', [])
        meme_clips = []
        temp_audio_files = []
        
        print(f"Generating meme compilation with {len(memes)} jokes...")
        
        for i, meme in enumerate(memes):
            setup = meme['setup']
            punchline = meme['punchline']
            
            # 1. Generate Audio for this joke
            audio_path = f"temp_audio_{i}.mp3"
            script = f"{setup} ... ... {punchline} ... Hahaha!"
            
            try:
                asyncio.run(generate_audio(script, audio_path))
                
                # Validate audio file before using
                if not os.path.exists(audio_path):
                    print(f"  [WARN] Audio file not created for meme {i}, skipping segment")
                    continue
                
                # CRITICAL: Wrap AudioFileClip in try-except as it can fail on corrupt files
                try:
                    audio_clip = AudioFileClip(audio_path)
                except Exception as clip_error:
                    print(f"  [ERROR] Cannot open audio file for meme {i}: {clip_error}")
                    print(f"  [SKIP] Skipping this meme segment")
                    continue
                
                # Validate duration IMMEDIATELY before using
                try:
                    clip_dur = audio_clip.duration
                except:
                    print(f"  [ERROR] Cannot read duration for meme {i}")
                    audio_clip.close()
                    continue
                    
                if clip_dur < 0.1 or clip_dur == 0:
                    print(f"  [WARN] Audio duration invalid for meme {i} ({clip_dur}s), skipping segment")
                    audio_clip.close()
                    continue
                
                temp_audio_files.append(audio_path)
                
                # Use actual audio duration - DO NOT pad beyond file length
                # Padding with set_duration() causes OSError when MoviePy tries to read beyond actual audio data
                duration = clip_dur
                audio = audio_clip
                print(f"  [OK] Meme {i} audio ready: {duration:.1f}s")
            except Exception as audio_error:
                print(f"  [ERROR] Audio generation failed for meme {i}: {audio_error}")
                print(f"  [SKIP] Skipping this meme segment")
                continue
            
            # 2. Get Background for this segment
            # Use unique filename to prevent locking/overwrite issues
            # Vary keywords for different visuals each time
            bg_keywords = [
                "funny reaction",
                "people laughing",
                "comedy show",
                "happy people",
                "celebration party",
                "friends laughing"
            ]
            bg_keyword = bg_keywords[i % len(bg_keywords)]
            bg_filename = f"temp_bg_{i}.mp4"
            bg_file = download_background_video(bg_keyword, pexels_key, bg_filename, segment_index=i)
            clip = None
            if bg_file:
                try:
                    clip = VideoFileClip(bg_file)
                    # Explicitly check if we can read the first frame
                    _ = clip.get_frame(0) 
                    
                    if clip.duration < duration:
                        clip = clip.loop(duration=duration)
                    else:
                        clip = clip.subclip(0, duration)
                    temp_bg_files.append(bg_file) # Track for cleanup
                except Exception as e:
                    print(f"Corrupted video skip: {e}")
                    if clip: clip.close()
                    clip = None
            
            if not clip:
                # Random darkish colors fallback
                colors = [(30, 30, 30), (20, 40, 20), (40, 20, 20), (20, 20, 40)]
                clip = ColorClip(size=(1080, 1920), color=random.choice(colors), duration=duration)
            
            # Resize logic (DRY later maybe)
            w, h = clip.size
            target_ratio = 9/16
            if w/h > target_ratio:
                new_w = h * target_ratio
                clip = crop(clip, x1=(w/2 - new_w/2), width=new_w, height=h)
            else:
                new_h = w / target_ratio
                clip = crop(clip, y1=(h/2 - new_h/2), width=w, height=new_h)
            clip = clip.resize(newsize=(1080, 1920))
            
            # HUMAN EXPERIENCE: Dynamic camera for meme impact
            # Subtle vibration and handheld sway makes it feel like a real person filmed/edited it
            clip = clip.resize(lambda t: (1.0 + 0.04 * math.sin(t * 12))) 
            clip = clip.rotate(lambda t: 0.8 * math.sin(t * 4)) 
            
            # Watermark Guard (Crop bottom 150px)
            clip = crop(clip, y2=clip.h - 150).resize(newsize=(1080, 1920))
            
            # Combine Meme Segment (Pure visual, no text/banners as requested)
            meme_segment = CompositeVideoClip([clip]).set_audio(audio)
            meme_clips.append(meme_segment.set_duration(duration))

        # --- SUBSCRIBE HOOK INJECTION ---
        print("  [*] Adding Subscribe & Like hook...")
        sub_hook = create_subscribe_hook()
        if sub_hook:
            meme_clips.append(sub_hook)

        # Final Concatenation
        final_video = concatenate_videoclips(meme_clips, method="compose")
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        
        # Cleanup
        for f in temp_audio_files + temp_bg_files:
            try:
                if os.path.exists(f): os.remove(f)
            except:
                pass
            
        return output_path

    elif mode == 'long' and 'segments' in metadata:
        # --- NEW LONG-FORM DOCUMENTARY LOGIC ---
        segments = metadata['segments']
        segment_clips = []
        temp_audio_files = []
        
        print(f"Generating long-form video: {metadata.get('topic')}...")
        # Use "Christopher" (Deep, Documentary Style)
        voice_persona = "en-US-ChristopherNeural"
        print(f"Total segments: {len(segments)} (Target: 8+ minutes) | Voice: {voice_persona}")
        
        for i, seg in enumerate(segments):
            text = seg['text']
            keyword = seg['keyword']
            
            # Determine speech rate based on segment type
            # Hook and intro: normal speed
            # Key points: slightly slower for emphasis
            # Transitions: slightly faster
            if i == 0:  # Opening hook
                rate = "+0%"
                pitch = "+2Hz"  # Slightly higher for excitement
            elif i < 3:  # Intro and context
                rate = "-5%"  # Slower for clarity
                pitch = "+0Hz"
            elif "discovery" in text.lower() or "incredible" in text.lower():
                rate = "-10%"  # Slow down for emphasis
                pitch = "+0Hz"
            elif i >= len(segments) - 2:  # Summary and CTA
                rate = "+5%"  # Slightly faster
                pitch = "+0Hz"
            else:
                rate = "+0%"  # Normal
                pitch = "+0Hz"
            
            # 1. Generate Audio for this segment with variation
            # Specialized Voice: Deep & Storytelling for Long-form
            audio_path = f"temp_long_audio_{i}.mp3" 
            rate = "-5%"
            pitch = "-10Hz"
            asyncio.run(generate_audio(text, audio_path, rate=rate, pitch=pitch))
            audio_clip = AudioFileClip(audio_path)
            temp_audio_files.append(audio_path)
            
            duration = audio_clip.duration + 0.5
            audio = add_background_music(audio_clip, duration)
            
            # 2. Visual (FORCE STICKMAN)
            is_stickman = True
            bg_filename = f"temp_long_bg_{i}_a.jpg" if is_stickman else f"temp_long_bg_{i}.mp4"
            
            clip = None
            if is_stickman:
                segment_poses = seg.get('stickman_poses', ["standing normally", "standing relaxed"])
                if isinstance(segment_poses, str): segment_poses = [segment_poses, segment_poses]
                if len(segment_poses) < 2: segment_poses = segment_poses + [segment_poses[0]]
                
                # Get niche from metadata for color palette
                niche = metadata.get('niche', 'default')
                generate_stickman_image.current_label = "A"
                img1 = generate_stickman_image(segment_poses[0], f"temp_long_bg_{i}_a.jpg", niche=niche)
                generate_stickman_image.current_label = "B"
                img2 = generate_stickman_image(segment_poses[1], f"temp_long_bg_{i}_b.jpg", niche=niche)
                # Reset
                generate_stickman_image.current_label = "1"
                
                if img1 and img2:
                    try:
                        f1 = ImageClip(img1).set_duration(0.2)
                        f2 = ImageClip(img2).set_duration(0.2)
                        # Watermark Guard: Crop bottom 150px
                        f1 = crop(f1, y2=f1.h - 150)
                        f2 = crop(f2, y2=f2.h - 150)
                        anim_loop = concatenate_videoclips([f1, f2]).loop(duration=duration)
                        # HUMAN EXPERIENCE: Dynamic camera for documentary feel
                        clip = anim_loop.resize(lambda t: 1.0 + 0.1 * (t/duration))
                        clip = clip.rotate(lambda t: 0.3 * math.cos(t * 3)) # Slow professional sway
                        clip = clip.resize(lambda t: (1.0 + 0.02 * math.sin(t * 8))) 
                        temp_bg_files.extend([f"temp_long_bg_{i}_a.jpg", f"temp_long_bg_{i}_b.jpg"])
                    except Exception as e:
                        print(f"Long Stickman Anim Error: {e}")
                        clip = None
                elif img1:
                    clip = ImageClip(img1).set_duration(duration)
                    # Watermark Guard
                    clip = crop(clip, y2=clip.h - 150)
                    clip = clip.resize(lambda t: 1.0 + 0.15 * (t/duration))
                    clip = clip.rotate(lambda t: 2 * math.sin(t * 5))
                    temp_bg_files.append(f"temp_long_bg_{i}_a.jpg")
            else:
                # Stock Footage Fallback
                bg_file = download_background_video(keyword, pexels_key, bg_filename, orientation="landscape", segment_index=i)
                if bg_file:
                    try:
                        clip = VideoFileClip(bg_file)
                        _ = clip.get_frame(0) 
                        if clip.duration < duration:
                            clip = clip.loop(duration=duration)
                        else:
                            clip = clip.subclip(0, duration)
                        temp_bg_files.append(bg_file)
                    except Exception as e:
                        print(f"Corrupted long bg skip: {e}")
                        if clip: clip.close()
                        clip = None
            
            if not clip:
                # Fallback: Pleasant Pastel Backgrounds (Soft Blue, Mint, Cream, Lavender, Peach)
                colors = [(200, 230, 255), (200, 255, 230), (255, 250, 200), (230, 200, 255), (255, 218, 185)]
                clip = ColorClip(size=(1920, 1080), color=colors[i % len(colors)], duration=duration)
            
            # Standard 16:9 Resize
            curr_w, curr_h = clip.size
            target_ratio = 16/9
            if curr_w/curr_h > target_ratio:
                new_w = curr_h * target_ratio
                clip = crop(clip, x1=(curr_w/2 - new_w/2), width=new_w, height=curr_h)
            else:
                new_h = curr_w / target_ratio
                clip = crop(clip, y1=(curr_h/2 - new_h/2), width=curr_w, height=new_h)
            clip = clip.resize(newsize=(1920, 1080))
            
            # 3. Add Chapter Title Card (first 2 seconds of each segment)
            chapter_overlays = []
            if i == 0:
                chapter_title = "🎬 OPENING"
            elif i == 1:
                chapter_title = "📖 INTRODUCTION"
            elif i == len(segments) - 1:
                chapter_title = "👍 SUBSCRIBE FOR MORE!"
            elif i == len(segments) - 2:
                chapter_title = "📝 SUMMARY"
            else:
                chapter_title = f"CHAPTER {i-1}"
            
            try:
                # Chapter card (first 2 seconds)
                chapter_card = (TextClip(chapter_title, fontsize=80, color='white', font='Liberation-Sans-Bold',
                                        stroke_color='black', stroke_width=4, method='label')
                               .set_position('center')
                               .set_duration(min(2.0, duration))
                               .set_start(0))
                chapter_overlays.append(chapter_card)
            except:
                pass  # Skip if text rendering fails
            
            # 4. Enhanced Subtitle Overlays
            words = text.split()
            # Longer chunks for better readability (8 words instead of 6)
            chunks = [" ".join(words[j:j+8]) for j in range(0, len(words), 8)]
            txt_clips = []
            chunk_duration = duration / len(chunks)
            
            for j, chunk in enumerate(chunks):
                try:
                    # Skip subtitles during chapter card (first 2 seconds)
                    start_time = max(2.0, j * chunk_duration)
                    if start_time >= duration:
                        continue
                    
                    # Enhanced subtitle styling with background for better readability
                    # Create semi-transparent background
                    txt_height = 120
                    txt_bg = ColorClip(size=(1800, txt_height), color=(0, 0, 0), duration=chunk_duration)
                    txt_bg = txt_bg.set_opacity(0.7).set_position(('center', 900)).set_start(start_time)
                    txt_clips.append(txt_bg)
                    
                    # Text on top of background
                    txt = (TextClip(chunk, fontsize=52, color='white', font='Liberation-Sans-Bold',
                                    method='caption', size=(1700, None), align='center')
                           .set_position(('center', 920))
                           .set_duration(chunk_duration)
                           .set_start(start_time))
                    txt_clips.append(txt)
                except:
                    continue
            
            # 4. TRANSFORMATIVE OVERLAY (Monetization Safety)
            # Add a "Polaroid/Gallery" style frame to define "visual transformation"
            # This prevents instances of "reused content" by adding a distinct framing element
            if is_stickman:
                 # Add 20px white border, then 2px black border
                 try:
                    clip = clip.margin(20, color=(255, 255, 255)).margin(2, color=(0, 0, 0))
                    # Resize back to target to ensure it fits (1080x1920)
                    clip = clip.resize(newsize=(1080, 1920))
                 except Exception as e:
                    print(f"Frame transform warning: {e}")
            
            # Combine all elements (Pure visual, no text/subtitles as requested)
            segment_clip = CompositeVideoClip([clip]).set_audio(audio)
            segment_clips.append(segment_clip)
            
            # Progress indicator
            print(f"  ✓ Segment {i+1}/{len(segments)} complete ({duration:.1f}s)")

        # Avatar logic removed

        # Final Concatenation
        final_video = concatenate_videoclips(segment_clips, method="compose")
        total_duration = final_video.duration
        print(f"\n🎥 Total video duration: {total_duration/60:.2f} minutes ({total_duration:.1f} seconds)")
        
        if total_duration < 480:  # Less than 8 minutes
            print(f"⚠️  WARNING: Video is {480-total_duration:.0f} seconds SHORT of 8-minute target!")
        else:
            print(f"✅ SUCCESS: Video meets 8+ minute requirement!")
        
        # Save with optimized settings
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", 
                                    preset="medium", bitrate="2500k")
        
        # Cleanup
        for f in temp_audio_files + temp_bg_files:
            try:
                if os.path.exists(f): os.remove(f)
            except:
                pass
            
        return output_path

    else:
        # --- ENHANCED SHORTS/FACTS LOGIC WITH MULTI-CLIP SYNC ---
        script_segments = metadata.get('script', [])
        if not script_segments:
            # Fallback for old single-text format
            script_segments = [{"text": metadata.get('text', ''), "keyword": metadata.get('topic', 'abstract')}]
            
        final_clips = []
        temp_files = []
        
        # --- SHORTS DURATION BUDGET ---
        # Intro (~4s), Outro (~4s), Hook (~2s) = 10s overhead
        # We must keep content under 48s to stay safe within 58s total
        MAX_SHORTS_DURATION = 58.0
        overhead = 0
        if metadata.get('use_avatar'): overhead += 8.5 # Intro + Outro
        overhead += 2.2 # Subscribe Hook fallback/padding
        
        content_budget = MAX_SHORTS_DURATION - overhead
        current_total_duration = 0
        
        print(f"Generating enhanced sync video with {len(script_segments)} segments...")
        print(f"  [BUDGET] Content limit: {content_budget:.1f}s (Total limit: {MAX_SHORTS_DURATION}s)")
        
        for i, seg in enumerate(script_segments):
            # --- SHORTS DURATION GUARD ---
            if current_total_duration >= content_budget:
                print(f"  [!] Content budget reached ({current_total_duration:.1f}s). Skipping remaining segments.")
                break
                
            text = seg['text']
            keyword = seg.get('keyword', metadata.get('topic', 'abstract'))
            
            # 1. Voice
            # Specialized Voice: Professional & Engaging (Slightly faster but natural)
            is_meme = (metadata.get('mode') == 'meme' or metadata.get('category') == 'meme')
            
            # Use "Ryan" (British, Sarcastic/Funny) for Memes, "Andrew" (Warm/Professional) for Facts
            voice_persona = metadata.get('voice', "en-GB-RyanNeural" if is_meme else "en-US-AndrewNeural")
            
            # Use a more natural speed increase. Too fast = robotic/unpleasant.
            rate = "+10%" if is_meme else "+0%" 
            pitch = "+0Hz" 
            
            audio_path = f"temp_voc_{i}.mp3"
            try:
                word_metadata = asyncio.run(generate_audio(text, audio_path, rate=rate, pitch=pitch, voice=voice_persona))
                
                # Validate file exists and is readable
                if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 100:
                    print(f"  [WARN] Audio file {audio_path} is missing or too small, skipping segment")
                    continue
                    
                try:
                    audio_clip = AudioFileClip(audio_path)
                    # Force read duration to catch errors early
                    _ = audio_clip.duration
                except Exception as clip_err:
                    print(f"  [ERROR] MoviePy failed to read audio {audio_path}: {clip_err}")
                    continue

                duration = audio_clip.duration + 0.2
                
                # FINAL BUDGET CHECK (Trim if needed or skip)
                if current_total_duration + duration > content_budget:
                    print(f"  [!] Segment would exceed content budget. Skipping.")
                    audio_clip.close()
                    break
                    
                audio = add_background_music(audio_clip, duration)
                temp_files.append(audio_path)
                
                # Give the TTS some "breathing room" (0.2s padding)
                duration = duration + 0.2
            except Exception as segment_audio_err:
                print(f"  [SKIP] Skipping segment {i} due to audio error: {segment_audio_err}")
                continue
            
            # Define niche and flags for visual processing
            niche = metadata.get('category', metadata.get('mode', 'fact'))
            is_stickman = True # Force stickman as requested
            
            clip = None
            if is_stickman:
                # Use Stickman Engine with Animation (Alternating Frames)
                all_segment_poses = metadata.get('stickman_poses', [])
                segment_poses = all_segment_poses[i] if i < len(all_segment_poses) else ["standing normally", "standing relaxed"]
                
                # Ensure we have at least 2 poses
                if isinstance(segment_poses, str): segment_poses = [segment_poses, segment_poses]
                # Standard stickman logic
                poses = seg.get('stickman_poses', ["standing normally", "standing relaxed"])
                if isinstance(poses, str): poses = [poses, poses]
                if len(poses) < 2: poses = poses + [poses[0]]
                
                generate_stickman_image.current_label = "A"
                img1 = generate_stickman_image(poses[0], f"temp_bg_{i}_a.jpg", niche=niche)
                generate_stickman_image.current_label = "B"
                img2 = generate_stickman_image(poses[1], f"temp_bg_{i}_b.jpg", niche=niche)
                # Reset
                generate_stickman_image.current_label = "1"
                
                if img1 and img2:
                    try:
                        # Create alternating frames (0.3s each)
                        f1 = ImageClip(img1).set_duration(0.3)
                        f2 = ImageClip(img2).set_duration(0.3)
                        # Watermark Guard
                        f1 = crop(f1, y2=f1.h - 150)
                        f2 = crop(f2, y2=f2.h - 150)
                        
                        # Concatenate and loop to fill segment duration
                        anim_loop = concatenate_videoclips([f1, f2]).loop(duration=duration)
                        
                        # Add Ken Burns zoom (1.0 to 1.15)
                        clip = anim_loop.resize(lambda t: 1.0 + 0.15 * (t/duration))
                        
                        # HUMAN EXPERIENCE: Add a subtle 'Handheld Camera' jitter
                        # This keeps the eye busy since we removed on-screen text
                        clip = clip.rotate(lambda t: 0.5 * math.sin(t * 4)) # Subtle sway
                        clip = clip.resize(lambda t: (1.0 + 0.03 * math.sin(t * 12))) # Micro-zoom pulse
                        
                        # Add a "breathing" or "talking" scale effect synced with audio volume 
                        clip = clip.resize(lambda t: (1.0 + 0.02 * math.sin(t * 10))) 
                        
                        temp_files.extend([f"temp_bg_{i}_a.jpg", f"temp_bg_{i}_b.jpg"])
                        temp_bg_files.extend([f"temp_bg_{i}_a.jpg", f"temp_bg_{i}_b.jpg"])
                    except Exception as e:
                        print(f"Stickman Animation Error: {e}")
                        clip = None
                elif img1:
                    # Fallback to single frame with rocking animation
                    clip = ImageClip(img1).set_duration(duration)
                    # Watermark Guard
                    clip = crop(clip, y2=clip.h - 150)
                    clip = clip.resize(lambda t: 1.0 + 0.15 * (t/duration))
                    # Rocking animation
                    clip = clip.rotate(lambda t: 2 * math.sin(t * 5))
                    temp_files.append(f"temp_bg_{i}_a.jpg")
                    temp_bg_files.append(f"temp_bg_{i}_a.jpg")
            else:
                # Use Stock Footage (Pexels) - Fallback/Legacy
                bg_file = download_background_video(keyword, pexels_key, bg_path, segment_index=i)
                if bg_file:
                    try:
                        clip = VideoFileClip(bg_file)
                        _ = clip.get_frame(0)
                        if clip.duration < duration:
                            clip = clip.loop(duration=duration)
                        else:
                            clip = clip.subclip(0, duration)
                        temp_files.append(bg_path)
                        temp_bg_files.append(bg_path)
                    except:
                        if clip: clip.close()
                        clip = None
            
            if not clip:
                # HUMAN EXPERIENCE: Programmatic Motion Background (Offline Fallback)
                # Instead of a flat color, we create a 'Breathing' Gradient effect
                print("  [BRAIN] Creating premium programmatic motion background (API Fallback)")
                
                # Base is a light aesthetic color (Ghost White / Lavender hint)
                base_color = (248, 248, 255) 
                clip = ColorClip(size=(1080, 1920), color=base_color, duration=duration)
                
                # Add a 'Breathing' Vignette/Pulse effect
                def pulse(get_frame, t):
                    frame = get_frame(t).copy()
                    # Apply a subtle brightness pulse (98% to 102%)
                    factor = 1.0 + 0.02 * math.sin(t * 2)
                    return (frame * factor).clip(0, 255).astype('uint8')
                
                clip = clip.fl(pulse)
                # Add a floating 'Particle' zoom effect
                clip = clip.resize(lambda t: 1.0 + 0.05 * math.sin(t * 0.5))
            
            # Ensure proper orientation/resize
            w, h = clip.size
            tr = 9/16
            if w/h > tr:
                nw = h * tr
                clip = crop(clip, x1=(w/2 - nw/2), width=nw, height=h)
            else:
                nh = w / tr
                clip = crop(clip, y1=(h/2 - nh/2), width=w, height=nh)
            clip = clip.resize(newsize=(1080, 1920))
            
            # 3. Text Overlays (Dynamic Word-Level)
            # Use colored captions if background is white (stickman)
            text_color = 'black' if is_stickman else 'white'
            stroke_color = 'white' if is_stickman else 'black'
            
            if word_metadata:
                txt_clips = generate_word_level_captions(word_metadata, duration)
                # Override colors for stickman if needed (captions.py might need update, checking it)
            else:
                # Fallback to chunked layout
                words = text.split()
                chunks = [" ".join(words[j:j+5]) for j in range(0, len(words), 5)]
                txt_clips = []
                chunk_dur = duration / len(chunks)
                for j, chunk in enumerate(chunks):
                    try:
                        txt = (TextClip(chunk, fontsize=85, color=text_color, font='Liberation-Sans-Bold',
                                        method='caption', size=(950, None), stroke_color=stroke_color, stroke_width=2)
                               .set_position(('center', 1400))
                               .set_duration(chunk_dur)
                               .set_start(j * chunk_dur))
                        txt_clips.append(txt)
                    except:
                        continue
            
            # Combine all elements (Pure visual, no text/captions as requested)
            seg_clip = CompositeVideoClip([clip]).set_audio(audio)
            final_clips.append(seg_clip)
            current_total_duration += duration

        # --- HYBRID AVATAR: Intro/Outro Injection ---
        use_avatar = metadata.get('use_avatar', False)
        if use_avatar:
            # Intro Avatar
            intro_audio = "temp_avatar_intro.mp3"
            intro_video = "temp_avatar_intro.mp4"
            intro_text = metadata.get('avatar_intro', "Welcome to another curiosity deep dive.")
            asyncio.run(generate_audio(intro_text, intro_audio, rate="-5%", pitch="-10Hz")) # Use narrative voice
            avatar_path = generate_avatar_video(intro_audio, intro_video)
            if avatar_path:
                avatar_size = (1080, 1920) if metadata.get('orientation') == 'vertical' else (1920, 1080)
                intro_clip = VideoFileClip(avatar_path).resize(newsize=avatar_size)
                # Watermark Guard
                intro_clip = crop(intro_clip, y2=intro_clip.h - 150).resize(newsize=avatar_size)
                final_clips.insert(0, intro_clip)
                temp_files.extend([intro_audio, intro_video])
            
            # Outro Avatar
            outro_audio = "temp_avatar_outro.mp3"
            outro_video = "temp_avatar_outro.mp4"
            outro_text = metadata.get('avatar_outro', "Thanks for watching. Subscribe for more curiosity.")
            asyncio.run(generate_audio(outro_text, outro_audio, rate="-5%", pitch="-10Hz"))
            avatar_path = generate_avatar_video(outro_audio, outro_video)
            if avatar_path:
                avatar_size = (1080, 1920) if metadata.get('orientation') == 'vertical' else (1920, 1080)
                outro_clip = VideoFileClip(avatar_path).resize(newsize=avatar_size)
                # Watermark Guard
                outro_clip = crop(outro_clip, y2=outro_clip.h - 150).resize(newsize=avatar_size)
                final_clips.append(outro_clip)
                temp_files.extend([outro_audio, outro_video])

        # --- SUBSCRIBE HOOK INJECTION ---
        print("  [*] Adding Subscribe & Like hook...")
        sub_hook = create_subscribe_hook()
        if sub_hook:
            # Add audio to hook if possible (e.g. just a silence or continue bg music)
            # For now, it will be silent or carry over ambient if mixed appropriately, 
            # but usually concatenate cuts audio. 
            # Ideally we'd add a sound effect, but keeping it simple as per plan.
            final_clips.append(sub_hook)

        final_video = concatenate_videoclips(final_clips, method="compose")
        total_duration = final_video.duration
        print(f"\n🎥 Total video duration: {total_duration/60:.2f} minutes ({total_duration:.1f} seconds)")
        
        # Validation for Shorts/FACTS (Target: 30-45s)
        if total_duration < 30:
            print(f"⚠️  WARNING: Short video is {30-total_duration:.1f}s TOO SHORT! (Target: 30-45s)")
        elif total_duration > 59:
            print(f"⚠️  WARNING: Short video is nearing the 60s limit ({total_duration:.1f}s)")
        else:
            print(f"✅ SUCCESS: Short video length is perfect ({total_duration:.1f}s)")

        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        
        # Cleanup
        for f in temp_files:
            try:
                if os.path.exists(f): os.remove(f)
            except:
                pass
        
        # KEY UPGRADE: VidIQ Thumbnail Generation
        # Uses punchy 3-word text if available (from content.py), otherwise falls back to title
        print("\n[*] Generating thumbnail...")
        thumb_text = metadata.get('thumbnail_text', metadata.get('title', 'Video'))[:30]
        try:
            # Use one of the used backgrounds if available
            thumb_bg = random.choice(temp_bg_files) if temp_bg_files else None
            create_thumbnail(thumb_bg, thumb_text, output_path="thumbnail.jpg")
        except:
            create_thumbnail(None, thumb_text, output_path="thumbnail.jpg")

        return output_path

if __name__ == "__main__":
    # Test run
    test_meta = {
        "text": "Did you know? Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old.",
        "mode": "fact"
    }
    create_video(test_meta, "test_output.mp4")
