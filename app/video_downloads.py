import os
import shutil
import logging
import yt_dlp

logger = logging.getLogger(__name__)

YOUTUBE_URL_TEMPLATE = 'https://www.youtube.com/watch?v={video_id}'


def _make_video_filename(title, video_id, ext):
    '''Build a video filename from title, video ID, and extension.'''
    safe_title = ''.join(c if c.isalnum() or c in ' ._-' else '_' for c in title).strip()
    return f'{safe_title}-{video_id}.{ext}'


def _get_video_items(metadata):
    '''Extract video ID, title, and publish year from a metadata response.'''
    items = []
    for item in metadata.get('response', []):
        video_id = item['contentDetails']['videoId']
        published_at = item['contentDetails'].get('videoPublishedAt', '')
        year = published_at[:4] if published_at else 'unknown'
        title = item['snippet'].get('title', video_id)
        items.append((video_id, year, title))
    return items


def _is_already_downloaded(video_id, ready_dir):
    '''Return True if a file for this video ID already exists in any year subdirectory.'''
    for entry in os.scandir(ready_dir):
        if entry.is_dir():
            if any(f.endswith(f'-{video_id}.mp4') for f in os.listdir(entry.path)):
                return True
    return False


def download_videos(metadata, data_directory, cookies_from_browser=None):
    '''Download videos described in metadata if not already downloaded.

    Videos are placed in data/videos/in-progress during download,
    then moved to data/videos/ready/{year} on completion.
    '''
    in_progress_dir = os.path.join(data_directory, 'videos', 'in-progress')
    ready_dir = os.path.join(data_directory, 'videos', 'ready')

    try:
        os.makedirs(in_progress_dir, exist_ok=True)
        os.makedirs(ready_dir, exist_ok=True)
    except Exception as e:
        logger.error(f'Failed to create video directories: {e}')
        raise

    video_items = _get_video_items(metadata)
    logger.info(f'Found {len(video_items)} videos in metadata')

    for video_id, year, title in video_items:
        if _is_already_downloaded(video_id, ready_dir):
            logger.info(f'Skipping already downloaded video: {video_id}')
            continue

        url = YOUTUBE_URL_TEMPLATE.format(video_id=video_id)
        output_template = os.path.join(in_progress_dir, _make_video_filename(title, video_id, '%(ext)s'))

        ydl_opts = {
            'outtmpl': output_template,
            'format': 'bestvideo[protocol!=mhtml]+bestaudio[protocol!=mhtml]/best[protocol!=mhtml]',
            'merge_output_format': 'mp4',
            'format_sort': ['+height', '+filesize'],
            'sleep_interval': 5,
            'ratelimit': 1_000_000,
            'quiet': True,
            'noplaylist': True,
            'no_warnings': True,
        }

        if cookies_from_browser:
            ydl_opts['cookiesfrombrowser'] = (cookies_from_browser,)

        logger.info(f'Downloading video: {video_id}')
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            logger.error(f'Failed to download video {video_id}: {e}')
            continue

        # Move completed file(s) to ready/{year}
        try:
            year_dir = os.path.join(ready_dir, year)
            os.makedirs(year_dir, exist_ok=True)
            for filename in os.listdir(in_progress_dir):
                if filename == _make_video_filename(title, video_id, 'mp4'):
                    src = os.path.join(in_progress_dir, filename)
                    dst = os.path.join(year_dir, filename)
                    shutil.move(src, dst)
                    logger.info(f'Video ready at: {dst}')
                    break
        except Exception as e:
            logger.error(f'Failed to move video {video_id} to ready: {e}')
            continue
