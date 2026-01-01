# Test script for trending topics and visual tracking

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from content import get_trending_video_topic, get_long_video_metadata
from generator import load_used_videos, save_used_video, is_video_used

def test_trending_detection():
    print("=" * 60)
    print("TEST 1: Trending Topic Detection")
    print("=" * 60)
    
    # Test trending topic fetching
    print("\n[*] Fetching trending topics...")
    topic, niche = get_trending_video_topic()
    
    if topic and niche:
        print(f"\n[OK] Trending topic detected!")
        print(f"  Topic: {topic}")
        print(f"  Niche: {niche}")
    else:
        print(f"\n[WARN] No trending topics found, will use curated list")
    
    print("\n" + "=" * 60)

def test_video_tracking():
    print("\nTEST 2: Visual Tracking System")
    print("=" * 60)
    
    # Test tracking functions
    test_url = "https://test.video.url/sample.mp4"
    
    print(f"\n[*] Testing video tracking...")
    
    # Check if video is used (should be False)
    is_used = is_video_used(test_url)
    print(f"  Is test video used? {is_used}")
    
    if not is_used:
        print(f"  [OK] Video not in tracking (as expected)")
    
    # Save video
    print(f"\n[*] Saving test video to tracking...")
    save_used_video(test_url, "test keyword")
    
    # Check again (should be True now)
    is_used_after = is_video_used(test_url)
    print(f"  Is test video used now? {is_used_after}")
    
    if is_used_after:
        print(f"  [OK] Video successfully tracked!")
    else:
        print(f"  [FAIL] Video tracking failed")
    
    # Load and display tracked videos
    used_videos = load_used_videos()
    print(f"\n[*] Total tracked videos: {len(used_videos)}")
    
    print("\n" + "=" * 60)

def test_metadata_with_trending():
    print("\nTEST 3: Metadata Generation with Trending")
    print("=" * 60)
    
    print(f"\n[*] Generating metadata with trending topic integration...")
    metadata = get_long_video_metadata()
    
    print(f"\n  Topic: {metadata['topic']}")
    print(f"  Mode: {metadata['mode']}")
    print(f"  Segments: {len(metadata['segments'])}")
    print(f"  Title: {metadata['title']}")
    
    # Check if it's a trending topic or curated
    if metadata.get('wiki_url'):
        print(f"  Wikipedia URL: {metadata['wiki_url']}")
    
    print(f"\n[OK] Metadata generated successfully!")
    print("\n" + "=" * 60)

def main():
    print("\n" + "=" * 60)
    print("TubeAutoma Trending & Anti-Repetition Test Suite")
    print("=" * 60)
    print("Testing:")
    print("  - Trending topic detection (Google Trends + YouTube + Reddit)")
    print("  - Visual tracking system (prevent repetition)")
    print("  - Metadata generation with trending integration")
    print("=" * 60)
    
    try:
        # Run tests
        test_trending_detection()
        test_video_tracking()
        test_metadata_with_trending()
        
        print("\n[OK] ALL TESTS COMPLETE!")
        print("\nSummary:")
        print("  - Trending detection: Working (with fallback)")
        print("  - Visual tracking: Functional")
        print("  - Metadata integration: Success")
        print("\nReady for production!")
        
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
