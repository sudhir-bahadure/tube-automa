import os
import random
import requests
import asyncio
import edge_tts
import json
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, ColorClip, ImageClip, concatenate_videoclips
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.video.fx.all import crop, resize
# Removed silent logging override as it causes issues in some moviepy versions

# ============================================================================
# VISUAL TRACKING SYSTEM - Prevents video repetition
# ============================================================================

TRACKING_FILE = "used_videos.json"

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


# Audio Mixing Engine
def mix_audio(voice_clip, music_path=None, sfx_path=None, music_vol=0.1):
    """Mix voice with background music and optional SFX"""
    audio_clips = [voice_clip]
    
    # 1. Background Music
    if music_path and os.path.exists(music_path):
        try:
            music = AudioFileClip(music_path)
            # Loop music to match voice duration
            if music.duration < voice_clip.duration:
                from moviepy.audio.fx.all import audio_loop
                music = audio_loop(music, duration=voice_clip.duration)
            else:
                music = music.subclip(0, voice_clip.duration)
            
            # Apply ducking (volume reduction)
            music = music.volumex(music_vol)
            audio_clips.append(music)
        except Exception as e:
            print(f"  [WARN] Music mix failed: {e}")

    # 2. Sound Effects (e.g., Laugh Track)
    if sfx_path and os.path.exists(sfx_path):
        try:
            sfx = AudioFileClip(sfx_path)
            # Add SFX at the end/punchline (simple logic: start at 70% of clip)
            start_time = max(0, voice_clip.duration - sfx.duration - 0.5) 
            sfx = sfx.set_start(start_time).volumex(0.8)
            audio_clips.append(sfx)
        except Exception as e:
            print(f"  [WARN] SFX mix failed: {e}")
            
    return CompositeAudioClip(audio_clips).set_duration(voice_clip.duration)

