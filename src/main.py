import argparse
import os
import warnings
import PIL.Image

# Monkeypatch Pillow 10+ ANTIALIAS for MoviePy 1.0.3 compatibility
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

# Suppress Pytrends/Pandas FutureWarnings to keep logs clean
warnings.simplefilter(action='ignore', category=FutureWarning)
from content import get_fact, get_meme_metadata, get_video_metadata, get_long_video_metadata
from generator import create_video
from youtube_uploader import upload_video
from telegram_bot import upload_to_telegram
from thumbnail import create_thumbnail
from moviepy.editor import VideoFileClip

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="fact", help="Video Category: fact, meme, or long")
    parser.add_argument("--long", action="store_true", help="Generate 8-10 minute long video")
    parser.add_argument("--clone", action="store_true", help="Use voice cloning for curiosity shorts")
    parser.add_argument("--avatar", action="store_true", help="Enable AI Hybrid Avatar intro/outro")
    parser.add_argument("--tweak", default=None, help="Custom prompt tweak for AI generation")
    args = parser.parse_args()
    
    print(f"[*] TubeAutoma Starting in [{args.category.upper()}] mode...")
    
    # 1. Fetch Content
    if args.long or args.category == "long":
        metadata = get_long_video_metadata(tweak=args.tweak)
        if metadata: metadata['orientation'] = 'landscape'
    elif args.category == "meme":
        metadata = get_meme_metadata(tweak=args.tweak)
        if metadata: metadata['orientation'] = 'vertical'
    else:
        metadata = get_video_metadata(tweak=args.tweak)
        if metadata: metadata['orientation'] = 'vertical'
        
    if metadata is None:
        print("[!] Error: No metadata generated. Exiting...")
        return
        
    if args.clone:
        metadata['voice'] = "cloned"
        
    if args.avatar:
        metadata['use_avatar'] = True
        
    print(f"Topic: {metadata['title']}")
    
    # Ensure description and tags exist
    if 'description' not in metadata:
        metadata['description'] = f"{metadata['title']}\n\n#shorts #facts #trending"
    
    if 'tags' not in metadata:
        metadata['tags'] = "#shorts #facts #trending"
    
    # 2. Generate Video
    # Get Pexels Key from Environment (Secrets)
    pexels_key = os.environ.get("PEXELS_API_KEY") 
    
    output_file = f"viral_{args.category}.mp4"
    
    # Avatar logic removed

    # Pass entire metadata object to generator now
    final_video_path = create_video(metadata, output_file, pexels_key)
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    video_path_final = final_video_path
    
    # 3. Upload to YouTube (Primary)
    youtube_id = None
    try:
        # Generate Thumbnail (Phase 2)
        thumbnail_path = None
        try:
            print("[*] Generating Thumbnail...")
            # Extract frame
            thumb_bg = "temp_thumb_bg.jpg"
            with VideoFileClip(final_video_path) as clip:
                clip.save_frame(thumb_bg, t=min(clip.duration/2, 5.0)) # Frame at 5s or mid
            
            # Create Thumbnail
            thumb_text = metadata['title'].split(':')[0][:20] # Short text
            if len(thumb_text) < 5: thumb_text = "WATCH THIS"
            
            thumbnail_path = create_thumbnail(thumb_bg, thumb_text, "final_thumbnail.jpg")
        except Exception as e:
            print(f"[WARN] Thumbnail generation failed: {e}")

        # 3. Upload to YouTube
        print("Uploading to YouTube...")
        youtube_id = upload_video(final_video_path, metadata['title'], metadata['description'], metadata['tags'], metadata.get('youtube_category', '27'), thumbnail_path)
    except Exception as e:
        print(f"YouTube Upload Module Error: {e}")

    # 4. Delivery / Notification to Telegram
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if os.path.exists(final_video_path):
        caption = f"{metadata['title']}\n\n{metadata['tags']}"
        if youtube_id:
            caption += f"\n\n✅ Uploaded to YouTube: https://youtu.be/{youtube_id}"
        else:
            caption += "\n\n⚠️ YouTube Upload Failed (Check Logs)"
            
        upload_to_telegram(final_video_path, caption, bot_token, chat_id)
        
        # Cleanup
        os.remove(final_video_path)
    else:
        print("Error: Video generation failed.")

if __name__ == "__main__":
    main()
