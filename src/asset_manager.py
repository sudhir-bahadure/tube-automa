import requests
import os
import hashlib
import math
from .config import Config

class AssetManager:
    def __init__(self):
        # if not Config.PEXELS_API_KEY:
        #     raise ValueError("PEXELS_API_KEY not found")
        self.headers = {"Authorization": Config.PEXELS_API_KEY or ""}
    
    def search_video(self, query, orientation="portrait"):
        """Searches Pexels for a video URL."""
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation={orientation}"
        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()
            if data['videos']:
                # Get the best quality video file link
                video_files = data['videos'][0]['video_files']
                #Sort by quality (width)
                best_video = sorted(video_files, key=lambda x: x['width'], reverse=True)[0]
                return best_video['link']
        except Exception as e:
            print(f"Error searching video for {query}: {e}")
        return None

    def download_file(self, url, output_path, max_retries=3):
        """Downloads a file from a URL with retries and verification."""
        if not url: return False
        
        import time
        from PIL import Image
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, stream=True, timeout=15)
                
                if response.status_code != 200:
                    print(f"  [WARN] Download failed (Status {response.status_code}) for attempt {attempt+1}")
                    # Client/auth/payment responses will not recover by retrying.
                    if response.status_code in (400, 401, 402, 403, 404):
                        break
                    if response.status_code == 429:  # Rate limited
                        time.sleep(5 * (attempt + 1))
                    continue

                # Check Content-Type to avoid saving HTML as Image
                content_type = response.headers.get('Content-Type', '').lower()
                if 'image' not in content_type:
                    print(f"  [WARN] Unexpected content type: {content_type} on attempt {attempt+1}")
                    continue

                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                
                # VERIFICATION: Try to open with PIL
                try:
                    with Image.open(output_path) as img:
                        img.verify() # Verify file integrity
                    return True
                except Exception as verify_err:
                    print(f"  [WARN] Verification failed for {output_path}: {verify_err}")
                    if os.path.exists(output_path):
                        os.remove(output_path)
            
            except Exception as e:
                print(f"  [ERROR] Download attempt {attempt+1} failed for {url}: {e}")
                time.sleep(2)
        
        return False

    def generate_image(
        self, prompt, output_path, orientation="portrait",
        style="psych_stickman", video_type="short", allow_fallback=False
    ):
        """Generate a scene-specific illustration; never silently publish generic fallbacks."""
        import urllib.parse

        if video_type == "long":
            visual_style = (
                "editorial surrealist ink-and-wash illustration, painterly paper texture, "
                "cinematic lighting, layered composition, metaphorical objects, restrained "
                "charcoal and muted accent palette, sophisticated documentary art direction"
            )
        elif style == "psych_stickman":
            visual_style = (
                "original hand-drawn minimalist stick-figure illustration, expressive body "
                "language, scene-specific props, varied camera framing and composition, "
                "clean editorial linework, restrained dark palette with one accent colour"
            )
        elif style == "noir":
            visual_style = (
                "surrealist psychological noir illustration, ink drawing, dramatic shadows, "
                "symbolic composition, cinematic contrast and restrained colour"
            )
        else:
            visual_style = (
                "original clean vector illustration, expressive character acting, "
                "scene-specific props, varied composition and bright but controlled colour"
            )

        # MARROW Psychology production visuals are rendered locally with Pillow.
        # This avoids a third-party image endpoint that can impose credits, rate limits,
        # change access terms, or return HTTP 402 during a scheduled run.
        if style == "psych_stickman":
            print(
                "  [LOCAL VISUALS] Rendering original scene-specific Psychology artwork "
                f"without an external image API: {prompt[:70]}"
            )
            return self.generate_fallback_visual(
                prompt, output_path, orientation, style=style
            )

        enhanced_prompt = (
            f"{prompt}. Art direction: {visual_style}. "
            "Make the scene visually distinct and faithful to the described action. "
            "No text, captions, watermark, logo, QR code, user interface or signature."
        )
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        
        # Dimensions for Pollinations
        if orientation == "portrait":
            width, height = 1080, 1920
        elif orientation == "landscape":
            width, height = 1920, 1080
        else: # Thumbnail
            width, height = 1280, 720
            
        import random
        seed = random.randint(1, 1000000)
        
        # Using specific parameters to avoid logos/text
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&enhance=true&seed={seed}&nofeed=true"
        
        success = self.download_file(url, output_path)
        if not success and (allow_fallback or style == "psych_stickman"):
            if style == "psych_stickman":
                print(
                    "  [OFFLINE] Image provider unavailable; generating an original "
                    f"scene-specific local illustration for: {prompt[:60]}"
                )
            else:
                print(
                    "  [WARN] Image service unavailable; creating a local visual fallback "
                    f"for: {prompt[:50]}"
                )
            success = self.generate_fallback_visual(
                prompt, output_path, orientation, style=style
            )
        elif not success:
            print(
                f"  [ERROR] Scene illustration unavailable; refusing fallback "
                f"for style '{style}': {prompt[:50]}"
            )
        return success

    def generate_fallback_visual(self, prompt, output_path, orientation="portrait", style="psych_stickman"):
        """Render an original, prompt-aware illustration locally with Pillow (no image API)."""
        from PIL import Image, ImageDraw
        import os

        prompt_text = str(prompt or "")
        text = prompt_text.lower()
        digest = hashlib.sha256(prompt_text.encode("utf-8", errors="ignore")).digest()

        if orientation == "portrait":
            width, height = 1080, 1920
        elif orientation == "landscape":
            width, height = 1920, 1080
        else:
            width, height = 1280, 720

        # Stable prompt-derived palette and layout make repeated topics visually varied
        # while remaining deterministic across retries and runner machines.
        accent = (
            120 + digest[0] % 105,
            105 + digest[1] % 105,
            100 + digest[2] % 110,
        )
        accent_soft = tuple(max(0, int(channel * 0.32)) for channel in accent)
        background = (15 + digest[3] % 13, 19 + digest[4] % 15, 28 + digest[5] % 18)
        line = (237, 239, 244)
        muted = (150, 160, 177)
        unit = min(width, height)
        image = Image.new("RGB", (width, height), background)
        draw = ImageDraw.Draw(image)

        # Quiet editorial backdrop: a frame, subtle horizon and prompt-specific geometry.
        margin = int(width * 0.075)
        draw.rounded_rectangle(
            (margin, margin, width - margin, height - margin),
            radius=max(18, int(unit * 0.025)),
            outline=accent_soft,
            width=max(2, int(unit * 0.003)),
        )
        for index in range(5):
            x = int(width * (0.12 + digest[index + 6] / 255 * 0.76))
            y = int(height * (0.10 + digest[index + 11] / 255 * 0.56))
            radius = int(unit * (0.018 + digest[index + 16] / 2550))
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                outline=accent_soft,
                width=max(2, int(unit * 0.002)),
            )

        floor_y = int(height * 0.81)
        draw.line((int(width * 0.10), floor_y, int(width * 0.90), floor_y),
                  fill=(74, 83, 101), width=max(3, int(unit * 0.004)))

        # A consistent character language, with pose selected from the scene direction.
        stressed = any(word in text for word in (
            "panic", "horror", "anxiety", "staring", "worried", "stress", "overwhelmed"
        ))
        raised = any(word in text for word in (
            "illuminated", "spotlight", "surprised", "hands up", "reaching", "pointing"
        ))
        seated = any(word in text for word in ("sitting", "seated", "desk", "conference table"))
        pose = "raised" if raised else ("stressed" if stressed else "open")
        cx = int(width * (0.53 + (digest[21] / 255 - 0.5) * 0.12))
        base_y = floor_y

        def draw_person(person_x, person_base, scale=1.0, color=line, small=False):
            head_r = max(12, int(unit * (0.043 if not small else 0.030) * scale))
            head_x = int(person_x)
            head_y = int(person_base - unit * 0.405 * scale)
            stroke = max(3, int(unit * (0.009 if not small else 0.007) * scale))
            draw.ellipse(
                (head_x - head_r, head_y - head_r, head_x + head_r, head_y + head_r),
                outline=color, width=stroke,
            )
            eye_r = max(2, int(head_r * 0.075))
            eye_y = head_y - int(head_r * 0.04)
            draw.ellipse((head_x - int(head_r * 0.36) - eye_r, eye_y - eye_r,
                          head_x - int(head_r * 0.36) + eye_r, eye_y + eye_r), fill=color)
            draw.ellipse((head_x + int(head_r * 0.36) - eye_r, eye_y - eye_r,
                          head_x + int(head_r * 0.36) + eye_r, eye_y + eye_r), fill=color)
            mouth_y = head_y + int(head_r * 0.36)
            if stressed:
                draw.arc((head_x - int(head_r * 0.28), mouth_y - 2,
                          head_x + int(head_r * 0.28), mouth_y + int(head_r * 0.24)),
                         180, 360, fill=color, width=max(2, stroke // 2))
            else:
                draw.line((head_x - int(head_r * 0.22), mouth_y,
                           head_x + int(head_r * 0.22), mouth_y),
                          fill=color, width=max(2, stroke // 2))

            shoulder_y = head_y + head_r + int(unit * 0.045 * scale)
            body_bottom = int(person_base - unit * 0.135 * scale)
            draw.line((head_x, shoulder_y, head_x, body_bottom), fill=color, width=stroke)
            arm_y = shoulder_y + int((body_bottom - shoulder_y) * 0.16)
            arm_len = int(unit * (0.17 if not small else 0.12) * scale)
            if pose == "raised":
                left_end = (head_x - arm_len, arm_y - int(arm_len * 0.78))
                right_end = (head_x + arm_len, arm_y - int(arm_len * 0.78))
            elif pose == "stressed":
                left_end = (head_x - int(arm_len * 0.48), arm_y - int(arm_len * 0.85))
                right_end = (head_x + int(arm_len * 0.48), arm_y - int(arm_len * 0.85))
            else:
                left_end = (head_x - int(arm_len * 0.72), arm_y + int(arm_len * 0.62))
                right_end = (head_x + int(arm_len * 0.72), arm_y + int(arm_len * 0.62))
            draw.line((head_x, arm_y, *left_end), fill=color, width=stroke)
            draw.line((head_x, arm_y, *right_end), fill=color, width=stroke)
            if seated:
                hip_x = head_x
                hip_y = body_bottom
                draw.line((hip_x, hip_y, hip_x + int(unit * 0.10 * scale),
                           hip_y + int(unit * 0.055 * scale)), fill=color, width=stroke)
                draw.line((hip_x + int(unit * 0.10 * scale), hip_y + int(unit * 0.055 * scale),
                           hip_x + int(unit * 0.20 * scale),
                           hip_y + int(unit * 0.055 * scale)), fill=color, width=stroke)
                draw.line((head_x, hip_y, head_x - int(unit * 0.10 * scale),
                           hip_y + int(unit * 0.055 * scale)), fill=color, width=stroke)
            else:
                leg_len = int(unit * 0.19 * scale)
                leg_spread = int(unit * 0.075 * scale)
                draw.line((head_x, body_bottom, head_x - leg_spread,
                           body_bottom + leg_len), fill=color, width=stroke)
                draw.line((head_x, body_bottom, head_x + leg_spread,
                           body_bottom + leg_len), fill=color, width=stroke)

        # Scene props are selected from actual words in the visual direction.
        # Several can coexist (e.g. a meeting table and the tiny speck being noticed).
        if any(word in text for word in ("spotlight", "illuminated", "cone of light", "beam of light")):
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            beam_top = int(width * (0.48 + digest[22] / 255 * 0.10))
            beam_bottom_left = int(width * 0.31)
            beam_bottom_right = int(width * 0.72)
            overlay_draw.polygon(
                ((beam_top - int(unit * 0.04), int(height * 0.12)),
                 (beam_top + int(unit * 0.04), int(height * 0.12)),
                 (beam_bottom_right, floor_y),
                 (beam_bottom_left, floor_y)),
                fill=(245, 194, 75, 42),
            )
            image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(image)
            lamp_r = int(unit * 0.035)
            draw.ellipse((beam_top - lamp_r, int(height * 0.10) - lamp_r,
                          beam_top + lamp_r, int(height * 0.10) + lamp_r),
                         fill=(245, 194, 75), outline=line, width=max(3, int(unit * 0.004)))

        if any(word in text for word in ("conference table", "meeting", "table", "desk")):
            table_y = int(height * 0.69)
            left, right = int(width * 0.12), int(width * 0.88)
            draw.rounded_rectangle((left, table_y, right, table_y + int(unit * 0.055)),
                                   radius=max(8, int(unit * 0.012)), fill=(45, 55, 73),
                                   outline=accent, width=max(3, int(unit * 0.005)))
            leg_bottom = floor_y
            for x in (int(width * 0.20), int(width * 0.80)):
                draw.line((x, table_y + int(unit * 0.05), x, leg_bottom),
                          fill=muted, width=max(4, int(unit * 0.009)))
            # A small open notebook/laptop makes the table read as a working scene.
            notebook = (int(width * 0.38), table_y - int(unit * 0.085),
                        int(width * 0.53), table_y - int(unit * 0.01))
            draw.rounded_rectangle(notebook, radius=8, fill=background,
                                   outline=accent, width=max(3, int(unit * 0.004)))
            draw.line((notebook[0] + 8, notebook[1] + int(unit * 0.03),
                       notebook[2] - 8, notebook[1] + int(unit * 0.03)),
                      fill=muted, width=max(2, int(unit * 0.003)))

        if any(word in text for word in ("phone", "smartphone", "message", "scroll", "screen", "reels")):
            px = int(width * (0.76 if cx < width * 0.58 else 0.18))
            py = int(height * 0.42)
            pw, ph = int(unit * 0.15), int(unit * 0.29)
            draw.rounded_rectangle((px - pw // 2, py - ph // 2, px + pw // 2, py + ph // 2),
                                   radius=max(12, int(unit * 0.025)), fill=(8, 12, 20),
                                   outline=accent, width=max(4, int(unit * 0.008)))
            draw.rounded_rectangle((px - pw // 2 + int(pw * 0.12),
                                    py - ph // 2 + int(ph * 0.12),
                                    px + pw // 2 - int(pw * 0.12),
                                    py + ph // 2 - int(ph * 0.12)),
                                   radius=8, fill=(36, 48, 67))
            for row in range(3):
                yy = py - int(ph * 0.20) + row * int(ph * 0.13)
                draw.rounded_rectangle((px - int(pw * 0.30), yy,
                                        px + int(pw * 0.27), yy + int(ph * 0.055)),
                                       radius=5, fill=accent if row == 0 else muted)

        if any(word in text for word in ("clock", "time", "deadline", "hour", "minute")):
            clock_x, clock_y = int(width * 0.22), int(height * 0.38)
            radius = int(unit * 0.11)
            draw.ellipse((clock_x - radius, clock_y - radius,
                          clock_x + radius, clock_y + radius),
                         outline=accent, width=max(6, int(unit * 0.009)))
            draw.line((clock_x, clock_y, clock_x, clock_y - int(radius * 0.60)),
                      fill=line, width=max(4, int(unit * 0.009)))
            draw.line((clock_x, clock_y, clock_x + int(radius * 0.52),
                       clock_y + int(radius * 0.20)),
                      fill=line, width=max(4, int(unit * 0.009)))
            draw.ellipse((clock_x - 7, clock_y - 7, clock_x + 7, clock_y + 7), fill=accent)

        if any(word in text for word in ("mirror", "reflection", "reflected")):
            mx, my = int(width * 0.20), int(height * 0.34)
            mw, mh = int(unit * 0.19), int(unit * 0.38)
            draw.rounded_rectangle((mx - mw // 2, my - mh // 2,
                                    mx + mw // 2, my + mh // 2),
                                   radius=max(15, int(unit * 0.035)), fill=(31, 42, 59),
                                   outline=accent, width=max(5, int(unit * 0.009)))
            draw.ellipse((mx - int(mw * 0.22), my - int(mh * 0.31),
                          mx + int(mw * 0.22), my - int(mh * 0.02)),
                         outline=line, width=max(3, int(unit * 0.006)))
            draw.line((mx, my - int(mh * 0.02), mx, my + int(mh * 0.28)),
                      fill=line, width=max(3, int(unit * 0.006)))

        if any(word in text for word in ("paper", "note", "document", "speck", "spot on", "chest")):
            px, py = int(width * 0.21), int(height * 0.62)
            pw, ph = int(unit * 0.16), int(unit * 0.20)
            draw.rounded_rectangle((px - pw // 2, py - ph // 2, px + pw // 2, py + ph // 2),
                                   radius=8, fill=(224, 226, 230), outline=accent,
                                   width=max(4, int(unit * 0.006)))
            for row in range(3):
                yy = py - int(ph * 0.20) + row * int(ph * 0.15)
                draw.line((px - int(pw * 0.28), yy, px + int(pw * 0.28), yy),
                          fill=(92, 101, 117), width=max(2, int(unit * 0.003)))
            if "speck" in text or "spot on" in text:
                sx, sy = int(width * 0.56), int(height * 0.50)
                radius = max(7, int(unit * 0.012))
                draw.ellipse((sx - radius, sy - radius, sx + radius, sy + radius),
                             fill=(245, 194, 75), outline=line,
                             width=max(2, int(unit * 0.003)))

        if any(word in text for word in ("crowd", "audience", "nobody", "everyone", "other people", "people around")):
            for index in range(4):
                other_x = int(width * (0.18 + index * 0.21))
                if abs(other_x - cx) > int(unit * 0.13):
                    draw_person(other_x, int(height * 0.77), scale=0.48,
                                color=muted, small=True)

        if any(word in text for word in ("talking", "conversation", "speaking", "dialogue", "chat")):
            bx, by = int(width * 0.74), int(height * 0.30)
            bw, bh = int(unit * 0.20), int(unit * 0.10)
            draw.rounded_rectangle((bx - bw // 2, by - bh // 2, bx + bw // 2, by + bh // 2),
                                   radius=max(10, int(unit * 0.02)), outline=accent,
                                   width=max(4, int(unit * 0.006)))
            for dot in range(3):
                dx = bx - int(bw * 0.20) + dot * int(bw * 0.20)
                draw.ellipse((dx - 6, by - 6, dx + 6, by + 6), fill=accent)

        if any(word in text for word in ("choice", "decision", "path", "fork", "direction")):
            start_x, start_y = int(width * 0.50), int(height * 0.68)
            draw.line((start_x, start_y, int(width * 0.30), int(height * 0.48)),
                      fill=accent, width=max(5, int(unit * 0.008)))
            draw.line((start_x, start_y, int(width * 0.72), int(height * 0.48)),
                      fill=accent, width=max(5, int(unit * 0.008)))
            for ex, ey in ((int(width * 0.30), int(height * 0.48)),
                           (int(width * 0.72), int(height * 0.48))):
                draw.ellipse((ex - 12, ey - 12, ex + 12, ey + 12), fill=accent)

        if any(word in text for word in ("thought", "thinking", "mind", "idea", "wondering")):
            bx, by = int(width * 0.72), int(height * 0.22)
            radius = int(unit * 0.065)
            draw.ellipse((bx - radius, by - radius, bx + radius, by + radius),
                         outline=accent, width=max(4, int(unit * 0.006)))
            draw.ellipse((bx - int(radius * 0.55), by - int(radius * 0.55),
                          bx + int(radius * 0.55), by + int(radius * 0.55)),
                         outline=accent_soft, width=max(3, int(unit * 0.004)))
            draw.ellipse((bx - int(radius * 1.05), by + int(radius * 0.95),
                          bx - int(radius * 0.85), by + int(radius * 1.15)), fill=accent)
            draw.ellipse((bx - int(radius * 0.60), by + int(radius * 1.35),
                          bx - int(radius * 0.45), by + int(radius * 1.50)), fill=accent)

        if not any(word in text for word in (
            "conference table", "meeting", "table", "desk", "phone", "smartphone",
            "message", "scroll", "screen", "reels", "clock", "time", "deadline",
            "hour", "minute", "mirror", "reflection", "paper", "note", "document",
            "speck", "spot on", "chest", "crowd", "audience", "nobody", "everyone",
            "other people", "people around", "talking", "conversation", "speaking",
            "dialogue", "chat", "choice", "decision", "path", "fork", "direction",
            "thought", "thinking", "mind", "idea", "wondering", "spotlight",
            "illuminated", "cone of light", "beam of light"
        )):
            # Unclassified scenes still get a distinct, prompt-seeded focal prop.
            px, py = int(width * (0.18 + digest[24] / 255 * 0.64)), int(height * 0.50)
            radius = int(unit * (0.075 + digest[25] / 2550))
            draw.rounded_rectangle((px - radius, py - radius, px + radius, py + radius),
                                   radius=max(12, int(radius * 0.20)), outline=accent,
                                   width=max(5, int(unit * 0.008)))
            draw.ellipse((px - int(radius * 0.25), py - int(radius * 0.25),
                          px + int(radius * 0.25), py + int(radius * 0.25)),
                         fill=accent)

        draw_person(cx, base_y, scale=1.0, color=line)
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        image.save(output_path, format="JPEG", quality=91, optimize=True)
        return os.path.isfile(output_path) and os.path.getsize(output_path) > 1000

def generate_thumbnail(self, title, output_path):
        """Create an original 16:9 visual and add a readable, restrained title overlay."""
        from PIL import Image, ImageDraw, ImageFont
        prompt = (
            f"Editorial psychology documentary thumbnail about '{title}', "
            "one strong visual metaphor, a single clear focal subject, cinematic ink wash, "
            "dark charcoal background with one muted accent, generous negative space, "
            "high contrast, no text, no lettering, no logo, no watermark"
        )
        if not self.generate_image(
            prompt, output_path, orientation="thumbnail",
            style="psych_stickman", video_type="long", allow_fallback=True
        ):
            return False

        try:
            image = Image.open(output_path).convert("RGB")
            if image.size != (1280, 720):
                image = image.resize((1280, 720), Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(image, "RGBA")
            # Subtle bottom gradient panel keeps text legible without hiding the artwork.
            panel_top = 470
            for y in range(panel_top, 720):
                alpha = int(190 * ((y - panel_top) / 250))
                draw.line((0, y, 1280, y), fill=(5, 8, 14, alpha))
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf", 62
                )
            except OSError:
                font = ImageFont.load_default()

            words = title.strip().split()
            lines = []
            current = ""
            for word in words:
                candidate = (current + " " + word).strip()
                if len(candidate) > 24 and current:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
                if len(lines) == 2:
                    break
            if current and len(lines) < 2:
                lines.append(current)
            if len(words) > sum(len(line.split()) for line in lines):
                lines[-1] = lines[-1].rstrip(" .,:;") + "…"

            y = 520 if len(lines) == 1 else 490
            for line in lines:
                draw.text((58, y), line, font=font, fill=(255, 255, 255, 255),
                          stroke_width=2, stroke_fill=(0, 0, 0, 210))
                y += 82

            image.save(output_path, format="JPEG", quality=94, optimize=True)
            return os.path.isfile(output_path) and os.path.getsize(output_path) > 5000
        except Exception as exc:
            print(f"Thumbnail composition failed: {exc}")
            return False