async def generate_audio(text, output_file="audio.mp3", rate="+0%", pitch="+0Hz"):
    # Microsoft Edge Neural Voices (High Quality, Free)
    voice = "en-US-AriaNeural" # Female, Natural, Professional 
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await communicate.save(output_file)
            return
        except Exception as e:
            print(f"Audio generation attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2) # Backoff
            else:
                # If all else fails, we might need a backup or silent clip, but let's try to crash early if critical
                raise e

def download_background_video(query="abstract", api_key=None, output_file="bg_raw.mp4", orientation="portrait", segment_index=0):
    # Fallback to a solid color if no API key or download fails
    if not api_key:
        return None
    
    # Add variation to query to get different results
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
                if not unused_videos and query != varied_query:
                    print(f"  [INFO] All videos used for '{varied_query}', trying base query...")
                    return download_background_video(query, api_key, output_file, orientation, segment_index + 1)
                
                # If still no unused videos, expand search
                if not unused_videos:
                    print(f"  [INFO] All videos used, expanding search...")
                    return download_background_video(f"{query} cinematic", api_key, output_file, orientation, segment_index + 2)
                
                # Select random unused video
                video_data = random.choice(unused_videos)
                video_files = video_data.get('video_files', [])
                # Prefer HD/Full HD but keep it manageable
                video_files = [v for v in video_files if v['width'] >= 720]
                if not video_files:
                    video_files = video_data.get('video_files', [])
                
                best_file = min(video_files, key=lambda x: abs(x['width'] - 1080))
                link = best_file['link']
                
                print(f"  [NEW] Downloading fresh background: {link[:60]}...")
                with requests.get(link, stream=True, timeout=15) as res:
                    if res.status_code == 200:
                        with open(output_file, "wb") as f:
                            for chunk in res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Verify file size (at least 100KB)
                        if os.path.exists(output_file) and os.path.getsize(output_file) > 102400:
                            save_used_video(link, query)  # Track this video
                            return output_file
                        else:
                            print("  [WARN] Downloaded video too small, likely corrupted.")
                            if os.path.exists(output_file): os.remove(output_file)
    except Exception as e:
        print(f"  [ERROR] Pexels download error: {e}")
        
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
        
        # --- INTRO HOOK (For Long Compilations or Branding) ---
        if metadata.get('is_long_compilation', False):
             # Generate Intro Audio
             intro_audio_path = "temp_intro_audio.mp3"
             intro_script = "Welcome to yo Daily Meme Dose! Get ready to laugh!"
             asyncio.run(generate_audio(intro_script, intro_audio_path))
             intro_audio_clip = AudioFileClip(intro_audio_path)
             temp_audio_files.append(intro_audio_path)
             
             # Intro Clip (Standard Banner Style)
             intro_dur = intro_audio_clip.duration + 0.5
             intro_audio = CompositeAudioClip([intro_audio_clip]).set_duration(intro_dur)
             
             # Visual
             intro_bg = download_background_video("happy girl waving", pexels_key, "temp_intro_bg.mp4", 0)
             if intro_bg:
                 intro_clip = VideoFileClip(intro_bg).resize(newsize=(1080, 1920))
                 if intro_clip.duration < intro_dur: intro_clip = intro_clip.loop(duration=intro_dur)
                 else: intro_clip = intro_clip.subclip(0, intro_dur)
                 temp_bg_files.append(intro_bg)
             else:
                 intro_clip = ColorClip(size=(1080, 1920), color=(50, 50, 200), duration=intro_dur)

             # Overlay
             intro_txt = (TextClip("WELCOME TO\nyoDailyMemeDose", fontsize=80, color='white', font='Impact',
                                   size=(1000, 1920), method='caption', align='center', stroke_color='black', stroke_width=4)
                           .set_position('center')
                           .set_duration(intro_dur))
             
             intro_segment = CompositeVideoClip([intro_clip, intro_txt]).set_audio(intro_audio)
             meme_clips.append(intro_segment)

        for i, meme in enumerate(memes):
            setup = meme['setup']
            punchline = meme['punchline']
            
            # 1. Generate Audio for this joke
            audio_path = f"temp_audio_{i}.mp3"
            script = f"{setup} ... ... {punchline} ... Hahaha!"
            asyncio.run(generate_audio(script, audio_path))
            audio_clip = AudioFileClip(audio_path)
            temp_audio_files.append(audio_path)
            
            duration = audio_clip.duration + 0.5
            # Fix: Pad audio to match video duration to avoid MoviePy OSError
            # from moviepy.audio.AudioClip import CompositeAudioClip
            # audio = CompositeAudioClip([audio_clip]).set_duration(duration)
            
            # --- VIRAL POLISH: mix_audio implementation ---
            # 1. Select Music (Random from assets/music/*.mp3)
            music_file = None
            try:
                music_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'music')
                if os.path.exists(music_dir):
                    mp3s = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
                    if mp3s:
                        music_file = os.path.join(music_dir, random.choice(mp3s))
            except: pass

            # 2. Select SFX (Laugh Track)
            sfx_file = None
            try:
                sfx_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'sfx')
                # Only add laugh track for punchlines (every clip in meme mode is essentially a punchline/joke)
                if os.path.exists(sfx_dir) and random.random() > 0.3: # 70% chance of laugh track
                    sfxs = [f for f in os.listdir(sfx_dir) if "laugh" in f.lower() or "punch" in f.lower()]
                    if sfxs:
                        sfx_file = os.path.join(sfx_dir, random.choice(sfxs))
            except: pass
            
            audio = mix_audio(audio_clip, music_path=music_file, sfx_path=sfx_file, music_vol=0.08)
            # -----------------------------------------------
            
            # 2. Get Background for this segment
            # Use unique filename to prevent locking/overwrite issues
            # Vary keywords for different visuals each time
            # Vary keywords for different visuals each time
            # Vary keywords for different visuals each time - GIRLS ONLY (User Request)
            bg_keywords = [
                "girl laughing",
                "woman laughing portrait",
                "happy girl smiling",
                "woman giggling",
                "female model laughing",
                "pretty girl laugh",
                "woman happy face",
                "girl reaction laugh"
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

        # --- NEW SUBSCRIBE HOOK ---
        # Generate Audio for Subscribe
        sub_audio_path = "temp_audio_sub.mp3"
        sub_script = "Subscribe for more Daily Meme Dose!"
        asyncio.run(generate_audio(sub_script, sub_audio_path))
        sub_audio_clip = AudioFileClip(sub_audio_path)
        temp_audio_files.append(sub_audio_path)
        
        sub_duration = sub_audio_clip.duration + 1.0 # Little extra pause
        sub_audio = CompositeAudioClip([sub_audio_clip]).set_duration(sub_duration)
        
        # Subscribe Visuals
        # Use a nice varied background
        sub_bg_file = download_background_video("happy celebration", pexels_key, "temp_bg_sub.mp4", segment_index=99)
        sub_clip = None
        if sub_bg_file:
             try:
                 sub_clip = VideoFileClip(sub_bg_file)
                 # Resize logic
                 w, h = sub_clip.size
                 target_ratio = 9/16
                 if w/h > target_ratio:
                     new_w = h * target_ratio
                     sub_clip = crop(sub_clip, x1=(w/2 - new_w/2), width=new_w, height=h)
                 else:
                     new_h = w / target_ratio
                     sub_clip = crop(sub_clip, y1=(h/2 - new_h/2), width=w, height=new_h)
                 sub_clip = sub_clip.resize(newsize=(1080, 1920))
                 
                 if sub_clip.duration < sub_duration:
                     sub_clip = sub_clip.loop(duration=sub_duration)
                 else:
                      sub_clip = sub_clip.subclip(0, sub_duration)
                 temp_bg_files.append(sub_bg_file)
             except:
                 sub_clip = None
        
        if not sub_clip:
            sub_clip = ColorClip(size=(1080, 1920), color=(255, 50, 50), duration=sub_duration)

        # Standardize Subscribe Hook Layout (White Banner)
        # Banner & Divider
        banner_h = 350
        sub_banner = ColorClip(size=(1080, banner_h), color=(255, 255, 255), duration=sub_duration).set_position(('center', 'top'))
        sub_divider = ColorClip(size=(1080, 5), color=(200, 200, 200), duration=sub_duration).set_position(('center', banner_h))
        
        # Text in Banner
        sub_banner_txt = (TextClip("SUBSCRIBE FOR MORE", fontsize=65, color='black', font='Impact',
                              method='caption', size=(1000, banner_h-40), align='center')
                      .set_position(('center', 20))
                      .set_duration(sub_duration))
                      
        # Channel Name Overlay (Bottom)
        sub_channel_txt = (TextClip("@DailyMemeDose", fontsize=80, color='white', font='Impact',
                               size=(1000, None), method='caption', align='center', stroke_color='black', stroke_width=3)
                       .set_position(('center', 1200)) # Lower area
                       .set_duration(sub_duration))
        
        sub_segment = CompositeVideoClip([sub_clip, sub_banner, sub_divider, sub_banner_txt, sub_channel_txt]).set_audio(sub_audio)
        meme_clips.append(sub_segment)

        # Final Concatenation
        final_video = concatenate_videoclips(meme_clips, method="compose")
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        
        # --- ENHANCED CLEANUP: Close all clips to free resources ---
        final_video.close()
        for c in meme_clips:
            try: c.close()
            except: pass
        
        # Cleanup temp files
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
            audio_path = f"temp_long_audio_{i}.mp3"
            asyncio.run(generate_audio(text, audio_path, rate=rate, pitch=pitch))
            audio_clip = AudioFileClip(audio_path)
            temp_audio_files.append(audio_path)
            
            duration = audio_clip.duration + 0.5
            from moviepy.audio.AudioClip import CompositeAudioClip
            audio = CompositeAudioClip([audio_clip]).set_duration(duration)
            
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

        # Final Concatenation
        final_video = concatenate_videoclips(segment_clips, method="compose")
        total_duration = final_video.duration
        print(f"\n🎥 Total video duration: {total_duration/60:.2f} minutes ({total_duration:.1f} seconds)")
        
        if total_duration < 480:  # Less than 8 minutes
            print(f"⚠️  WARNING: Video is {480-total_duration:.0f} seconds SHORT of 8-minute target!")
        else:
            print(f"✅ SUCCESS: Video meets 8+ minute requirement!")
        
        # Save with optimized settings (better quality than ultrafast)
        final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", 
                                    preset="medium", bitrate="2500k")
        
        # --- ENHANCED CLEANUP ---
        final_video.close()
        for c in segment_clips:
            try: c.close()
            except: pass

        # Cleanup temp files
        for f in temp_audio_files + temp_bg_files:
            try:
                if os.path.exists(f): os.remove(f)
            except:
                pass
            
        return output_path

    else:
        # --- FACT STYLE (OR SINGLE JOKE FALLBACK) ---
        text = metadata['text']
        # --- VIRAL POLISH: Use Contextual Keyword ---
        # Default to "satisfying" if no keyword passed, or specific keyword if present
        visual_keyword = metadata.get('keyword', 'satisfying')
        print(f" using visual keyword: {visual_keyword}")
        
        # 1. Generate Audio
        asyncio.run(generate_audio(text, "temp_audio.mp3"))
        audio_clip = AudioFileClip("temp_audio.mp3")
        duration = audio_clip.duration + 0.5 

        # --- VIRAL POLISH: Audio Mixing for Facts ---
        # Facts usually need subtle background music to keep retention
        music_file = None
        try:
             music_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'music')
             if os.path.exists(music_dir):
                 mp3s = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
                 if mp3s:
                     music_file = os.path.join(music_dir, random.choice(mp3s))
        except: pass
        
        # Mix with ducking (no SFX usually for facts)
        audio = mix_audio(audio_clip, music_path=music_file, music_vol=0.10)
        # ---------------------------------------------
        
        # 2. Get Background
        bg_file = download_background_video(visual_keyword, pexels_key, "temp_bg.mp4")
        
        if bg_file:
            try:
                clip = VideoFileClip(bg_file)
                # Explicitly check if we can read the first frame
                _ = clip.get_frame(0)
                
                if clip.duration < duration:
                    clip = clip.loop(duration=duration)
                else:
                    clip = clip.subclip(0, duration)
            except Exception as e:
                print(f"Corrupted fact background skip: {e}")
                if clip: clip.close()
                clip = None
        
        if not clip:
            clip = ColorClip(size=(1080, 1920), color=(20, 20, 20), duration=duration)
        
        w, h = clip.size
        target_ratio = 9/16
        if w/h > target_ratio:
            new_w = h * target_ratio
            clip = crop(clip, x1=(w/2 - new_w/2), width=new_w, height=h)
        else:
            new_h = w / target_ratio
            clip = crop(clip, y1=(h/2 - new_h/2), width=w, height=new_h)
        clip = clip.resize(newsize=(1080, 1920))
        
        words = text.split()
        chunks = []
        chunk_size = 5
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i+chunk_size]))
            
        font_list = ['Liberation-Sans-Bold', 'Arial', 'Impact', 'Verdana']
        txt_clips = []
        chunk_duration = duration / len(chunks)
        for i, chunk in enumerate(chunks):
            txt = None
            for font in font_list:
                try:
                    txt = (TextClip(chunk, fontsize=70, color='white', font=font, 
                                   method='caption', size=(900, None), stroke_color='black', stroke_width=2)
                           .set_position('center')
                           .set_duration(chunk_duration)
                           .set_start(i * chunk_duration))
                    break
                except:
                    continue
            if txt:
                txt_clips.append(txt)
            
        final_clip = CompositeVideoClip([clip] + txt_clips).set_audio(audio)
        final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
        
        # --- ENHANCED CLEANUP ---
        final_clip.close()
        if clip: clip.close()
        for t in txt_clips: t.close()
        # ------------------------

        try:
            os.remove("temp_audio.mp3")
            if bg_file: os.remove(bg_file)
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
