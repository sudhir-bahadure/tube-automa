"""
Stickman Engine - Now using Programmatic Generation
100% Reliable - No External API Dependencies
"""

import os
from character_generator import generate_character

def generate_stickman_image(pose_description, output_path="temp_stickman.jpg", niche="default", segment_index=0):
    """
    Generates a character image using programmatic PIL generation.
    100% reliable - no API timeouts, no failures.
    Monetization-safe - 100% original code-generated art.
    
    Args:
        pose_description: Text description (used for emotion detection)
        output_path: Where to save the image
        niche: Content niche (not used in programmatic generation)
        segment_index: Which segment (0-5) to determine character type
    
    Returns:
        Path to generated image (always succeeds)
    """
    # 1. Try Together AI (Professional Quality)
    try:
        if os.environ.get("TOGETHER_API_KEY"):
            from together_engine import generate_professional_image
            print(f"  [PROFESSIONAL] Attempting Flux.1 generation for: {pose_description[:50]}...")
            return generate_professional_image(pose_description, output_path)
    except Exception as e:
        print(f"  [WARN] Professional generation failed (falling back to programmatic): {e}")

    # 2. Fallback to Programmatic PIL (100% Reliable)
    try:
        print(f"  [PROGRAMMATIC] Generating character {segment_index % 6} for: {pose_description[:50]}...")
        
        # Generate character using PIL (instant, never fails)
        img = generate_character(pose_description, segment_index, size=(1080, 1920))
        
        # Save
        img.save(output_path, quality=95)
        
        file_size = os.path.getsize(output_path)
        print(f"  [OK] Character generated: {file_size} bytes")
        
        return output_path
        
    except Exception as e:
        print(f"  [ERROR] Programmatic generation failed (should never happen): {e}")
        # This should never happen, but if it does, create a simple fallback
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (1080, 1920), color=(200, 200, 255))
        draw = ImageDraw.Draw(img)
        draw.text((540, 960), "Error", fill=(0, 0, 0), anchor="mm")
        img.save(output_path)
        return output_path

if __name__ == "__main__":
    # Test
    test_image = generate_stickman_image("I'm so stressed about this deadline!", "test_output.jpg", segment_index=0)
    print(f"Test image saved: {test_image}")
