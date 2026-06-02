import os
import json
import shutil
from datetime import datetime, timezone
from googleapiclient.discovery import build


def fetch_channel_video_metadata(api_key, channel_id):
    """Fetch video metadata for all videos in a channel's uploads playlist."""
    youtube = build('youtube', 'v3', developerKey=api_key)

    uploads_playlist_id = 'UU' + channel_id[2:]

    metadata = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=5000,
            pageToken=next_page_token
        )

        response = request.execute()

        for item in response.get('items', []):
            metadata.append(item)

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return metadata


def validate_video_metadata(metadata):
    """Validate that the metadata list is non-empty and each item has required fields."""
    if not isinstance(metadata, list) or len(metadata) == 0:
        return False, "metadata list is empty or not a list"
    for i, item in enumerate(metadata):
        if 'snippet' not in item or 'contentDetails' not in item:
            return False, f"item {i} is missing 'snippet' or 'contentDetails'"
    return True, None


def save_video_metadata(metadata, data_directory):
    """Write video metadata to in-progress, validate, then move to ready if valid."""
    in_progress_dir = os.path.join(data_directory, 'metadata', 'in-progress')
    ready_dir = os.path.join(data_directory, 'metadata', 'ready')
    os.makedirs(in_progress_dir, exist_ok=True)
    os.makedirs(ready_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-")
    filename = f'video_metadata_{timestamp}.json'
    in_progress_file = os.path.join(in_progress_dir, filename)

    # Write video metadata to in-progress
    print(f"Writing metadata to: {in_progress_file}")
    with open(in_progress_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Validate the written file
    print("Validating metadata file...")
    with open(in_progress_file, 'r') as f:
        written_metadata = json.load(f)

    valid, error = validate_video_metadata(written_metadata)

    if valid:
        ready_file = os.path.join(ready_dir, filename)
        shutil.move(in_progress_file, ready_file)
        print(f"Validation passed. File moved to: {ready_file}")
    else:
        print(f"Validation failed: {error}")
        print(f"File left at: {in_progress_file}")
