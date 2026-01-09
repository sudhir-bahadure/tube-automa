import os
import random
import requests
import asyncio
import edge_tts
import json
from datetime import datetime, timedelta
from moviepy.editor import *
from moviepy.video.fx.all import crop, resize
from avatar_engine import generate_avatar_video
from captions import generate_word_level_captions
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

async def generate_audio(text, output_file="audio.mp3", rate="+0%", pitch="+0Hz"):
    # Microsoft Edge Neural Voices (High Quality, Free)
    voice = "en-US-BrianNeural" 
    word_metadata = []
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            
            with open(output_file, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        # Convert 100ns units to seconds
                        # offset and duration are int (100-nanoseconds ticks)
                        # 1 tick = 1e-7 seconds. 10,000,000 ticks = 1 second.
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
            # AudioFileClip can throw exceptions on corrupt/zero-duration files
            try:
                test_clip = AudioFileClip(output_file)
                clip_duration = test_clip.duration
                test_clip.close()
                
                if clip_duration < 0.1:  # Less than 0.1 seconds
                    raise Exception(f"Audio duration too short ({clip_duration}s)")
                    
                print(f"  [OK] Audio generated: {file_size} bytes, duration: {clip_duration:.2f}s")
            except Exception as validation_error:
                # Don't re-raise with nested exception, just raise cleanly for retry
                raise Exception(f"Audio clip validation failed: {str(validation_error)}")
                        
            return word_metadata
            
        except Exception as e:
            print(f"Audio generation attempt {attempt+1} failed: {e}")
            if "403" in str(e):
                print("  [TIP] 403 error often means we need a version update or the service is temporarily throttling.")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3
                await asyncio.sleep(wait_time)
                word_metadata = [] # Reset on retry
                # Clean up failed file
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                    except:
                        pass
            else:
                # FALLBACK: Create silent audio as last resort
                print(f"  [FALLBACK] All retries failed, creating silent audio clip")
                try:
                    from moviepy.audio.AudioClip import AudioClip
                    import numpy as np
                    # Create 2 seconds of silence
                    silent_duration = 2.0
                    silent_audio = AudioClip(lambda t: np.zeros((int(silent_duration * 44100), 2)), 
                                            duration=silent_duration, fps=44100)
                    silent_audio.write_audiofile(output_file, fps=44100, codec='libmp3lame', verbose=False, logger=None)
                    silent_audio.close()
                    print(f"  [OK] Silent audio fallback created")
                    return []  # No word metadata for silent audio
                except Exception as fallback_error:
                    print(f"  [ERROR] Even silent audio fallback failed: {fallback_error}")
                    raise e
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
                            return output_file
    except Exception as e:
        print(f"  [ERROR] Pexels error: {e}")
        
    return None


def create_video(metadata, output_path="final_video.mp4", pexels_key=None):
    mode = metadata.get('mode', 'fact')
    
    if mode == 'meme' and 'memes' in metadata:
        # --- NEW COMPILATION LOGIC FOR MEMES ---
        memes = metadata['memes']
        meme_clips = []
        temp_bg_files = []
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
                
                duration = clip_dur + 0.5
                # Fix: Pad audio to match video duration to avoid MoviePy OSError
                audio = add_background_music(audio_clip, duration)
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
            
            # 3. Add Meme Style Overlay
            banner_h = 350
            banner = ColorClip(size=(1080, banner_h), color=(255, 255, 255), duration=duration).set_position(('center', 'top'))
            
            # Subtle divider line
            divider = ColorClip(size=(1080, 5), color=(200, 200, 200), duration=duration).set_position(('center', banner_h))

            # Try common fonts
            font_list = ['Liberation-Sans-Bold', 'Arial', 'Impact', 'Verdana']
            setup_txt = None
            for font in font_list:
                try:
                    setup_txt = (TextClip(setup, fontsize=55, color='black', font=font,
                                          method='caption', size=(1000, banner_h-40), align='center')
                                  .set_position(('center', 20))
                                  .set_duration(duration))
                    selected_font = font
                    break
                except:
                    continue
            
            if not setup_txt:
                print("Warning: Could not create TextClip. ImageMagick might be missing.")
                # Fallback to just the background/banner if text fails (prevent crash)
                meme_segment = CompositeVideoClip([clip, banner, divider]).set_audio(audio)
            else:
                # More impact for punchline
                punch_start = duration * 0.5
                punch_txt = (TextClip(punchline, fontsize=100, color='white', font=selected_font,
                                     method='caption', size=(950, None), stroke_color='black', stroke_width=3)
                             .set_position(('center', 1100))
                             .set_start(punch_start)
                             .set_duration(duration - punch_start))
                
                # Combine Meme Segment
                meme_segment = CompositeVideoClip([clip, banner, divider, setup_txt, punch_txt]).set_audio(audio)
            meme_clips.append(meme_segment.set_duration(duration))

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
        temp_bg_files = []
        temp_audio_files = []
        
        print(f"Generating long-form video: {metadata.get('topic')}...")
        print(f"Total segments: {len(segments)} (Target: 8+ minutes)")
        
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
            
            # 2. Get Background (Landscape for long videos)
            bg_filename = f"temp_long_bg_{i}.mp4"
            bg_file = download_background_video(keyword, pexels_key, bg_filename, orientation="landscape", segment_index=i)
            clip = None
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
                # Varied background colors for visual interest
                colors = [(20,20,20), (30,30,50), (50,30,30), (30,50,30), (40,40,60)]
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
            
            # Combine all elements
            segment_clip = CompositeVideoClip([clip] + chapter_overlays + txt_clips).set_audio(audio)
            segment_clips.append(segment_clip)
            
            # Progress indicator
            print(f"  ✓ Segment {i+1}/{len(segments)} complete ({duration:.1f}s)")

        # --- HYBRID AVATAR: Intro/Outro Injection ---
        use_avatar = metadata.get('use_avatar', False)
        if use_avatar:
            print("[*] Generating AI Avatar Intro/Outro...")
            # Intro Avatar
            intro_audio = "temp_avatar_intro.mp3"
            intro_video = "temp_avatar_intro.mp4"
            intro_text = metadata.get('avatar_intro', "Welcome to another curiosity deep dive.")
            asyncio.run(generate_audio(intro_text, intro_audio, rate="-5%", pitch="-10Hz")) 
            avatar_path = generate_avatar_video(intro_audio, intro_video)
            if avatar_path:
                intro_clip = VideoFileClip(avatar_path).resize(newsize=(1920, 1080))
                segment_clips.insert(0, intro_clip)
                temp_audio_files.append(intro_audio)
                temp_bg_files.append(intro_video)
            
            # Outro Avatar
            outro_audio = "temp_avatar_outro.mp3"
            outro_video = "temp_avatar_outro.mp4"
            outro_text = metadata.get('avatar_outro', "Thanks for watching. Subscribe for more curiosity.")
            asyncio.run(generate_audio(outro_text, outro_audio, rate="-5%", pitch="-10Hz"))
            avatar_path = generate_avatar_video(outro_audio, outro_video)
            if avatar_path:
                outro_clip = VideoFileClip(avatar_path).resize(newsize=(1920, 1080))
                segment_clips.append(outro_clip)
                temp_audio_files.append(outro_audio)
                temp_bg_files.append(outro_video)

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
        
        print(f"Generating enhanced sync video with {len(script_segments)} segments...")
        
        for i, seg in enumerate(script_segments):
            text = seg['text']
            keyword = seg.get('keyword', metadata.get('topic', 'abstract'))
            
            # 1. Voice
            # Specialized Voice: Energetic & Fast for Memes
            rate = "+15%" 
            pitch = "-2Hz"
            audio_path = f"temp_voc_{i}.mp3"
            word_metadata = asyncio.run(generate_audio(text, audio_path, rate=rate, pitch=pitch))
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration + 0.2
            audio = add_background_music(audio_clip, duration)
            temp_files.append(audio_path)
            
            # 2. Visual
            bg_path = f"temp_bg_{i}.mp4"
            bg_file = download_background_video(keyword, pexels_key, bg_path, segment_index=i)
            clip = None
            if bg_file:
                try:
                    clip = VideoFileClip(bg_file)
                    _ = clip.get_frame(0)
                    if clip.duration < duration:
                        clip = clip.loop(duration=duration)
                    else:
                        clip = clip.subclip(0, duration)
                    temp_files.append(bg_path)
                except:
                    if clip: clip.close()
                    clip = None
            
            if not clip:
                clip = ColorClip(size=(1080, 1920), color=(20, 20, 20), duration=duration)
            
            # Crop to Vertical
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
            if word_metadata:
                # Use precise timestamps from EdgeTTS
                txt_clips = generate_word_level_captions(word_metadata, duration)
            else:
                # Fallback to chunked layout if metadata missing
                words = text.split()
                chunks = [" ".join(words[j:j+5]) for j in range(0, len(words), 5)]
                txt_clips = []
                chunk_dur = duration / len(chunks)
                for j, chunk in enumerate(chunks):
                    try:
                        txt = (TextClip(chunk, fontsize=75, color='white', font='Liberation-Sans-Bold',
                                        method='caption', size=(950, None), stroke_color='black', stroke_width=3)
                               .set_position('center')
                               .set_duration(chunk_dur)
                               .set_start(j * chunk_dur))
                        txt_clips.append(txt)
                    except:
                        continue
            
            seg_clip = CompositeVideoClip([clip] + txt_clips).set_audio(audio)
            final_clips.append(seg_clip)

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
                final_clips.append(outro_clip)
                temp_files.extend([outro_audio, outro_video])

        final_video = concatenate_videoclips(final_clips, method="compose")
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        
        # Cleanup
        for f in temp_files:
            try:
                if os.path.exists(f): os.remove(f)
            except:
                pass
                
        return output_path

if __name__ == "__main__":
    # Test run
    test_meta = {
        "text": "Did you know? Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old.",
        "mode": "fact"
    }
    create_video(test_meta, "test_output.mp4")
