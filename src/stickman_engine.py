"""
Stickman Engine - Now using Gemini Visuals (Imagen 3) for Professional Quality
"""

import os
from character_generator import generate_character

def generate_stickman_image(pose_description, output_path, niche="default", segment_index=0):
    """
    Generates a stickman image.
    Meme Niche -> Uses Gemini Visuals (Imagen 3) exclusively for high quality.
    """
    try:
        # Check for Gemini Key
        if os.environ.get("GEMINI_VISUAL_KEY") or os.environ.get("GEMINI_API_KEY"):
            try:
                from gemini_visual_engine import generate_gemini_image
                print(f"  [PROFESSIONAL] Generating High-Quality Visual for: {pose_description[:50]}...")
                
                # Enhance prompt for "Dynamic Movement" feel
                enhanced_prompt = f"minimalist stick figure drawing, {pose_description}, expressive face, dynamic action pose, white background, thick rough lines, hand-drawn aesthetic"
                
                return generate_gemini_image(enhanced_prompt, output_path)
            except ImportError:
                print("  [WARN] gemini_visual_engine not found, falling back.")
            except Exception as e:
                 print(f"  [WARN] Gemini Visuals failed: {e}")

        # Fallback to Programmatic PIL (Reliable)
        print("  [FALLBACK] Using basic PIL engine")
        img = generate_character(pose_description, segment_index, size=(1080, 1920))
        img.save(output_path, quality=95)
        return output_path
            
    except Exception as e:
        print(f"  [CRITICAL ERROR] Visual Generation Failed: {e}")
        # Last ditch: Error placeholder
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (1080, 1920), color=(200, 200, 255))
        draw = ImageDraw.Draw(img)
        draw.text((540, 960), "Error", fill=(0, 0, 0), anchor="mm")
        img.save(output_path)
        return output_path

if __name__ == "__main__":
    # Test
    generate_stickman_image("Test pose", "test_stickman.jpg", "meme", 0)
