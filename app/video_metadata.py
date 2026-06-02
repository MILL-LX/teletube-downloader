import os
import json
import shutil
import logging
from datetime import datetime, timezone
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def fetch_channel_video_metadata(api_key, channel_id):
    '''Fetch video metadata for all videos in a channel's uploads playlist.'''
    youtube = build('youtube', 'v3', developerKey=api_key)

    uploads_playlist_id = 'UU' + channel_id[2:]

    metadata = {'metadataUpdatedAt': None, 'response': []}

    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=5000,
            pageToken=next_page_token,
        )

        try:
            response = request.execute()
        except Exception as e:
            logger.error(f'Failed to fetch playlist items: {e}')
            raise

        metadata['response'].extend(response.get('items', []))

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    metadata['metadataUpdatedAt'] = datetime.now(timezone.utc).isoformat()
    return metadata


def write_metadata_file(metadata, data_directory):
    '''Write video metadata JSON to in-progress, then move to ready when complete.'''
    in_progress_dir = os.path.join(data_directory, 'metadata', 'in-progress')
    ready_dir = os.path.join(data_directory, 'metadata', 'ready')

    try:
        os.makedirs(in_progress_dir, exist_ok=True)
        os.makedirs(ready_dir, exist_ok=True)
    except Exception as e:
        logger.error(f'Failed to create metadata directories: {e}')
        raise

    file_timestamp = metadata['metadataUpdatedAt'].replace(':', '-')
    filename = f'video_metadata_{file_timestamp}.json'
    in_progress_file = os.path.join(in_progress_dir, filename)

    try:
        logger.info(f'Writing metadata to: {in_progress_file}')
        with open(in_progress_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f'Failed to write metadata file: {e}')
        raise

    try:
        ready_file = os.path.join(ready_dir, filename)
        shutil.move(in_progress_file, ready_file)
    except Exception as e:
        logger.error(f'Failed to move metadata file to ready: {e}')
        raise

    logger.info(f'Metadata ready at: {ready_file}')
    return ready_file


def load_latest_metadata(data_directory):
    '''Find the latest metadata file in the ready directory and return its parsed JSON.'''
    ready_dir = os.path.join(data_directory, 'metadata', 'ready')

    try:
        files = sorted(
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

    latest_file = os.path.join(ready_dir, files[0])
    logger.info(f'Loading metadata from: {latest_file}')

    try:
        with open(latest_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Failed to read metadata file {latest_file}: {e}')
        raise


def download_video_metadata(api_key, channel_id, data_directory):
    '''Fetch video metadata from a channel and save it to the data directory.'''
    metadata = fetch_channel_video_metadata(api_key, channel_id)
    return write_metadata_file(metadata, data_directory)
