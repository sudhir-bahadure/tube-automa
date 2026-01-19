"""
Gemini Visual Engine - Professional Visuals (Imagen 3)
Uses Google's SOTA Image Generation model for high-quality results.
"""

import os
import google.generativeai as genai
from PIL import Image
import io

def generate_gemini_image(prompt, output_path):
    """
    Generates a professional image using Google Gemini (Imagen 3).
    Attempts SDK first, then falls back to robust REST API.
    """
    import requests
    import json
    
    api_key = os.environ.get("GEMINI_MEME_KEY") or os.environ.get("GEMINI_VISUAL_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_MEME_KEY or equivalent")

    enhanced_prompt = (
        f"professional 2d vector art, minimalist high quality stickman, {prompt}, "
        "white background, clean lines, expressive, 8k resolution, masterpiece"
    )
    
    print(f"  [GEMINI] Generating professional image: {prompt[:50]}...")
    
    # METHOD 1: Try SDK (if available)
    try:
        if hasattr(genai, "ImageGenerationModel"):
            model = genai.ImageGenerationModel("imagen-4.0-fast-generate-001")
            response = model.generate_images(
                prompt=enhanced_prompt,
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_only_high",
                person_generation="allow_adult" 
            )
            if response.images:
                response.images[0].save(output_path)
                print(f"  [SUCCESS] Image saved (SDK) to {output_path}")
                return output_path
    except Exception as e:
        print(f"  [WARN] SDK Generation failed ({e}), switching to REST API...")

    # METHOD 2: Direct REST API (Robust Fallback)
    try:
        # Endpoint for Imagen 4 on Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-fast-generate-001:predict?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Correct Payload for :predict endpoint
        # Structure: {"instances": [{"prompt": "..."}], "parameters": {"sampleCount": 1, ...}}
        data = {
            "instances": [
                {
                    "prompt": enhanced_prompt
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "9:16",
                "safetyFilterLevel": "block_only_high",
                "personGeneration": "allow_adult"
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # Parse result which has "predictions": [{"bytesBase64Encoded": "..."}] or similar
            if "predictions" in result:
                import base64
                # Vertex/Gemini predict response often has bytesBase64Encoded
                # Let's handle both common formats just in case
                img_b64 = result["predictions"][0].get("bytesBase64Encoded") or result["predictions"][0].get("image64") or result["predictions"][0].get("mimeType") # Check struct
                
                # Careful inspection of response structure might be needed, but usually it's bytesBase64Encoded
                if not img_b64:
                     # Fallback check if it's direct string
                     img_b64 = result["predictions"][0]
                     if isinstance(img_b64, dict):
                         img_b64 = img_b64.get("bytesBase64Encoded")
                
                if img_b64:
                    img_data = base64.b64decode(img_b64)
                    with open(output_path, "wb") as f:
                        f.write(img_data)
                    print(f"  [SUCCESS] Image saved (REST) to {output_path}")
                    return output_path
            
            print(f"  [ERROR] REST Response missing predictions: {result}")
        else:
            print(f"  [ERROR] REST API Failed {response.status_code}: {response.text}")

    except Exception as e:
        print(f"  [ERROR] All Gemini generation methods failed: {e}")
        
    raise Exception("Imagen 3 Generation Failed")
