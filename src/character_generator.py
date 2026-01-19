"""
Programmatic Character Generator - 100% Reliable, No External APIs
Generates simple cartoon characters using PIL/ImageDraw primitives.
Monetization-safe: 100% original code-generated art.
"""

from PIL import Image, ImageDraw, ImageFont
import random
import math

# Character type registry
CHARACTER_TYPES = ["stick_figure", "blob", "simple_face", "robot", "ghost", "emoji"]

# Emotion-based color palettes
EMOTION_COLORS = {
    "happy": {"primary": (255, 220, 100), "accent": (255, 180, 50)},
    "sad": {"primary": (100, 150, 255), "accent": (70, 120, 200)},
    "stressed": {"primary": (255, 100, 100), "accent": (220, 70, 70)},
    "excited": {"primary": (255, 150, 255), "accent": (220, 100, 220)},
    "confused": {"primary": (200, 200, 100), "accent": (170, 170, 70)},
    "default": {"primary": (150, 200, 255), "accent": (100, 150, 220)}
}

def get_emotion_from_text(text):
    """Detect emotion from text"""
    text_lower = text.lower()
    if any(word in text_lower for word in ["stress", "anxiety", "panic", "worried"]):
        return "stressed"
    elif any(word in text_lower for word in ["happy", "joy", "excited", "yay"]):
        return "happy"
    elif any(word in text_lower for word in ["sad", "cry", "depressed", "down"]):
        return "sad"
    elif any(word in text_lower for word in ["confused", "what", "huh", "???"]):
        return "confused"
    elif any(word in text_lower for word in ["wow", "omg", "amazing", "!"]):
        return "excited"
    return "default"

