import argparse
import asyncio
import os
import sys
import random
from src.utils import setup_logging, ensure_dir_exists
from src.llm_wrapper import LLMWrapper
from src.voice_engine import VoiceEngine
from src.asset_manager import AssetManager
from src.video_editor import VideoEditor
from src.youtube_uploader import YouTubeUploader
from src.music_engine import MusicEngine
from src.quality_gate import validate_script_data, validate_video
from src.research_engine import ResearchEngine

logger = setup_logging()

async def main():
    parser = argparse.ArgumentParser(description="Media Generation Engine")
    parser.add_argument("--dry-run", action="store_true", help="Generate video but do not upload")
    parser.add_argument("--topic", type=str, help="Specific topic to generate")
    parser.add_argument("--type", type=str, choices=["long", "short"], default="long", help="Type of video to generate")
    parser.add_argument("--style", type=str, choices=["noir", "stickman", "psych_stickman"], default="noir", help="Visual style of the video")
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
        except Exception as e:
            if os.getenv("YOUTUBE_EXPECTED_CHANNEL_TITLE"):
                logger.error(f"YouTube destination/authentication check failed; stopping before production: {e}")
                sys.exit(1)
            logger.warning(f"Analytics unavailable; continuing without performance context: {e}")
            perf_data = None
        
        title = trend_engine.get_viral_topic(llm, performance_context=perf_data)
        if not title:
            logger.error("Failed to discover a viral topic")
            sys.exit(1)
        logger.info(f"Viral Topic Selected: {title}")
    
    # Override voice for stickman style if requested (Harry-like deep voice)
    # Also use for psych_stickman if that's desired, or keep Christopher?
    # User didn't ask to change voice ID, just settings. Stickman uses Ryan, Noir uses Christopher.
    # Curiosity workflow uses Christopher. 
    # Let's keep Christopher (default) for psych_stickman unless user specifically requested otherwise.
    # But user wants "humanly" AI narration.
    if args.style == "stickman":
        voice.voice = "en-GB-RyanNeural" 
        logger.info(f"Using deep voice: {voice.voice}")
    
    logger.info(f"Retrieving free scholarly context for: {title}")
    research_data = ResearchEngine().search(title, limit=3)
    research_context = research_data.get("notes", "")

    logger.info(f"Generating {args.type} script for Title: {title}")
    
    script_data = None
    for attempt in range(2):
        if args.style == "stickman":
            if args.type == "short":
                script_data = llm.generate_relatable_comedy_script(title)
            else:
                script_data = llm.generate_conversational_script(title, type=args.type)
        elif args.style == "psych_stickman":
             if args.type == "long":
                 script_data = llm.generate_psychology_script(title, research_context=research_context)
             else:
                 script_data = llm.generate_psychology_stickman_script(title, research_context=research_context)
        elif args.type == "long":
            script_data = llm.generate_psychology_script(title)
        else:
            # Noir style shorts use the specific psychology-short engine
            script_data = llm.generate_psychology_short_script(title)
            
        if script_data:
            break
        logger.warning(f"Script generation attempt {attempt+1} failed. Retrying...")

    if not script_data:
        logger.error(f"Failed to generate {args.type} script after 2 attempts.")
        sys.exit(1)

    try:
        script_check = validate_script_data(script_data, is_short=(args.type == "short"))
        logger.info(f"Script quality gate passed: {script_check}")
    except Exception as e:
        logger.error(f"Script quality gate failed; refusing to render or upload: {e}")
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
        
        # Audio Settings for Psych Stickman
        audio_kwargs = {}
        if args.style == "psych_stickman":
            audio_kwargs = {
                "voice_settings": {"stability": 1.0, "similarity_boost": 0.8},
                "remove_silence": True
            }

        audio_ok = await voice.generate_audio(scene['text'], audio_path, mood=mood, **audio_kwargs)
        if not audio_ok or not os.path.isfile(audio_path) or os.path.getsize(audio_path) < 1000:
            logger.error(f"Voice generation failed for scene {i+1}; refusing to publish a video with missing narration.")
            sys.exit(1)
        
        # Visuals
        # Use landscape for long-form, portrait for shorts
        orientation = "landscape" if args.type == "long" else "portrait"
        
        # Save visuals in persistent assets folder for tracking
        ensure_dir_exists("assets/visuals")
        video_path = f"assets/visuals/visual_{i}.jpg"
        
        prompt = scene.get('visual_prompt', scene.get('text'))
        logger.info(f"Generating Image with prompt: {prompt}")
        
        # Logic to ensure stickman usage for stickman styles even if prompt is generic (though script should provide it)
        # prompt already comes from script.
        
        success = asset_mgr.generate_image(
            prompt, video_path, orientation=orientation,
            style=args.style, video_type=args.type, allow_fallback=False
        )
        if not success:
            logger.error(
                f"Scene {i+1} illustration could not be generated. "
                "Stopping rather than publishing a generic placeholder video."
            )
            sys.exit(1)
        
        processed_scenes.append({
            'audio_path': audio_path,
            'video_path': video_path if success else None,
            'text': scene['text'],
            'is_punchline': scene.get('is_punchline', False)
        })

    # 3. Create Video
    # Select Background Music
    music_mood = script_data.get('music_mood', 'chill')
    bg_music_path, music_credits = None, None
    if os.getenv("MUSIC_ENABLED", "false").lower() == "true":
        music_engine = MusicEngine()
        bg_music_path, music_credits = music_engine.get_track(music_mood)
    
    editor = VideoEditor()
    output_file = f"output/final_{args.type}.mp4"
    logger.info(f"Rendering video with {music_mood} music...")
    is_short = (args.type == "short")
    
    try:
        bg_color = script_data.get('bg_color', "#FFFFFF") # Default to white
        success = editor.create_video(processed_scenes, output_file, is_short=is_short, bg_music_path=bg_music_path, style=args.style, bg_color=bg_color)
    except Exception as e:
        logger.error(f"CRITICAL RENDER ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        success = False
    
    if success:
        logger.info(f"Video generated successfully: {output_file}")
        try:
            validation = validate_video(output_file, is_short=is_short)
            logger.info(f"Production quality gate passed: {validation}")
        except Exception as e:
            logger.error(f"Production quality gate failed; refusing upload: {e}")
            sys.exit(1)

        # Prepare SEO Metadata
        video_title = script_data.get('title', args.topic)
        seo_description = script_data.get('description', f"{video_title}")
        research_sources = research_data.get("sources", [])
        if research_sources:
            source_lines = [
                f"- {source['title']} ({source['journal']}, {source['year']}): {source['url']}"
                for source in research_sources
            ]
            seo_description += "\n\nFurther reading (scholarly sources):\n" + "\n".join(source_lines)
        if args.type == "long" and 'chapters' in script_data:
            seo_description += "\n\nChapters:\n" + "\n".join(script_data['chapters'])
        
        # Add Music Credits (License Awareness)
        if bg_music_path and music_credits:
            seo_description += f"\n\n🎵 Music: {music_credits}"
        elif bg_music_path:
            # Fallback if credits couldn't be parsed
            music_name = os.path.basename(bg_music_path).split('.')[0].replace('_', ' ').title()
            seo_description += f"\n\n🎵 Music: {music_name}"
        
        seo_tags = script_data.get('tags', ['Viral', 'Trending'])
        
        # Schedule against America/New_York so daylight-saving changes are handled.
        from datetime import datetime, timedelta, timezone
        from zoneinfo import ZoneInfo

        target_hours_et = {"morning": 10, "afternoon": 14, "evening": 18}
        now_utc = datetime.now(timezone.utc)
        if args.schedule_for == "now":
            schedule_date = now_utc + timedelta(hours=12)
        else:
            eastern = now_utc.astimezone(ZoneInfo("America/New_York"))
            target_local = eastern.replace(
                hour=target_hours_et[args.schedule_for],
                minute=0, second=0, microsecond=0
            )
            if eastern >= target_local:
                target_local += timedelta(days=1)
            schedule_date = target_local.astimezone(timezone.utc)

        publish_at = schedule_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        logger.info(f"Scheduling video for {args.schedule_for} (America/New_York): {publish_at}")

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
                
                
                # Engagement Strategy: Since Pinned Comments don't work for Scheduled (Private) videos,
                # we move the Engagement Prompt to the TOP of the description for Shorts.
                prompts = [
                    f"Who else relates to this? Comment 'ME' below! 👇",
                    f"How was the video? Comment 'Ready' if you reached the end! 👇",
                    f"Did you know about this? Let's discuss in the comments! 💬",
                    f"Should I do more videos about '{video_title[:20]}'? Let me know! 👇"
                ]
                engagement_prompt = random.choice(prompts)
                
                # Prepend to description for visibility
                seo_description = f"{engagement_prompt}\n\n{seo_description}"
                
                # Determine category based on style
                category_id = "23" if args.style == "stickman" else "27"
                
                video_id = uploader.upload_video(
                    output_file, 
                    video_title, 
                    seo_description, 
                    tags=seo_tags,
                    publish_at=publish_at,
                    category_id=category_id,
                    # Our current visuals are stylized illustrations, not photorealistic synthetic footage.
                    altered_content=(os.getenv('YOUTUBE_SYNTHETIC_DISCLOSURE', 'false').lower() == 'true')
                )
                
                if video_id:
                    if not args.topic:
                        trend_engine.mark_used(title)
                    if os.path.exists(thumbnail_path):
                        uploader.set_thumbnail(video_id, thumbnail_path)
                    
                    # Attempt comment pinning only if NOT scheduled for far in the future
                    # (Though uploader.pin_comment usually fails for private/scheduled videos)
                    if not publish_at:
                        import time
                        logger.info("Waiting 15s for processing before pinning...")
                        time.sleep(15)
                        comment_id = uploader.add_comment(video_id, engagement_prompt)
                        if comment_id:
                            uploader.pin_comment(comment_id)
                    else:
                        logger.info("Video is scheduled. Engagement prompt has been added to the description instead.")
                    
                    logger.info(f"Successfully uploaded: https://youtu.be/{video_id}")
                else:
                    logger.error("YouTube upload returned no video ID; marking this workflow run as failed.")
                    sys.exit(1)
            except Exception as e:
                logger.error(f"Upload process failed: {e}")
                sys.exit(1)
    else:
        logger.error("Video generation failed")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
