"""
Together AI Engine - Professional Visuals (Flux.1)
"""

import os
import requests
import base64
import time

def generate_professional_image(prompt, output_path, width=1080, height=1920):
    """
    Generates a professional image using Together AI (Flux.1-schnell).
    """
    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        raise ValueError("Missing TOGETHER_API_KEY environment variable")

    url = "https://api.together.xyz/v1/images/generations"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Enhanced prompt for Flux.1 to ensure professional style
    enhanced_prompt = (
        f"{prompt}, professional 2d vector art, masterpiece, high quality, "
        "minimalist, clean lines, white background, cinematic lighting, 8k, "
        "expressive, trending on artstation"
    )

    payload = {
        "model": "black-forest-labs/FLUX.1-schnell",
        "prompt": enhanced_prompt,
        "width": width,
        "height": height,
        "steps": 4, # Flux.1-schnell is fast (4 steps is standard)
        "n": 1,
        "response_format": "b64_json" 
    }

    print(f"  [TOGETHER AI] Generating professional image: {prompt[:50]}...")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")
            
        data = response.json()
        
        if "data" not in data or not data["data"]:
             raise Exception("No image data received from Together AI")
             
        # Decode base64 image
        b64_data = data["data"][0]["b64_json"]
        img_bytes = base64.b64decode(b64_data)
        
        with open(output_path, "wb") as f:
            f.write(img_bytes)
            
        print(f"  [SUCCESS] Professional image saved to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"  [ERROR] Together AI generation failed: {e}")
        raise e
