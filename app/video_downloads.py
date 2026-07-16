import os
import json
import shutil
import subprocess
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any
import yt_dlp

logger = logging.getLogger(__name__)

YOUTUBE_URL_TEMPLATE = 'https://www.youtube.com/watch?v={video_id}'
SKIP_LIST_FILENAME = 'skip.json'


def _load_skip_list(videos_dir: str) -> Dict[str, Dict[str, str]]:
    '''Load the skip list from disk. Returns a dict of {video_id: {reason, timestamp}}.'''
    skip_file = os.path.join(videos_dir, SKIP_LIST_FILENAME)
    if not os.path.isfile(skip_file):
        return {}
    try:
        with open(skip_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Failed to load skip list: {e}')
        return {}


def _add_to_skip_list(videos_dir: str, skip_list: Dict[str, Dict[str, str]], video_id: str, reason: str) -> None:
    '''Add a video to the skip list and persist it.'''
    timestamp = datetime.now(timezone.utc).isoformat()
    skip_list[video_id] = {'reason': reason, 'timestamp': timestamp}
    skip_file = os.path.join(videos_dir, SKIP_LIST_FILENAME)
    try:
        with open(skip_file, 'w') as f:
            json.dump(skip_list, f, indent=2)
        logger.info(f'Added {video_id} to skip list: {reason}')
    except Exception as e:
        logger.error(f'Failed to save skip list: {e}')


def _make_video_filename(title: str, video_id: str, ext: str) -> str:
    '''Build a video filename from title, video ID, and extension.'''
    safe_title = ''.join(c if c.isalnum() or c in ' ._-' else '_' for c in title).strip()
    return f'{safe_title}-{video_id}.{ext}'


def _get_video_items(metadata: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    '''Extract video ID, title, and publish year from a metadata response.'''
    items: List[Tuple[str, str, str]] = []
    for item in metadata.get('response', []):
        video_id: str = item['contentDetails']['videoId']
        published_at: str = item['contentDetails'].get('videoPublishedAt', '')
        year: str = published_at[:4] if published_at else 'unknown'
        title: str = item['snippet'].get('title', video_id)
        items.append((video_id, year, title))
    return items


def _is_already_downloaded(video_id: str, title: str, year: str, ready_dir: str) -> bool:
    '''Return True if the video file already exists in the ready directory.'''
    expected_file = os.path.join(ready_dir, year, _make_video_filename(title, video_id, 'mp4'))
    return os.path.isfile(expected_file)


def download_videos(metadata: Dict[str, Any], data_directory: str) -> None:
    '''Download videos described in metadata if not already downloaded.

    Videos are placed in data/videos/in-progress during download,
    then moved to data/videos/ready/{year} on completion.
    '''
    videos_dir = os.path.join(data_directory, 'videos')
    in_progress_dir = os.path.join(videos_dir, 'in-progress')
    ready_dir = os.path.join(videos_dir, 'ready')

    try:
        os.makedirs(in_progress_dir, exist_ok=True)
        os.makedirs(ready_dir, exist_ok=True)
    except Exception as e:
        logger.error(f'Failed to create video directories: {e}')
        raise

    skip_list = _load_skip_list(videos_dir)
    video_items = _get_video_items(metadata)
    logger.info(f'Found {len(video_items)} videos in metadata')

    for video_id, year, title in video_items:
        if video_id in skip_list:
            logger.info(f'Skipping {video_id} (skip list): {skip_list[video_id]["reason"]}')
            continue
        if _is_already_downloaded(video_id, title, year, ready_dir):
            logger.info(f'Skipping already downloaded video: {video_id}')
            continue

        url = YOUTUBE_URL_TEMPLATE.format(video_id=video_id)
        output_template = os.path.join(in_progress_dir, _make_video_filename(title, video_id, '%(ext)s'))

        ydl_opts: Dict[str, Any] = {
            'outtmpl': output_template,
            'format': 'bestvideo[height>=360][protocol!=mhtml]+bestaudio[protocol!=mhtml]/best[height>=360][vcodec!=none][protocol!=mhtml]',
            'merge_output_format': 'mp4',
            'format_sort': ['+height', '+filesize'],
            'sleep_interval': 2,
            'max_sleep_interval': 5,
            'quiet': True,
            'noplaylist': True,
            'no_warnings': True,
        }

        logger.info(f'Downloading video: {video_id}')
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore
                ydl.download([url])
        except Exception as e:
            error_msg = str(e)
            logger.error(f'Failed to download video {video_id}: {error_msg}')
            if 'Sign in to confirm' in error_msg or 'not a bot' in error_msg:
                logger.error('YouTube is rate limiting. Please try again in a couple of hours.')
                return
            if '403' in error_msg or 'Forbidden' in error_msg:
                _add_to_skip_list(videos_dir, skip_list, video_id, error_msg)
            if 'This video is not available' in error_msg:
                _add_to_skip_list(videos_dir, skip_list, video_id, error_msg)
            if 'Requested format is not available' in error_msg:
                _add_to_skip_list(videos_dir, skip_list, video_id, error_msg)
            continue

        # Move completed file to ready/{year} if it contains a video stream
        try:
            year_dir = os.path.join(ready_dir, year)
            os.makedirs(year_dir, exist_ok=True)
            for filename in os.listdir(in_progress_dir):
                if filename == _make_video_filename(title, video_id, 'mp4'):
                    src = os.path.join(in_progress_dir, filename)
                    probe = subprocess.run(
                        ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                         '-show_entries', 'stream=codec_type', '-of', 'default=noprint_wrappers=1', src],
                        capture_output=True, text=True
                    )
                    if 'codec_type=video' not in probe.stdout:
                        logger.error(f'Downloaded file has no video stream, discarding: {src}')
                        os.remove(src)
                        break
                    dst = os.path.join(year_dir, filename)
                    shutil.move(src, dst)
                    logger.info(f'Video ready at: {dst}')
                    break
        except Exception as e:
            logger.error(f'Failed to move video {video_id} to ready: {e}')
            continue
