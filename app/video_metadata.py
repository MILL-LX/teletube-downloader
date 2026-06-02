import os
import json
import shutil
import logging
from datetime import datetime, timezone
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def fetch_channel_video_metadata(api_key, channel_id):
    """Fetch video metadata for all videos in a channel's uploads playlist."""
    youtube = build("youtube", "v3", developerKey=api_key)

    uploads_playlist_id = "UU" + channel_id[2:]

    metadata = {"metadataUpdatedAt": None, "response": []}

    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=5000,
            pageToken=next_page_token,
        )

        response = request.execute()

        metadata["response"].extend(response.get("items", []))

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    metadata["metadataUpdatedAt"] = datetime.now(timezone.utc).isoformat()

    return metadata


def write_metadata_file(metadata, data_directory):
    """Write video metadata JSON to in-progress, then move to ready when complete."""
    in_progress_dir = os.path.join(data_directory, "metadata", "in-progress")
    ready_dir = os.path.join(data_directory, "metadata", "ready")
    os.makedirs(in_progress_dir, exist_ok=True)
    os.makedirs(ready_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat().replace(":", "-")
    filename = f"video_metadata_{timestamp}.json"
    in_progress_file = os.path.join(in_progress_dir, filename)

    logger.info(f"Writing metadata to: {in_progress_file}")
    with open(in_progress_file, "w") as f:
        json.dump(metadata, f, indent=2)

    ready_file = os.path.join(ready_dir, filename)
    shutil.move(in_progress_file, ready_file)
    logger.info(f"Metadata ready at: {ready_file}")
    return ready_file


def download_video_metadata(api_key, channel_id, data_directory):
    """Fetch video metadata from a channel and save it to the data directory."""
    metadata = fetch_channel_video_metadata(api_key, channel_id)
    return write_metadata_file(metadata, data_directory)
