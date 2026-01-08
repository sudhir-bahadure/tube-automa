import os
import google.generativeai as genai
import json

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[FAIL] GEMINI_API_KEY not found in environment.")
        return

    print(f"[*] Testing Gemini API with key: {api_key[:10]}...")
    
    try:
        genai.configure(api_key=api_key)
        
        print("[*] Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
        
        # Trying the literal 'latest' alias from the list
        model = genai.GenerativeModel('gemini-flash-latest')
        print(f"[*] Trying model: gemini-flash-latest")
        
        prompt = "Respond with a JSON object containing a 'status' field set to 'success' and a 'message' field saying 'Gemini is working!'"
        response = model.generate_content(prompt)
        
        print(f"[*] Raw Response: {response.text}")
        
        # Simple cleanup for JSON
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(text)
        if data.get("status") == "success":
            print("[OK] Gemini Connection Successful!")
            return True
        else:
            print(f"[FAIL] Unexpected JSON structure: {data}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Gemini Connection Error: {e}")
        return False

if __name__ == "__main__":
    test_gemini()