def generate_stick_figure(text, size=(1080, 1920), segment_index=0):
    """Generate stick figure character"""
    img = Image.new('RGB', size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    emotion = get_emotion_from_text(text)
    colors = EMOTION_COLORS[emotion]
    
    # Center position
    cx, cy = size[0] // 2, size[1] // 2
    
    # Head
    head_radius = 120
    draw.ellipse([cx-head_radius, cy-300-head_radius, cx+head_radius, cy-300+head_radius], 
                 outline=(0, 0, 0), width=8, fill=colors["primary"])
    
    # Eyes
    eye_y = cy - 320
    if emotion == "stressed":
        # Stressed eyes (X X)
        draw.line([cx-60, eye_y-20, cx-40, eye_y+20], fill=(0, 0, 0), width=6)
        draw.line([cx-60, eye_y+20, cx-40, eye_y-20], fill=(0, 0, 0), width=6)
        draw.line([cx+40, eye_y-20, cx+60, eye_y+20], fill=(0, 0, 0), width=6)
        draw.line([cx+40, eye_y+20, cx+60, eye_y-20], fill=(0, 0, 0), width=6)
    else:
        # Normal eyes (dots)
        draw.ellipse([cx-60, eye_y-15, cx-40, eye_y+15], fill=(0, 0, 0))
        draw.ellipse([cx+40, eye_y-15, cx+60, eye_y+15], fill=(0, 0, 0))
    
    # Mouth
    mouth_y = cy - 260
    if emotion == "happy":
        draw.arc([cx-50, mouth_y-20, cx+50, mouth_y+40], 0, 180, fill=(0, 0, 0), width=6)
    elif emotion == "sad":
        draw.arc([cx-50, mouth_y-40, cx+50, mouth_y+20], 180, 360, fill=(0, 0, 0), width=6)
    else:
        draw.line([cx-50, mouth_y, cx+50, mouth_y], fill=(0, 0, 0), width=6)
    
    # Body
    draw.line([cx, cy-180, cx, cy+100], fill=(0, 0, 0), width=8)
    
    # Arms (different poses based on segment)
    arm_poses = [
        # Pose 0: Arms down
        [(cx, cy-100, cx-100, cy+50), (cx, cy-100, cx+100, cy+50)],
        # Pose 1: Arms up
        [(cx, cy-100, cx-120, cy-150), (cx, cy-100, cx+120, cy-150)],
        # Pose 2: One arm up
        [(cx, cy-100, cx-100, cy+50), (cx, cy-100, cx+120, cy-150)],
    ]
    pose = arm_poses[segment_index % len(arm_poses)]
    draw.line(pose[0], fill=(0, 0, 0), width=8)
    draw.line(pose[1], fill=(0, 0, 0), width=8)
    
    # Legs
    draw.line([cx, cy+100, cx-80, cy+250], fill=(0, 0, 0), width=8)
    draw.line([cx, cy+100, cx+80, cy+250], fill=(0, 0, 0), width=8)
    
    return img

def generate_blob(text, size=(1080, 1920), segment_index=0):
    """Generate blob character"""
    img = Image.new('RGB', size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    emotion = get_emotion_from_text(text)
    colors = EMOTION_COLORS[emotion]
    
    cx, cy = size[0] // 2, size[1] // 2
    
    # Blob body (ellipse)
    blob_width = 300
    blob_height = 350
    draw.ellipse([cx-blob_width, cy-blob_height, cx+blob_width, cy+blob_height], 
                 fill=colors["primary"], outline=(0, 0, 0), width=8)
    
    # Eyes
    eye_y = cy - 100
    eye_size = 40
    draw.ellipse([cx-120, eye_y-eye_size, cx-80, eye_y+eye_size], fill=(0, 0, 0))
    draw.ellipse([cx+80, eye_y-eye_size, cx+120, eye_y+eye_size], fill=(0, 0, 0))
    
    # White eye highlights
    draw.ellipse([cx-110, eye_y-30, cx-95, eye_y-15], fill=(255, 255, 255))
    draw.ellipse([cx+90, eye_y-30, cx+105, eye_y-15], fill=(255, 255, 255))
    
    # Mouth
    mouth_y = cy + 50
    if emotion == "happy":
        draw.arc([cx-100, mouth_y-30, cx+100, mouth_y+70], 0, 180, fill=(0, 0, 0), width=10)
    elif emotion == "sad":
        draw.arc([cx-100, mouth_y-70, cx+100, mouth_y+30], 180, 360, fill=(0, 0, 0), width=10)
    else:
        draw.ellipse([cx-80, mouth_y-20, cx+80, mouth_y+20], fill=(0, 0, 0))
    
    return img

def generate_simple_face(text, size=(1080, 1920), segment_index=0):
    """Generate simple face character"""
    img = Image.new('RGB', size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    emotion = get_emotion_from_text(text)
    colors = EMOTION_COLORS[emotion]
    
    cx, cy = size[0] // 2, size[1] // 2
    
    # Face circle
    face_radius = 300
    draw.ellipse([cx-face_radius, cy-face_radius, cx+face_radius, cy+face_radius], 
                 fill=colors["primary"], outline=(0, 0, 0), width=10)
    
    # Eyes
    eye_y = cy - 80
    if emotion == "stressed":
        # Spiral eyes
        for i in range(3):
            r = 30 + i*15
            draw.ellipse([cx-150-r, eye_y-r, cx-150+r, eye_y+r], outline=(0, 0, 0), width=6)
            draw.ellipse([cx+150-r, eye_y-r, cx+150+r, eye_y+r], outline=(0, 0, 0), width=6)
    else:
        # Normal eyes
        draw.ellipse([cx-180, eye_y-50, cx-120, eye_y+50], fill=(0, 0, 0))
        draw.ellipse([cx+120, eye_y-50, cx+180, eye_y+50], fill=(0, 0, 0))
        # Pupils
        draw.ellipse([cx-160, eye_y-20, cx-140, eye_y+20], fill=(255, 255, 255))
        draw.ellipse([cx+140, eye_y-20, cx+160, eye_y+20], fill=(255, 255, 255))
    
    # Eyebrows
    if emotion == "stressed":
        draw.line([cx-200, eye_y-100, cx-100, eye_y-80], fill=(0, 0, 0), width=12)
        draw.line([cx+100, eye_y-80, cx+200, eye_y-100], fill=(0, 0, 0), width=12)
    
    # Mouth
    mouth_y = cy + 100
    if emotion == "happy":
        draw.arc([cx-150, mouth_y-50, cx+150, mouth_y+100], 0, 180, fill=(0, 0, 0), width=15)
        # Tongue
        draw.ellipse([cx-40, mouth_y+50, cx+40, mouth_y+90], fill=(255, 100, 100))
    elif emotion == "sad":
        draw.arc([cx-150, mouth_y-100, cx+150, mouth_y+50], 180, 360, fill=(0, 0, 0), width=15)
    else:
        draw.ellipse([cx-120, mouth_y-30, cx+120, mouth_y+30], fill=(0, 0, 0))
    
    return img

def generate_robot(text, size=(1080, 1920), segment_index=0):
    """Generate robot character"""
    img = Image.new('RGB', size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    emotion = get_emotion_from_text(text)
    colors = EMOTION_COLORS[emotion]
    
    cx, cy = size[0] // 2, size[1] // 2
    
    # Robot head (rectangle)
    draw.rectangle([cx-180, cy-350, cx+180, cy-150], fill=colors["primary"], outline=(0, 0, 0), width=8)
    
    # Antenna
    draw.line([cx, cy-350, cx, cy-450], fill=(0, 0, 0), width=8)
    draw.ellipse([cx-30, cy-480, cx+30, cy-420], fill=colors["accent"], outline=(0, 0, 0), width=6)
    
    # LED eyes
    eye_y = cy - 270
    draw.rectangle([cx-120, eye_y-30, cx-60, eye_y+30], fill=(0, 255, 255), outline=(0, 0, 0), width=6)
    draw.rectangle([cx+60, eye_y-30, cx+120, eye_y+30], fill=(0, 255, 255), outline=(0, 0, 0), width=6)
    
    # Mouth (LED display)
    mouth_y = cy - 180
    if emotion == "happy":
        # Happy LED pattern
        for i in range(7):
            x = cx - 105 + i*35
            h = 20 + abs(3-i)*10
            draw.rectangle([x, mouth_y-h//2, x+25, mouth_y+h//2], fill=(0, 255, 0))
    else:
        # Neutral LED pattern
        draw.rectangle([cx-120, mouth_y-15, cx+120, mouth_y+15], fill=(255, 255, 0), outline=(0, 0, 0), width=4)
    
    # Body
    draw.rectangle([cx-150, cy-150, cx+150, cy+150], fill=colors["accent"], outline=(0, 0, 0), width=8)
    
    # Control panel
    draw.rectangle([cx-100, cy-50, cx+100, cy+50], fill=(50, 50, 50), outline=(0, 0, 0), width=4)
    for i in range(3):
        for j in range(2):
            draw.ellipse([cx-80+i*60, cy-30+j*40, cx-50+i*60, cy+j*40], fill=(255, 0, 0))
    
    # Arms
    draw.rectangle([cx-200, cy-50, cx-150, cy+50], fill=colors["primary"], outline=(0, 0, 0), width=6)
    draw.rectangle([cx+150, cy-50, cx+200, cy+50], fill=colors["primary"], outline=(0, 0, 0), width=6)
    
    # Legs
    draw.rectangle([cx-100, cy+150, cx-50, cy+300], fill=colors["primary"], outline=(0, 0, 0), width=6)
    draw.rectangle([cx+50, cy+150, cx+100, cy+300], fill=colors["primary"], outline=(0, 0, 0), width=6)
    
    return img

def generate_ghost(text, size=(1080, 1920), segment_index=0):
    """Generate ghost character"""
    img = Image.new('RGB', size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    emotion = get_emotion_from_text(text)
    colors = EMOTION_COLORS[emotion]
    
    cx, cy = size[0] // 2, size[1] // 2
    
    # Ghost body (rounded top, wavy bottom)
    # Top half circle
    draw.pieslice([cx-200, cy-400, cx+200, cy], 0, 180, fill=colors["primary"], outline=(0, 0, 0), width=8)
    
    # Wavy bottom
    wave_points = []
    for i in range(9):
        x = cx - 200 + i * 50
        y = cy + (30 if i % 2 == 0 else -30)
        wave_points.append((x, y))
    wave_points.append((cx+200, cy-400))
    wave_points.append((cx-200, cy-400))
    draw.polygon(wave_points, fill=colors["primary"], outline=(0, 0, 0), width=8)
    
    # Eyes
    eye_y = cy - 250
    draw.ellipse([cx-100, eye_y-50, cx-50, eye_y+50], fill=(0, 0, 0))
    draw.ellipse([cx+50, eye_y-50, cx+100, eye_y+50], fill=(0, 0, 0))
    
    # White highlights
    draw.ellipse([cx-90, eye_y-30, cx-70, eye_y-10], fill=(255, 255, 255))
    draw.ellipse([cx+60, eye_y-30, cx+80, eye_y-10], fill=(255, 255, 255))
    
    # Mouth
    mouth_y = cy - 150
    if emotion == "happy":
        draw.arc([cx-80, mouth_y-20, cx+80, mouth_y+60], 0, 180, fill=(0, 0, 0), width=10)
    else:
        draw.ellipse([cx-60, mouth_y-20, cx+60, mouth_y+20], fill=(0, 0, 0))
    
    return img

def generate_emoji(text, size=(1080, 1920), segment_index=0):
    """Generate emoji-style character"""
    img = Image.new('RGB', size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    emotion = get_emotion_from_text(text)
    colors = EMOTION_COLORS[emotion]
    
    cx, cy = size[0] // 2, size[1] // 2
    
    # Perfect circle face
    face_radius = 320
    draw.ellipse([cx-face_radius, cy-face_radius, cx+face_radius, cy+face_radius], 
                 fill=colors["primary"], outline=(0, 0, 0), width=12)
    
    # Eyes
    eye_y = cy - 100
    eye_size = 60
    draw.ellipse([cx-160, eye_y-eye_size, cx-80, eye_y+eye_size], fill=(0, 0, 0))
    draw.ellipse([cx+80, eye_y-eye_size, cx+160, eye_y+eye_size], fill=(0, 0, 0))
    
    # Mouth
    mouth_y = cy + 80
    if emotion == "happy":
        # Big smile
        draw.arc([cx-180, mouth_y-80, cx+180, mouth_y+120], 0, 180, fill=(0, 0, 0), width=20)
        # Fill smile
        draw.chord([cx-180, mouth_y-80, cx+180, mouth_y+120], 0, 180, fill=(0, 0, 0))
    elif emotion == "stressed":
        # Wavy stressed mouth
        draw.line([cx-150, mouth_y, cx-100, mouth_y-20, cx-50, mouth_y, cx, mouth_y-20, 
                   cx+50, mouth_y, cx+100, mouth_y-20, cx+150, mouth_y], fill=(0, 0, 0), width=15)
    else:
        # Neutral
        draw.ellipse([cx-140, mouth_y-40, cx+140, mouth_y+40], fill=(0, 0, 0))
    
    return img

# Main generation function
def generate_character(text, segment_index=0, size=(1080, 1920)):
    """
    Generate a character based on segment index.
    Rotates through 6 character types for variety.
    """
    generators = [
        generate_stick_figure,
        generate_blob,
        generate_simple_face,
        generate_robot,
        generate_ghost,
        generate_emoji
    ]
    
    generator = generators[segment_index % len(generators)]
    return generator(text, size, segment_index)

if __name__ == "__main__":
    # Test all character types
    test_texts = [
        "I'm so stressed about this deadline",
        "This makes me so happy!",
        "Feeling sad today",
        "What is even happening???",
        "OMG this is amazing!",
        "Just another day"
    ]
    
    for i, text in enumerate(test_texts):
        img = generate_character(text, i)
        img.save(f"test_character_{i}.jpg")
        print(f"Generated character {i}: {CHARACTER_TYPES[i % len(CHARACTER_TYPES)]}")
