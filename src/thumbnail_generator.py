import os
import requests
import random
from PIL import Image, ImageDraw, ImageFont

def download_thumbnail_bg(topic, pexels_key, output_file="thumb_bg.jpg"):
    """Download a high-quality landscape background for the thumbnail"""
    if not pexels_key: return None
    headers = {'Authorization': pexels_key}
    query = f"cinematic {topic} tech"
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=10&orientation=landscape"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            photos = r.json().get('photos', [])
            if photos:
                img_url = random.choice(photos)['src']['landscape']
                res = requests.get(img_url, timeout=10)
                if res.status_code == 200:
                    with open(output_file, 'wb') as f: f.write(res.content)
                    return output_file
    except: pass
    return None

def create_thumbnail(topic, output_path="thumbnail.jpg", pexels_key=None):
    """
    Generate curiosity-driven thumbnail
    Rules: 2-4 words max, high contrast, NO emojis, NO arrows, NO faces
    """
    print(f"[*] Creating curiosity thumbnail...")
    
    # Extract 2-4 word hook from topic
    words = topic.split()[:4]
    
    # Generate curiosity-driven text (2-4 words)
    thumbnail_texts = [
        "THIS SOUNDS IMPOSSIBLE",
        "WAIT FOR IT",
        "MIND BLOWN",
        "SCIENCE EXPLAINS",
        "REALITY CHECK",
        "TRUTH REVEALED",
        "NEVER NOTICED",
        "THINK AGAIN"
    ]
    
    # Use topic if short enough, otherwise use template
    if len(words) <= 4 and len(' '.join(words)) <= 25:
        thumb_text = ' '.join(words).upper()
    else:
        thumb_text = random.choice(thumbnail_texts)
    
    print(f"  [THUMB TEXT] {thumb_text}")
    
    # 1. Background - ABSTRACT ONLY (no faces, no copyrighted content)
    safe_queries = [
        "abstract gradient background",
        "geometric patterns colorful",
        "particle effects dark",
        "light rays abstract",
        "minimal tech background",
        "space nebula colors"
    ]
    
    bg = None
    if pexels_key:
        try:
            headers = {'Authorization': pexels_key}
            query = random.choice(safe_queries)
            url = f"https://api.pexels.com/v1/search?query={query}&per_page=10&orientation=landscape"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                photos = r.json().get('photos', [])
                if photos:
                    img_url = random.choice(photos)['src']['landscape']
                    res = requests.get(img_url, timeout=10)
                    if res.status_code == 200:
                        bg_file = "temp_thumb_bg.jpg"
                        with open(bg_file, 'wb') as f:
                            f.write(res.content)
                        bg = bg_file
        except Exception as e:
            print(f"  [WARN] Background fetch failed: {e}")
    
    # Create base image
    if bg and os.path.exists(bg):
        img = Image.open(bg).convert("RGBA")
    else:
        # High contrast gradient fallback
        img = Image.new("RGBA", (1280, 720), (0, 0, 0, 255))
        draw_temp = ImageDraw.Draw(img)
        for y in range(720):
            color_val = int(20 + (y / 720) * 60)
            draw_temp.rectangle([(0, y), (1280, y+1)], fill=(color_val, 0, color_val + 20, 255))
    
    img = img.resize((1280, 720), Image.Resampling.LANCZOS)
    
    # 2. High contrast overlay
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 1280, 720), fill=(0, 0, 0, 120))  # Dark overlay
    
    # 3. Text setup
    font_paths = [
        "C:\\Windows\\Fonts\\impact.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    
    font_path = None
    for p in font_paths:
        if os.path.exists(p):
            font_path = p
            break
    
    try:
        font_main = ImageFont.truetype(font_path, 140) if font_path else ImageFont.load_default()
    except:
        font_main = ImageFont.load_default()
    
    # 4. Draw text (HIGH CONTRAST - white on dark)
    # Center text
    text_bbox = draw.textbbox((0, 0), thumb_text, font=font_main)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (1280 - text_width) // 2
    y = (720 - text_height) // 2
    
    # Black outline for contrast
    outline_width = 8
    for adj_x in range(-outline_width, outline_width+1):
        for adj_y in range(-outline_width, outline_width+1):
            draw.text((x + adj_x, y + adj_y), thumb_text, font=font_main, fill=(0, 0, 0, 255))
    
    # Main text - bright yellow/white for maximum visibility
    draw.text((x, y), thumb_text, font=font_main, fill=(255, 255, 50, 255))
    
    # 5. Save
    try:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, "JPEG", quality=95)
        print(f"[OK] Thumbnail: {output_path}")
    except Exception as e:
        print(f"[ERROR] Thumbnail save failed: {e}")
    
    # Cleanup
    if bg and os.path.exists(bg):
        os.remove(bg)
    
    return output_path

if __name__ == "__main__":
    create_thumbnail("impossible science", "test_final.jpg")

