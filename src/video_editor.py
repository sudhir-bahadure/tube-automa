from moviepy.editor import *
import moviepy.video.fx.all as vfx
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class VideoEditor:
    def _create_text_clip(self, text, size, fontsize, color, stroke_color, stroke_width, duration):
        """Creates a TextClip using PIL as a fallback to avoid ImageMagick issues."""
        try:
            # Try to load a font
            try:
                # Common Windows font paths
                font = ImageFont.truetype("arialbd.ttf", fontsize)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", fontsize)
                except:
                    font = ImageFont.load_default()

            # Create an image with transparent background (RGBA)
            img = Image.new('RGBA', size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Wrap text manually
            import textwrap
            lines = textwrap.wrap(text, width=30) 
            
            current_h = 10 # Some top padding
            for line in lines:
                if hasattr(draw, 'textbbox'):
                    bbox = draw.textbbox((0, 0), line, font=font)
                    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                else:
                    w, h = draw.textsize(line, font=font)
                
                # Draw stroke
                if stroke_width > 0:
                    for offset_x in range(-stroke_width, stroke_width + 1):
                        for offset_y in range(-stroke_width, stroke_width + 1):
                            draw.text(((size[0]-w)/2 + offset_x, current_h + offset_y), line, font=font, fill=stroke_color)

                draw.text(((size[0]-w)/2, current_h), line, font=font, fill=color)
                current_h += h + 15
            
            # Convert to RGB array for MoviePy and also get alpha channel
            rgb_img = img.convert('RGB')
            alpha_img = img.convert('L') # Luminance as alpha
            
            # Create clip with mask for transparency
            clip = ImageClip(np.array(rgb_img)).set_duration(duration)
            mask = ImageClip(np.array(alpha_img), ismask=True).set_duration(duration)
            
            return clip.set_mask(mask)
            
        except Exception as e:
            print(f"PIL Text Render failed: {e}")
            return ColorClip(size=size, color=(0,0,0,0), duration=duration)
    def create_video(self, scenes, output_video_path, is_short=True, bg_music_path=None, style="noir", bg_color="#FFFFFF"):
        """
        Stitches visualization, audio and subtitles with dynamic animations and transitions.
        style: "noir" (Standard dark surreal) or "stickman" (Minimalist stick figures on white)
        """
        if is_short:
            target_w, target_h = 1080, 1920
        else:
            target_w, target_h = 1920, 1080

        clips = []
        for i, scene in enumerate(scenes):
            try:
                # Load Audio
                a_path = scene.get('audio_path', '')
                if a_path and os.path.exists(a_path):
                    audio_clip = AudioFileClip(a_path)
                else:
                    # Silence fallback
                    from moviepy.audio.AudioClip import AudioArrayClip
                    audio_clip = AudioArrayClip(np.zeros((44100, 2)), fps=44100).set_duration(2)
                
                duration = audio_clip.duration
                v_path = scene.get('video_path', '')
                video_clip = None
                
                if v_path and os.path.exists(v_path):
                    if v_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        try:
                            # Process Image - Use PIL to avoid imageio backend errors
                            from PIL import Image as PILImage
                            pil_img = PILImage.open(v_path)
                            img_array = np.array(pil_img)
                            # FAIL-SAFE: Crop bottom 8% of the image to remove potential Pollinations logo
                            h, w = img_array.shape[:2]
                            crop_h = int(h * 0.08)
                            img_array = img_array[:h-crop_h, :] 
                            img_clip = ImageClip(img_array).set_duration(duration)
                            
                            # If we reached here, img_clip is valid. 
                            # Let's handle the style logic inside the try block for safety.
                            
                            if style == "stickman" or style == "psych_stickman":
                                # VIRAL STYLE: Solid Vibrant BG (Selected by AI), Centered, Pleasant Liveness
                                
                                # 1. CREATE SOLID BACKGROUND
                                # Convert hex to RGB if necessary
                                if isinstance(bg_color, str) and bg_color.startswith('#'):
                                    hex_val = bg_color.lstrip('#')
                                    bg_rgb = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
                                else:
                                    bg_rgb = (255, 255, 255) # Fallback to white

                                backgrounds = []
                                # Base vibrant layer
                                bg_base = ColorClip(size=(target_w, target_h), color=bg_rgb).set_duration(duration)
                                backgrounds.append(bg_base)
                                
                                # Add 3 minimalist drifting particles (reduced for clean look)
                                for p_idx in range(3):
                                    p_size = random.randint(3, 8)
                                    p_color = (255, 255, 255) # white particles on vibrant BG
                                    p_clip = ColorClip(size=(p_size, p_size), color=p_color).set_duration(duration)
                                    
                                    start_x = random.randint(0, target_w)
                                    start_y = random.randint(0, target_h)
                                    speed_x = random.uniform(-15, 15)
                                    speed_y = random.uniform(-15, 15)
                                    
                                    p_clip = p_clip.set_position(lambda t, sx=start_x, sy=start_y, spx=speed_x, spy=speed_y: 
                                                                (sx + spx*t, sy + spy*t)).set_opacity(0.15)
                                    backgrounds.append(p_clip)
                                
                                bg_composite = CompositeVideoClip(backgrounds, size=(target_w, target_h))
                                
                                # 2. CHARACTER ANIMATION (SQUASH & STRETCH)
                                img_clip = img_clip.resize(width=int(target_w * 0.7))
                                v_action = scene.get('vocal_action', 'talking')
                                is_punchline = scene.get('is_punchline', False)
                                
                                # Base floating position
                                base_y = target_h/2 - img_clip.h/2
                                base_pos = lambda t, by=base_y: ('center', by + 15 * math.sin(2 * math.pi * 0.33 * t))
                                
                                if v_action == 'jumping':
                                    # Intense vertical bounce with Stretch at peak and Squash at landing
                                    def jumping_pos(t, by=base_y):
                                        jump_val = abs(150 * math.sin(2 * math.pi * 0.8 * t))
                                        return ('center', by - jump_val)
                                    
                                    def jumping_scale(t):
                                        # Squash when t makes sin close to 0 (landing), Stretch when sin close to 1 (peak)
                                        cycle = abs(math.sin(2 * math.pi * 0.8 * t))
                                        # Scale y inverse to x
                                        return 1.0 + 0.1 * (cycle - 0.5) 
                                    
                                    video_clip = img_clip.set_position(jumping_pos).resize(jumping_scale)
                                
                                elif v_action == 'bouncing' or v_action == 'jumping':
                                    # Squash & Stretch Bounce
                                    video_clip = img_clip.resize(lambda t: 1.0 + 0.15 * abs(math.sin(2 * math.pi * 0.7 * t))).set_position(base_pos)
                                
                                elif v_action == 'shaking' or is_punchline:
                                    # High frequency jitter (Intense for punchlines)
                                    intensity = 35 if is_punchline else 8 # Increase intensity
                                    video_clip = img_clip.set_position(lambda t, by=base_y, inst=intensity: 
                                                                    ('center', by + random.uniform(-inst, inst)))
                                    if is_punchline:
                                        # Sudden Zoom Punch
                                        video_clip = video_clip.resize(lambda t: 1.15 + 0.1 * math.sin(2 * math.pi * 5 * t)) 
                                        
                                        # Add extra pop with opacity flicker? No, zoom is better.
                                        video_clip = video_clip.set_start(0)
                                
                                elif v_action == 'waving':
                                    video_clip = img_clip.rotate(lambda t: 5 * math.sin(2 * math.pi * 0.5 * t)).set_position(base_pos)
                                else:
                                    video_clip = img_clip.set_position(base_pos)
                                
                                # Apply Breathing (Slow Scaling)
                                if v_action not in ['bouncing', 'jumping'] and not is_punchline:
                                    video_clip = video_clip.resize(lambda t: 1.0 + 0.015 * math.sin(2 * math.pi * 0.25 * t))
                                
                                # TRANSITION LOGIC
                                if style == "stickman":
                                    # Original Meme Style: Fade In/Out (Blink)
                                    video_clip = video_clip.fadein(0.4).fadeout(0.4)
                                else:
                                    # Professional Psych Stickman: Fade In only, no fade out (continuous)
                                    video_clip = video_clip.fadein(0.2)

                                video_clip = CompositeVideoClip([bg_composite, video_clip.set_start(0)])
                                
                            elif style == "noir":
                                # NOIR STYLE: Cinematic, slow, creepy animations
                                
                                anim_type = random.choice(['slow_zoom_in', 'slow_zoom_out', 'subtle_pan'])
                                
                                # Ensure we have enough resolution to crop/move
                                base_scale = 1.2
                                if is_short:
                                    img_clip = img_clip.resize(height=int(target_h * base_scale))
                                else:
                                    img_clip = img_clip.resize(width=int(target_w * base_scale))
                                    
                                # Center Crop Initial
                                img_clip = img_clip.crop(x_center=img_clip.w/2, y_center=img_clip.h/2, width=int(target_w * 1.1), height=int(target_h * 1.1))

                                if anim_type == 'slow_zoom_in':
                                    video_clip = img_clip.resize(lambda t: 1.0 + 0.05 * (t/duration))
                                elif anim_type == 'slow_zoom_out':
                                    video_clip = img_clip.resize(lambda t: 1.1 - 0.05 * (t/duration))
                                elif anim_type == 'subtle_pan':
                                    video_clip = img_clip.set_position(lambda t: (int(-0.05 * target_w * (t/duration)), 'center'))
                                
                                if 'zoom' in anim_type:
                                    video_clip = video_clip.set_position('center')
                                    
                                video_clip = video_clip.crop(x_center=video_clip.w/2, y_center=video_clip.h/2, width=target_w, height=target_h)
                            else:
                                video_clip = img_clip.set_position('center')
                                
                        except Exception as img_err:
                            print(f"  [ERROR] Image processing failed for {v_path}: {img_err}")
                            video_clip = None
                            
                    elif v_path.lower().endswith(('.mp4', '.mov', '.avi')):
                        try:
                            video_clip = VideoFileClip(v_path)
                            if video_clip.duration < duration:
                                video_clip = video_clip.loop(duration=duration)
                            else:
                                video_clip = video_clip.subclip(0, duration)
                            
                            if video_clip.w / video_clip.h > target_w / target_h:
                                video_clip = video_clip.resize(height=target_h)
                            else:
                                video_clip = video_clip.resize(width=target_w)
                            video_clip = video_clip.crop(x_center=video_clip.w/2, y_center=video_clip.h/2, width=target_w, height=target_h)
                        except Exception as vid_err:
                            print(f"  [ERROR] Video processing failed for {v_path}: {vid_err}")
                            video_clip = None
                
                # FALLBACK: If visual is missing or failed to load
                if video_clip is None:
                    print(f"  [FALLBACK] Searching for fallback image for scene {i+1}")
                    fallback_dir = "assets/fallbacks"
                    fallback_file = None
                    if os.path.exists(fallback_dir):
                        # Try to find style-specific fallback
                        style_file = f"fallback_{style}.jpg" if style in ["noir", "stickman"] else "fallback_generic.jpg"
                        if os.path.exists(os.path.join(fallback_dir, style_file)):
                            fallback_file = os.path.join(fallback_dir, style_file)
                        else:
                            # Fallback to generic if style-specific missing
                            generic_file = os.path.join(fallback_dir, "fallback_generic.jpg")
                            if os.path.exists(generic_file):
                                fallback_file = generic_file
                            else:
                                # Pick any jpg in the dir
                                import glob
                                fallback_options = glob.glob(os.path.join(fallback_dir, "*.jpg"))
                                if fallback_options:
                                    fallback_file = random.choice(fallback_options)

                    if fallback_file:
                        print(f"  [FALLBACK] Using image asset: {fallback_file}")
                        # Load and process the fallback image
                        try:
                            from PIL import Image as PILImage
                            pil_img = PILImage.open(fallback_file)
                            img_array = np.array(pil_img)
                            # Resize to target
                            fallback_clip = ImageClip(img_array).set_duration(duration)
                            
                            # Apply subtle movement
                            if style == "noir":
                                # Slow zoom for noir
                                video_clip = fallback_clip.resize(lambda t: 1.0 + 0.05 * (t/duration)).set_position('center')
                            else:
                                # Gentle breathing for others
                                video_clip = fallback_clip.resize(lambda t: 1.05 + 0.02 * math.sin(math.pi * t / duration)).set_position('center')
                            
                            video_clip = video_clip.crop(x_center=video_clip.w/2, y_center=video_clip.h/2, width=target_w, height=target_h)
                        except Exception as fe:
                            print(f"  [ERROR] Failed to load fallback image {fallback_file}: {fe}")
                            video_clip = None

                    if video_clip is None:
                        # FINAL FAILSAFE: solid color
                        print(f"  [FAILSAFE] Using solid color for scene {i+1}")
                        fallback_color = (30, 30, 30) # Dark grey
                        video_clip = ColorClip(size=(target_w, target_h), color=fallback_color, duration=duration)

                video_clip = video_clip.set_audio(audio_clip)
                
                # Overly Comedy SFX for Punchlines
                if style == "stickman" and scene.get('is_punchline'):
                    sfx_dir = "assets/sfx"
                    if os.path.exists(sfx_dir):
                        import glob
                        sfx_files = glob.glob(os.path.join(sfx_dir, "*.mp3")) + glob.glob(os.path.join(sfx_dir, "*.wav"))
                        if sfx_files:
                            try:
                                selected_sfx = random.choice(sfx_files)
                                sfx_clip = AudioFileClip(selected_sfx).volumex(0.8)
                                # Mix with original audio
                                if sfx_clip.duration > video_clip.duration:
                                    sfx_clip = sfx_clip.subclip(0, video_clip.duration)
                                video_clip.audio = CompositeAudioClip([video_clip.audio, sfx_clip])
                                print(f"DEBUG: Added comedy SFX: {os.path.basename(selected_sfx)}")
                            except Exception as sfx_e:
                                print(f"SFX Overlay Error: {sfx_e}")

                # Crossfade Mapping
                if i > 0:
                    if style == "psych_stickman":
                        video_clip = video_clip.crossfadein(0.3)
                    elif style != "stickman": # Noir/Standard
                        video_clip = video_clip.crossfadein(0.5)

                # Subtitles / Captions
                txt_h = 400
                if is_short:
                    txt_w = int(target_w * 0.9)
                    # MEME STYLE: Impact-like bold white with thick black stroke
                    txt_clip = self._create_text_clip(
                        scene['text'].upper(), # Memes usually have all-caps
                        size=(txt_w, txt_h),
                        fontsize=70, # Larger for memes
                        color='white', 
                        stroke_color='black', 
                        stroke_width=5, # Thicker stroke
                        duration=duration
                    )
                    txt_clip = txt_clip.set_pos(('center', target_h * 0.75)).set_duration(duration)
                    final_scene = CompositeVideoClip([video_clip, txt_clip])
                else:
                    txt_w = int(target_w * 0.8)
                    txt_clip = self._create_text_clip(
                        scene['text'], 
                        size=(txt_w, txt_h),
                        fontsize=40, 
                        color='black' if style == "stickman" else 'white', 
                        stroke_color='white' if style == "stickman" else 'black', 
                        stroke_width=1,
                        duration=duration
                    )
                    txt_clip = txt_clip.set_pos(('center', target_h * 0.85)).set_duration(duration)
                    final_scene = CompositeVideoClip([video_clip, txt_clip])
                
                clips.append(final_scene)
                
            except Exception as e:
                print(f"Error processing scene: {e}")
        
        if clips:
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Add Background Music
            if bg_music_path and os.path.exists(bg_music_path):
                # Professional Volume Mixing:
                # Noir (Psychology) needs subtle atmosphere (0.08-0.12)
                # Stickman (Meme) can have higher energy (0.15-0.20)
                music_volume = 0.18 if style == "stickman" else 0.10
                bg_audio = AudioFileClip(bg_music_path).volumex(music_volume)
                
                if bg_audio.duration < final_video.duration:
                    bg_audio = bg_audio.loop(duration=final_video.duration)
                else:
                    bg_audio = bg_audio.subclip(0, final_video.duration)
                
                # Professional Transitions: 1s Fade In, 2s Fade Out
                bg_audio = bg_audio.audio_fadein(1).audio_fadeout(2)
                
                # Combine original voice (from final_video) with background music
                final_audio = CompositeAudioClip([final_video.audio, bg_audio])
                
                final_video = final_video.set_audio(final_audio)

            final_video.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile="temp_audio.m4a", threads=4)
            return True
        return False
