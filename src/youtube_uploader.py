import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.config import Config
import logging

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self):
        self.youtube = self._get_authenticated_service()
        self._verify_expected_channel()

    def _verify_expected_channel(self):
        """Fail closed unless both the configured channel title and ID match."""
        expected_title = os.getenv("YOUTUBE_EXPECTED_CHANNEL_TITLE", "").strip()
        expected_id = os.getenv("YOUTUBE_EXPECTED_CHANNEL_ID", "").strip()
        if not expected_title or not expected_id:
            raise RuntimeError(
                "Safety stop: set YOUTUBE_EXPECTED_CHANNEL_TITLE and "
                "YOUTUBE_EXPECTED_CHANNEL_ID before any YouTube operation."
            )
        response = self.youtube.channels().list(mine=True, part="snippet", maxResults=5).execute()
        items = response.get("items", [])
        if len(items) != 1:
            raise RuntimeError(f"Safety stop: expected one authenticated channel, received {len(items)}.")
        channel = items[0]
        actual_id = channel.get("id", "")
        actual_title = channel.get("snippet", {}).get("title", "").strip()
        if actual_id != expected_id or actual_title.casefold() != expected_title.casefold():
            raise RuntimeError(
                "Safety stop: OAuth destination mismatch. "
                f"Expected '{expected_title}' ({expected_id}); received '{actual_title}' ({actual_id})."
            )
        self.channel_id = actual_id
        logger.info("YouTube destination verified: %s (%s)", actual_title, actual_id)

    def _get_authenticated_service(self):
        """Authenticate with the minimum scopes required; never broaden permissions silently."""
        if not Config.YOUTUBE_REFRESH_TOKEN:
            raise ValueError("YOUTUBE_REFRESH_TOKEN is missing from configuration/secrets.")
        if not Config.YOUTUBE_CLIENT_ID or not Config.YOUTUBE_CLIENT_SECRET:
            raise ValueError("YouTube OAuth client ID/secret are missing.")

        scopes = [
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/yt-analytics.readonly",
        ]
        credentials = google.oauth2.credentials.Credentials(
            None, refresh_token=Config.YOUTUBE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=Config.YOUTUBE_CLIENT_ID,
            client_secret=Config.YOUTUBE_CLIENT_SECRET, scopes=scopes,
        )
        from google.auth.transport.requests import Request
        credentials.refresh(Request())
        self.credentials = credentials
        # Actual permissions are verified by the channel lookup and upload request;
        # older refresh-token responses do not always return granted_scopes.
        return build("youtube", "v3", credentials=credentials, cache_discovery=False)

    def upload_video(self, video_path, title, description, tags=None, privacy_status="private", publish_at=None, category_id="27", altered_content=False):
        try:
            logger.info(f"Uploading video: {title}")
            
            status = {
                'privacyStatus': 'private' if publish_at else privacy_status,
                'selfDeclaredMadeForKids': False,
            }
            if publish_at:
                status['publishAt'] = publish_at  # ISO 8601 UTC timestamp

            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags if tags else [],
                    'categoryId': category_id
                },
                'status': status,
            }
            
            # Add altered content declaration if specified
            if altered_content:
                body['status']['containsSyntheticMedia'] = True
            
            # MediaFileUpload handles the file upload
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Uploaded {int(status.progress() * 100)}%")

            logger.info(f"Upload Complete! Video ID: {response['id']}")
            return response['id']

        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            return None

    def wait_until_processed(self, video_id, timeout_seconds=2400, poll_interval=15):
        """Wait for YouTube processing before setting a custom thumbnail or scheduling."""
        import time
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                response = self.youtube.videos().list(
                    part="processingDetails,status",
                    id=video_id,
                    maxResults=1,
                ).execute()
                items = response.get("items", [])
                if not items:
                    raise RuntimeError(f"YouTube could not find uploaded video {video_id}.")
                details = items[0].get("processingDetails", {})
                state = details.get("processingStatus", "")
                logger.info("YouTube processing status for %s: %s", video_id, state or "not reported")
                if state == "succeeded":
                    return True
                if state in ("failed", "terminated"):
                    logger.error("YouTube processing ended in state %s for %s", state, video_id)
                    return False
            except Exception as exc:
                logger.warning("Could not check processing status for %s: %s", video_id, exc)
            time.sleep(poll_interval)
        logger.error("Timed out waiting for YouTube processing for %s", video_id)
        return False

    def schedule_video(self, video_id, publish_at):
        """Schedule an already-uploaded private video only after thumbnail setup succeeds."""
        if not video_id or not publish_at:
            raise ValueError("A video ID and future publish time are required.")
        try:
            self.youtube.videos().update(
                part="status",
                body={
                    "id": video_id,
                    "status": {
                        "privacyStatus": "private",
                        "publishAt": publish_at,
                    },
                },
            ).execute()
            logger.info("Video %s scheduled for %s", video_id, publish_at)
            return True
        except Exception as exc:
            logger.error("Could not schedule video %s; it remains private: %s", video_id, exc)
            return False

    def add_comment(self, video_id, text):
        """Adds a top-level comment to a video."""
        try:
            request = self.youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": text
                            }
                        }
                    }
                }
            )
            response = request.execute()
            comment_id = response['snippet']['topLevelComment']['id']
            logger.info(f"Comment added. ID: {comment_id}")
            return comment_id
        except Exception as e:
            error_body = getattr(e, 'content', str(e))
            if "insufficientPermissions" in str(e):
                logger.warning(f"Failed to add comment: Insufficient Permissions (403). Ensure token has 'force-ssl'. Details: {error_body}")
            elif "commentsDisabled" in str(e):
                 logger.warning(f"Failed to add comment: Comments are disabled on this video (ID: {video_id}).")
            else:
                logger.warning(f"Failed to add comment error: {e}. Details: {error_body}")
            return None

    def pin_comment(self, comment_id):
        """Pins a comment (requires high-level scope)."""
        try:
            request = self.youtube.comments().setAttributes(
                id=comment_id,
                part="snippet",
                body={
                    "snippet": {
                        "viewerRating": "none",
                        "isPinned": True
                    }
                }
            )
            request.execute()
            logger.info(f"Comment {comment_id} pinned.")
            return True
        except Exception as e:
            logger.warning(f"Failed to pin comment: {e} (This usually requires force-ssl scope)")
            return False

    def set_thumbnail(self, video_id, thumbnail_path):
        """Uploads a custom thumbnail for a video."""
        try:
            logger.info(f"Uploading thumbnail for {video_id}...")
            if not os.path.exists(thumbnail_path):
                logger.error(f"Thumbnail file not found: {thumbnail_path}")
                return False

            request = self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            )
            response = request.execute()
            logger.info("Thumbnail uploaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to upload thumbnail: {e}")
            return False

    def get_video_performance(self, video_ids):
        """Fetch titles and public view counts for Analytics-ranked video IDs."""
        ids = [str(video_id) for video_id in video_ids if video_id]
        if not ids:
            return []
        try:
            response = self.youtube.videos().list(
                id=",".join(ids[:50]),
                part="snippet,statistics",
                maxResults=min(len(ids), 50),
            ).execute()
            return [
                {
                    "video_id": item.get("id", ""),
                    "title": item.get("snippet", {}).get("title", ""),
                    "views": int(item.get("statistics", {}).get("viewCount", 0)),
                }
                for item in response.get("items", [])
            ]
        except Exception as exc:
            logger.warning("Could not resolve Analytics video titles: %s", exc)
            return []

    def get_recent_performance(self, limit=5):
        """Fetches the titles and view counts of the last N uploaded videos."""
        try:
            logger.info(f"Fetching performance data for last {limit} videos...")
            
            # 1. Get uploaded videos playlist ID
            channels_response = self.youtube.channels().list(
                mine=True,
                part="contentDetails"
            ).execute()
            
            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # 2. Get recent videos from playlist
            playlist_items_response = self.youtube.playlistItems().list(
                playlistId=uploads_playlist_id,
                part="snippet,contentDetails",
                maxResults=limit
            ).execute()
            
            video_ids = [item['contentDetails']['videoId'] for item in playlist_items_response['items']]
            
            if not video_ids:
                return []
                
            # 3. Get view counts for these videos
            videos_response = self.youtube.videos().list(
                id=",".join(video_ids),
                part="snippet,statistics"
            ).execute()
            
            performance_data = []
            for item in videos_response['items']:
                performance_data.append({
                    "title": item['snippet']['title'],
                    "views": int(item['statistics'].get('viewCount', 0))
                })
                
            return performance_data
            
        except Exception as e:
            logger.warning(f"Failed to fetch performance data: {e}")
            return []
