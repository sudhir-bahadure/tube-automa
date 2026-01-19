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
    """
    api_key = os.environ.get("GEMINI_VISUAL_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_VISUAL_KEY or GEMINI_API_KEY")
        
    # Configure GenAI
    genai.configure(api_key=api_key)
    
    # Enhanced prompt for professional vector style
    enhanced_prompt = (
        f"professional 2d vector art, minimalist high quality stickman, {prompt}, "
        "white background, clean lines, expressive, 8k resolution, masterpiece"
    )
    
    print(f"  [GEMINI] Generating professional image: {prompt[:50]}...")
    
    try:
        # Initialize Imagen model
        # Try specific Imagen 3 model, fallback to general if needed
        model = genai.ImageGenerationModel("imagen-3.0-generate-001")
        
        response = model.generate_images(
            prompt=enhanced_prompt,
            number_of_images=1,
            aspect_ratio="9:16", # Perfect for Shorts
            safety_filter_level="block_only_high",
            person_generation="allow_adult" 
        )
        
        if not response.images:
             raise Exception("No images returned from Gemini API")
             
        # Save image
        response.images[0].save(output_path)
            
        print(f"  [SUCCESS] Professional image saved to {output_path}")
        return output_path
        
    except Exception as e:
        print(f"  [ERROR] Gemini generation failed: {e}")
        raise e
