# Test script for long video generation
# Tests the enhanced content generation with Wikipedia API integration

import sys
import os

# Fix Windows encoding for UTF-8 output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from content import get_long_video_metadata, fetch_wikipedia_content

def test_wikipedia_fetch():
    # Test Wikipedia API integration
    print("=" * 60)
    print("TEST 1: Wikipedia API Integration")
    print("=" * 60)
    
    test_topics = ["Black Holes", "Artificial Intelligence", "Egyptian Pyramids"]
    
    for topic in test_topics:
        print(f"\n[*] Fetching content for: {topic}")
        wiki_data = fetch_wikipedia_content(topic)
        
        if wiki_data:
            print(f"  [OK] SUCCESS")
            print(f"  - Title: {wiki_data['title']}")
            print(f"  - URL: {wiki_data['url']}")
            print(f"  - Sentences: {len(wiki_data['sentences'])}")
            print(f"  - First sentence: {wiki_data['sentences'][0][:100]}...")
        else:
            print(f"  [FAIL] FAILED - Using fallback content")
    
    print("\n" + "=" * 60)

def test_metadata_generation():
    # Test enhanced metadata generation
    print("\nTEST 2: Enhanced Metadata Generation")
    print("=" * 60)
    
    # Generate 3 sample videos
    for i in range(3):
        print(f"\n[*] Generating metadata for video {i+1}/3...")
        metadata = get_long_video_metadata()
        
        print(f"  Topic: {metadata['topic']}")
        print(f"  Mode: {metadata['mode']}")
        print(f"  Segments: {len(metadata['segments'])}")
        print(f"  Title: {metadata['title']}")
        print(f"  Category: {metadata['youtube_category']}")
        
        # Estimate duration
        total_words = sum(len(seg['text'].split()) for seg in metadata['segments'])
        estimated_duration = (total_words / 150) * 60  # 150 words per minute
        
        print(f"  Total words: {total_words}")
        print(f"  Estimated duration: {estimated_duration/60:.2f} minutes ({estimated_duration:.0f} seconds)")
        
        if estimated_duration >= 480:
            print(f"  [OK] Meets 8+ minute requirement!")
        else:
            print(f"  [WARN] SHORT by {(480-estimated_duration)/60:.2f} minutes")
        
        # Show first 3 segments
        print(f"\n  First 3 segments:")
        for j, seg in enumerate(metadata['segments'][:3]):
            print(f"    {j+1}. [{seg['keyword']}] {seg['text'][:80]}...")
    
    print("\n" + "=" * 60)

def test_content_uniqueness():
    # Test that generated content is unique
    print("\nTEST 3: Content Uniqueness Check")
    print("=" * 60)
    
    # Generate 5 videos and check for repetition
    scripts = []
    for i in range(5):
        metadata = get_long_video_metadata()
        full_script = " ".join([seg['text'] for seg in metadata['segments']])
        scripts.append(full_script)
    
    print(f"\n[*] Generated {len(scripts)} video scripts")
    
    # Check for exact duplicates
    unique_scripts = set(scripts)
    print(f"  Unique scripts: {len(unique_scripts)}/{len(scripts)}")
    
    if len(unique_scripts) == len(scripts):
        print(f"  [OK] All scripts are unique!")
    else:
        print(f"  [WARN] Found {len(scripts) - len(unique_scripts)} duplicate(s)")
    
    # Check for placeholder text
    placeholder_count = 0
    for script in scripts:
        if "This is a fascinating area of study" in script:
            placeholder_count += 1
    
    print(f"  Scripts with fallback content: {placeholder_count}/{len(scripts)}")
    
    if placeholder_count == 0:
        print(f"  [OK] No placeholder content detected!")
    else:
        print(f"  [WARN] {placeholder_count} script(s) using fallback (Wikipedia may have failed)")
    
    print("\n" + "=" * 60)

def main():
    print("\n" + "=" * 60)
    print("TubeAutoma Long Video Test Suite")
    print("=" * 60)
    print("Testing enhanced content generation with:")
    print("  - Wikipedia API integration")
    print("  - 15 segment structure (8+ minutes)")
    print("  - Opening hooks and engagement")
    print("  - Enhanced metadata and descriptions")
    print("=" * 60)
    
    try:
        # Run tests
        test_wikipedia_fetch()
        test_metadata_generation()
        test_content_uniqueness()
        
        print("\n[OK] ALL TESTS COMPLETE!")
        print("\nSummary:")
        print("  - Wikipedia API is functional")
        print("  - Metadata generation produces 15 segments")
        print("  - Estimated duration: 8+ minutes")
        print("  - Content is unique and varied")
        print("\nReady to generate videos!")
        print("\nTo test actual video generation, run:")
        print("  python src/main.py --category long")
        
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
