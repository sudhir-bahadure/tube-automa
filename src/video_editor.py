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
    def create_video(self, scenes, output_path, is_short=True, bg_music_path=None, style="noir"):
        """
        Stitches visualization, audio and subtitles with dynamic animations and transitions.
        style: "noir" (Standard dark surreal) or "stickman" (Minimalist stick figures on white)
        """
        import sys
        sys.stdout.write(f"DEBUG: Entering create_video with {len(scenes)} scenes...\n")
        sys.stdout.flush()
        import random
        import math
        
        # Target Dimensions
        if is_short:
            target_w, target_h = 1080, 1920
        else:
            target_w, target_h = 1920, 1080

        clips = []
        for i, scene in enumerate(scenes):
            try:
                # Load Audio
                audio_clip = AudioFileClip(scene['audio_path'])
                duration = audio_clip.duration
                
                # Load Visual (Video OR Image)
                v_path = scene['video_path']
                if os.path.exists(v_path):
                    if v_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        # Process Image - Use PIL to avoid imageio backend errors
                        from PIL import Image as PILImage
                        pil_img = PILImage.open(v_path)
                        img_array = np.array(pil_img)
                        img_clip = ImageClip(img_array).set_duration(duration)
                        
                        if style == "stickman" or style == "psych_stickman":
                            # STICKMAN STYLE: Pure White BG, Centered, Fade In/Out, Pleasant Liveness
                            
                            # 1. CREATE PARTICLE BACKGROUND
                            backgrounds = []
                            # Base white layer
                            bg_base = ColorClip(size=(target_w, target_h), color=(255, 255, 255)).set_duration(duration)
                            backgrounds.append(bg_base)
                            
                            # Add 5 minimalist drifting particles (small gray dots/squares)
                            for p_idx in range(5):
                                p_size = random.randint(4, 10)
                                p_color = (220, 220, 220) # Subtle gray
                                p_clip = ColorClip(size=(p_size, p_size), color=p_color).set_duration(duration)
                                
                                start_x = random.randint(0, target_w)
                                start_y = random.randint(0, target_h)
                                speed_x = random.uniform(-20, 20)
                                speed_y = random.uniform(-20, 20)
                                
                                p_clip = p_clip.set_position(lambda t, sx=start_x, sy=start_y, spx=speed_x, spy=speed_y: 
                                                            (sx + spx*t, sy + spy*t)).set_opacity(0.3)
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
                                intensity = 25 if is_punchline else 8
                                video_clip = img_clip.set_position(lambda t, by=base_y, inst=intensity: 
                                                                  ('center', by + random.uniform(-inst, inst)))
                                if is_punchline:
                                    video_clip = video_clip.resize(lambda t: 1.1 + 0.05 * math.sin(2 * math.pi * 10 * t)) # Visual pop
                            
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

                            final_scene_bg = CompositeVideoClip([bg_composite, video_clip.set_start(0)])
                            video_clip = final_scene_bg
                        elif style == "noir":
                            # NOIR STYLE: Cinematic, slow, creepy animations
                            # We want to avoid "bouncy" or "fast" movements.
                            # Focus on: Slow Zooms (Kenneth Burns), Slow Pans.
                            
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
                                # Very slow crawl in
                                video_clip = img_clip.resize(lambda t: 1.0 + 0.05 * (t/duration))
                            elif anim_type == 'slow_zoom_out':
                                # Very slow crawl out
                                video_clip = img_clip.resize(lambda t: 1.1 - 0.05 * (t/duration))
                            elif anim_type == 'subtle_pan':
                                # Horizontal drift
                                video_clip = img_clip.set_position(lambda t: (int(-0.05 * target_w * (t/duration)), 'center'))
                            
                            # Center anchor for zooms
                            if 'zoom' in anim_type:
                                video_clip = video_clip.set_position('center')
                                
                            # Final Crop to viewport
                            video_clip = video_clip.crop(x_center=video_clip.w/2, y_center=video_clip.h/2, width=target_w, height=target_h)
                            
                            # Color Grading: High Contrast B&W (Noir)
                            # MoviePy doesn't have robust color grading built-in without ImageMagick sometimes
                            # But we can try simple saturation adjustments if available or assume image gen did it.
                            # For now, rely on image prompt "noir, bw-photography".
                            
                            # Vignette (Optional, if we implemented a mask overlay)

                        else:
                            # STANDARD / FALLBACK STYLE
                            video_clip = img_clip.set_position('center')
                    else:
                        # Video Handling
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
                else:
                    video_clip = ColorClip(size=(target_w, target_h), color=(0,0,0), duration=duration)

                video_clip = video_clip.set_audio(audio_clip)

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
                    txt_clip = self._create_text_clip(
                        scene['text'], 
                        size=(txt_w, txt_h),
                        fontsize=50, 
                        color='black' if style == "stickman" else 'white', 
                        stroke_color='white' if style == "stickman" else 'black', 
                        stroke_width=2,
                        duration=duration
                    )
                    txt_clip = txt_clip.set_pos(('center', target_h * 0.8)).set_duration(duration)
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
            print(f"DEBUG: Concatenating {len(clips)} clips...")
            final_video = concatenate_videoclips(clips, method="compose")
            print("DEBUG: Concatenation successful.")
            
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
                
                print("DEBUG: Audio mixing successful.")
                final_video = final_video.set_audio(final_audio)

            print(f"DEBUG: Writing final video to {output_path}...")
            final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", temp_audiofile="temp_audio.m4a", threads=4)
            print("DEBUG: Write successful.")
            return True
        return False
