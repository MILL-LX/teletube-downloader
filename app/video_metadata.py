import os
import json
import shutil
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from googleapiclient.discovery import build  # type: ignore

logger = logging.getLogger(__name__)


def fetch_channel_video_metadata(api_key: str, channel_id: str) -> Dict[str, Any]:
    '''Fetch video metadata for all videos in a channel's uploads playlist.'''
    youtube: Any = build('youtube', 'v3', developerKey=api_key)  # type: ignore

    uploads_playlist_id = 'UU' + channel_id[2:]

    metadata: Dict[str, Any] = {'metadataUpdatedAt': None, 'response': []}

    next_page_token: str | None = None

    while True:
        request: Any = youtube.playlistItems().list(  # type: ignore
            part='snippet,contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=5000,
            pageToken=next_page_token,
        )

        try:
            response: Dict[str, Any] = request.execute()  # type: ignore
        except Exception as e:
            logger.error(f'Failed to fetch playlist items: {e}')
            raise

        metadata['response'].extend(response.get('items', []))  # type: ignore

        next_page_token = response.get('nextPageToken')  # type: ignore
        if not next_page_token:
            break

    metadata['metadataUpdatedAt'] = datetime.now(timezone.utc).isoformat()  # type: ignore
    return metadata


def write_metadata_file(metadata: Dict[str, Any], data_directory: str) -> str:
    '''Write video metadata JSON to in-progress, then move to ready when complete.'''
    in_progress_dir = os.path.join(data_directory, 'metadata', 'in-progress')
    ready_dir = os.path.join(data_directory, 'metadata', 'ready')

    try:
        os.makedirs(in_progress_dir, exist_ok=True)
        os.makedirs(ready_dir, exist_ok=True)
    except Exception as e:
        logger.error(f'Failed to create metadata directories: {e}')
        raise

    file_timestamp: str = metadata['metadataUpdatedAt'].replace(':', '-')
    filename: str = f'video_metadata_{file_timestamp}.json'
    in_progress_file: str = os.path.join(in_progress_dir, filename)

    try:
        logger.info(f'Writing metadata to: {in_progress_file}')
        with open(in_progress_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f'Failed to write metadata file: {e}')
        raise

    try:
        ready_file: str = os.path.join(ready_dir, filename)
        shutil.move(in_progress_file, ready_file)
    except Exception as e:
        logger.error(f'Failed to move metadata file to ready: {e}')
        raise

    logger.info(f'Metadata ready at: {ready_file}')
    return ready_file


def load_latest_metadata(data_directory: str) -> Dict[str, Any]:
    '''Find the latest metadata file in the ready directory and return its parsed JSON.'''
    ready_dir = os.path.join(data_directory, 'metadata', 'ready')

    try:
        files: List[str] = sorted(
            (f for f in os.listdir(ready_dir) if f.startswith('video_metadata_') and f.endswith('.json')),
            reverse=True
        )
    except Exception as e:
        logger.error(f'Failed to list metadata files in {ready_dir}: {e}')
        raise

    if not files:
        error = FileNotFoundError(f'No metadata files found in {ready_dir}')
        logger.error(error)
        raise error

    latest_file: str = os.path.join(ready_dir, files[0])
    logger.info(f'Loading metadata from: {latest_file}')

    try:
        with open(latest_file, 'r') as f:
            metadata: Dict[str, Any] = json.load(f)
            return metadata
    except Exception as e:
        logger.error(f'Failed to read metadata file {latest_file}: {e}')
        raise


def download_video_metadata(api_key: str, channel_id: str, data_directory: str) -> str:
    '''Fetch video metadata from a channel and save it to the data directory.'''
    metadata = fetch_channel_video_metadata(api_key, channel_id)
    return write_metadata_file(metadata, data_directory)
