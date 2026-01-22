import argparse
import asyncio
import os
import sys
from src.utils import setup_logging, ensure_dir_exists
from src.llm_wrapper import LLMWrapper
from src.voice_engine import VoiceEngine
from src.asset_manager import AssetManager
from src.video_editor import VideoEditor
from src.youtube_uploader import YouTubeUploader

logger = setup_logging()

async def main():
    parser = argparse.ArgumentParser(description="Media Generation Engine")
    parser.add_argument("--dry-run", action="store_true", help="Generate video but do not upload")
    parser.add_argument("--topic", type=str, help="Specific topic to generate")
    parser.add_argument("--type", type=str, choices=["long", "short"], default="long", help="Type of video to generate")
    parser.add_argument("--style", type=str, choices=["noir", "stickman"], default="noir", help="Visual style of the video")
    parser.add_argument("--schedule-for", type=str, choices=["morning", "afternoon", "evening", "now"], default="now", help="Time slot for scheduling (US ET)")
    args = parser.parse_args()

    logger.info(f"Starting Media Automation in {args.style} style...")
    ensure_dir_exists("temp")
    ensure_dir_exists("output")

    # 1. Generate Content
    llm = LLMWrapper()
    voice = VoiceEngine()
    
    from src.trends import TrendEngine
    trend_engine = TrendEngine()
    
    # Select Topic
    title = args.topic
    if not title:
        # Smart Topic Selection: Fetch view counts of last 10 videos
        try:
            uploader_temp = YouTubeUploader()
            perf_data = uploader_temp.get_recent_performance(limit=10)
        except:
            perf_data = None
        
        title = trend_engine.get_viral_topic(llm, performance_context=perf_data)
        if not title:
            logger.error("Failed to discover a viral topic")
            sys.exit(1)
        logger.info(f"Viral Topic Selected: {title}")
    
    # Override voice for stickman style if requested (Harry-like deep voice)
    if args.style == "stickman":
        voice.voice = "en-GB-RyanNeural" 
        logger.info(f"Using deep voice: {voice.voice}")
    
    logger.info(f"Generating {args.type} script for Title: {title}")
    
    script_data = None
    for attempt in range(2):
        if args.style == "stickman":
             script_data = llm.generate_conversational_script(title, type=args.type)
        elif args.type == "long":
            script_data = llm.generate_psychology_script(title)
        else:
            # Fallback for noir style shorts
            script_data = llm.generate_conversational_script(title, type="short")
            
        if script_data:
            break
        logger.warning(f"Script generation attempt {attempt+1} failed. Retrying...")

    if not script_data:
        logger.error(f"Failed to generate {args.type} script after 2 attempts.")
        sys.exit(1)

    logger.info(f"Title: {script_data.get('title')}")
    if script_data.get('deduced_angle'):
        logger.info(f"Deduced Angle: {script_data.get('deduced_angle')}")
    
    # 2. Process Scenes
    asset_mgr = AssetManager()
    processed_scenes = []

    for i, scene in enumerate(script_data['scenes']):
        logger.info(f"Processing Scene {i+1}...")
        
        # Audio
        audio_path = f"temp/audio_{i}.mp3"
        mood = scene.get('audio_mood', 'neutral')
        await voice.generate_audio(scene['text'], audio_path, mood=mood)
        
        # Visuals
        # Use landscape for long-form, portrait for shorts
        orientation = "landscape" if args.type == "long" else "portrait"
        
        # Save visuals in persistent assets folder for tracking
        ensure_dir_exists("assets/visuals")
        video_path = f"assets/visuals/visual_{i}.jpg"
        
        prompt = scene.get('visual_prompt', scene.get('text'))
        logger.info(f"Generating Image with prompt: {prompt}")
        
        asset_mgr.generate_image(prompt, video_path, orientation=orientation)
        
        processed_scenes.append({
            'audio_path': audio_path,
            'video_path': video_path,
            'text': scene['text'],
            'is_punchline': scene.get('is_punchline', False)
        })

    # 3. Create Video
    editor = VideoEditor()
    output_file = f"output/final_{args.type}.mp4"
    logger.info("Rendering video...")
    is_short = (args.type == "short")
    
    success = editor.create_video(processed_scenes, output_file, is_short=is_short, style=args.style)
    
    if success:
        logger.info(f"Video generated successfully: {output_file}")

        # Prepare SEO Metadata
        video_title = script_data.get('title', args.topic)
        seo_description = script_data.get('description', f"{video_title}")
        if args.type == "long" and 'chapters' in script_data:
            seo_description += "\n\nChapters:\n" + "\n".join(script_data['chapters'])
        
        seo_tags = script_data.get('tags', ['Viral', 'Trending'])
        
        # Preparation for Scheduling
        from datetime import datetime, timedelta
        
        # Calculate publish time based on time slot
        if args.schedule_for == "morning":
            # 10:00 AM ET = 3:00 PM UTC (15:00)
            target_hour_utc = 15
        elif args.schedule_for == "afternoon":
            # 2:00 PM ET = 7:00 PM UTC (19:00)
            target_hour_utc = 19
        elif args.schedule_for == "evening":
            # 6:00 PM ET = 11:00 PM UTC (23:00)
            target_hour_utc = 23
        else:
            # Default: 12 hours from now
            schedule_date = datetime.utcnow() + timedelta(hours=12)
            publish_at = schedule_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            target_hour_utc = None
        
        if target_hour_utc is not None:
            # Schedule for today if the hour hasn't passed, otherwise tomorrow
            now = datetime.utcnow()
            schedule_date = now.replace(hour=target_hour_utc, minute=0, second=0, microsecond=0)
            if now.hour >= target_hour_utc:
                schedule_date += timedelta(days=1)
            publish_at = schedule_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            logger.info(f"Scheduling video for {args.schedule_for} slot: {publish_at}")

        if not args.dry_run:
            # 4. Upload to YouTube
            logger.info("Starting Upload Process...")
            try:
                uploader = YouTubeUploader()
                
                # Generate Thumbnail
                ensure_dir_exists("assets/thumbnails")
                thumbnail_path = f"assets/thumbnails/thumb_{args.type}.jpg"
                logger.info(f"Generating Thumbnail for {video_title}...")
                asset_mgr.generate_thumbnail(video_title, thumbnail_path)
                
                
                # Determine category based on style
                # Category 23 = Comedy (for memes/stickman)
                # Category 27 = Education (for psychology/noir)
                category_id = "23" if args.style == "stickman" else "27"
                
                video_id = uploader.upload_video(
                    output_file, 
                    video_title, 
                    seo_description, 
                    tags=seo_tags,
                    publish_at=publish_at,
                    category_id=category_id,
                    altered_content=False  # Not altered/synthetic content
                )

                if video_id and os.path.exists(thumbnail_path):
                    uploader.set_thumbnail(video_id, thumbnail_path)
                    
                    # Add and Pin Engagement Comment
                    import time
                    import random
                    prompts = [
                        f"Who else relates to this? Comment 'ME' below! 👇",
                        f"How was the video? Comment 'Ready' if you reached the end! 👇",
                        f"Did you know about this? Let's discuss in the comments! 💬",
                        f"Should I do more videos about '{title}'? Let me know! 👇"
                    ]
                    comment_text = random.choice(prompts)
                    
                    logger.info("Waiting 15s for video processing before commenting...")
                    time.sleep(15)
                    
                    comment_id = None
                    for c_attempt in range(3):
                        logger.info(f"Attempting to add engagement comment (Attempt {c_attempt+1})...")
                        comment_id = uploader.add_comment(video_id, comment_text)
                        if comment_id:
                            break
                        logger.warning(f"Comment attempt {c_attempt+1} failed. Target: {video_id}. Retrying in 10s...")
                        time.sleep(10)
                        
                    if comment_id:
                        uploader.pin_comment(comment_id)
                    else:
                        logger.error("Failed to add engagement comment after 3 attempts.")
                        
                    logger.info(f"Successfully uploaded, scheduled for {publish_at}, and set thumbnail/comment: https://youtu.be/{video_id}")
                elif video_id:
                    logger.info(f"Successfully uploaded video: https://youtu.be/{video_id}")
            except Exception as e:
                logger.error(f"Upload process failed: {e}")
                sys.exit(1)
    else:
        logger.error("Video generation failed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
