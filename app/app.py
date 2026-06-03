import os
import logging
from dotenv import load_dotenv
from video_metadata import download_video_metadata, load_latest_metadata
from video_downloads import download_videos

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)


if __name__ == "__main__":
    # Load credentials from environment variables
    API_KEY = os.getenv('YOUTUBE_API_KEY')
    CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
    DATA_DIRECTORY = os.getenv('DATA_DIRECTORY', '../data')

    # Validate that required variables are set
    if not API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in .env file")
    if not CHANNEL_ID:
        raise ValueError("YOUTUBE_CHANNEL_ID not found in .env file")

    print(f"Fetching video metadata from channel: {CHANNEL_ID}")
    print("-" * 50)

    metadata_file = download_video_metadata(API_KEY, CHANNEL_ID, DATA_DIRECTORY)
    print(f"Downloaded metadata file: {metadata_file}")

    metadata = load_latest_metadata(DATA_DIRECTORY)

    download_videos(metadata, DATA_DIRECTORY)
