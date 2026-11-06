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
                    if response.status_code == 429: # Rate Limited
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

    def generate_image(self, prompt, output_path, orientation="portrait"):
        """Generates an image using Pollinations.ai (Free) with enhanced styling."""
        import urllib.parse
        
        # Add flavor tags to the prompt to ensure clean, flat 2D visuals (Viral Style)
        # Focus on flat design, clean lines, and minimalist icon style
        enhanced_prompt = f"{prompt}, flat vector art, clean lines, minimalist character icon, sticker style, solid vibrant background, vibrant colors, centered composition, no text, no captions, no watermark, no logo, no qr code, no user interface, no signature"
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
        if not success:
            print(f"  [WARN] Image service unavailable; creating original local fallback for: {prompt[:50]}")
            success = self.generate_fallback_visual(prompt, output_path, orientation)
        return success

    def generate_fallback_visual(self, prompt, output_path, orientation="portrait"):
        """Create an original, license-safe illustrated fallback using Pillow only."""
        from PIL import Image, ImageDraw
        digest = hashlib.sha256(prompt.encode("utf-8", errors="ignore")).digest()
        if orientation == "portrait":
            width, height = 1080, 1920
        elif orientation == "landscape":
            width, height = 1920, 1080
        else:
            width, height = 1280, 720

        accent = (80 + digest[0] % 150, 80 + digest[1] % 150, 100 + digest[2] % 130)
        base = (12 + digest[3] % 24, 16 + digest[4] % 28, 28 + digest[5] % 36)
        image = Image.new("RGBA", (width, height), (*base, 255))
        draw = ImageDraw.Draw(image)

        # Abstract backdrop, unique per prompt.
        for n in range(7):
            x = int(width * (0.12 + ((digest[n] / 255) * 0.76)))
            y = int(height * (0.10 + ((digest[n + 7] / 255) * 0.75)))
            radius = int(min(width, height) * (0.04 + digest[n + 14] / 2550))
            draw.ellipse((x-radius, y-radius, x+radius, y+radius),
                         fill=(*accent, 22), outline=(*accent, 45), width=4)

        cx, head_y = width // 2, int(height * 0.36)
        unit = min(width, height) * 0.12
        line = (235, 238, 245, 255)
        stroke = max(12, int(unit * 0.075))
        head_r = int(unit * 0.23)
        draw.ellipse((cx-head_r, head_y-head_r, cx+head_r, head_y+head_r),
                     outline=line, width=stroke)
        shoulder_y = head_y + int(unit * 0.38)
        hip_y = head_y + int(unit * 1.55)
        draw.line((cx, head_y+head_r, cx, hip_y), fill=line, width=stroke)

        left_angle = (digest[20] / 255) * math.pi
        right_angle = (digest[21] / 255) * math.pi
        arm_len = int(unit * 0.9)
        left_end = (int(cx - math.cos(left_angle) * arm_len),
                    int(shoulder_y - math.sin(left_angle) * arm_len))
        right_end = (int(cx + math.cos(right_angle) * arm_len),
                     int(shoulder_y - math.sin(right_angle) * arm_len))
        draw.line((cx, shoulder_y, *left_end), fill=line, width=stroke)
        draw.line((cx, shoulder_y, *right_end), fill=line, width=stroke)

        leg_spread = int(unit * (0.42 + digest[22] / 700))
        leg_drop = int(unit * (0.95 + digest[23] / 500))
        draw.line((cx, hip_y, cx-leg_spread, hip_y+leg_drop), fill=line, width=stroke)
        draw.line((cx, hip_y, cx+leg_spread, hip_y+leg_drop), fill=line, width=stroke)

        # A simple scene prop makes fallback frames less interchangeable.
        prop_x = int(width * (0.18 + digest[24] / 255 * 0.64))
        prop_y = int(height * (0.68 + digest[25] / 255 * 0.12))
        prop_r = int(unit * 0.22)
        draw.rounded_rectangle((prop_x-prop_r, prop_y-prop_r, prop_x+prop_r, prop_y+prop_r),
                               radius=12, outline=(*accent, 230), width=stroke)
        draw.ellipse((prop_x-7, prop_y-7, prop_x+7, prop_y+7), fill=(*accent, 255))

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        image.convert("RGB").save(output_path, format="JPEG", quality=90, optimize=True)
        return os.path.isfile(output_path) and os.path.getsize(output_path) > 1000

    def generate_thumbnail(self, title, output_path):
        """Generates a high-clickability thumbnail image."""
        prompt = f"Highly evocative, mysterious psychology thumbnail for '{title}', surrealist ink wash, dark moody atmosphere, psychological noir, minimalist, no text, 8k, cinematic"
        return self.generate_image(prompt, output_path, orientation="thumbnail")
