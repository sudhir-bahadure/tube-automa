"""Simple test for fact metadata generation"""
import sys
import os
import io

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock the ypp_script_template module
class MockModule:
    @staticmethod
    def generate_ypp_safe_script(text):
        return text
    
    @staticmethod
    def ensure_minimum_duration(segments):
        return segments

sys.modules['src.ypp_script_template'] = MockModule()

# Now import content
from src import content

def test_fact_metadata():
    print("=" * 60)
    print("Testing Fact Metadata Generation")
    print("=" * 60)
    
    print("\n[*] Generating fact metadata...")
    metadata = content.get_video_metadata()
    
    print(f"\n[OK] Title: {metadata['title']}")
    print(f"[OK] YouTube category: {metadata['youtube_category']}")
    print(f"\n[*] Text Content:")
    print(f"{metadata['text']}")
    
    print(f"\n[*] Description:")
    print(f"{metadata['description'][:200]}...")
    
    # Check for subscribe hook
    expected_hook = "Subscribe to Daily Meme Dose for more!"
    if expected_hook in metadata['text']:
        print(f"\n[SUCCESS] Found subscribe hook in TEXT: '{expected_hook}'")
    else:
        print(f"\n[FAIL] Subscribe hook MISSING from TEXT")
        
    if expected_hook in metadata['description']:
        print(f"[SUCCESS] Found subscribe hook in DESCRIPTION: '{expected_hook}'")
    else:
        print(f"[FAIL] Subscribe hook MISSING from DESCRIPTION")
    
    print("\n" + "=" * 60)
    
    return expected_hook in metadata['text']

if __name__ == "__main__":
    success = test_fact_metadata()
    sys.exit(0 if success else 1)
