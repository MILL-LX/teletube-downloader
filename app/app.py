import os
import argparse
import logging
from typing import Any, Dict
from dotenv import load_dotenv
from video_metadata import download_video_metadata, load_latest_metadata
from video_downloads import download_videos

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    class UsageOnErrorParser(argparse.ArgumentParser):
        def error(self, message: str) -> None:  # type: ignore
            self.print_help()
            print(f'\nerror: {message}')
            raise SystemExit(2)

    parser: UsageOnErrorParser = UsageOnErrorParser(description='Download YouTube channel videos.', allow_abbrev=False)
    parser.add_argument('--skip-metadata-download', action='store_true', help='Skip metadata download and use the latest existing metadata file.')
    args: argparse.Namespace = parser.parse_args()

    # Load credentials from environment variables
    API_KEY: str | None = os.getenv('YOUTUBE_API_KEY')
    CHANNEL_ID: str | None = os.getenv('YOUTUBE_CHANNEL_ID')
    DATA_DIRECTORY: str = os.getenv('DATA_DIRECTORY', '../data')

    # Validate that required variables are set
    if not API_KEY:
        raise ValueError("YOUTUBE_API_KEY not found in .env file")
    if not CHANNEL_ID:
        raise ValueError("YOUTUBE_CHANNEL_ID not found in .env file")

    if not args.skip_metadata_download:
        print(f"Fetching video metadata from channel: {CHANNEL_ID}")
        print("-" * 50)
        metadata_file: str = download_video_metadata(API_KEY, CHANNEL_ID, DATA_DIRECTORY)
        print(f"Downloaded metadata file: {metadata_file}")
    else:
        logger.info('Skipping metadata download, using latest available metadata.')

    metadata: Dict[str, Any] = load_latest_metadata(DATA_DIRECTORY)

    download_videos(metadata, DATA_DIRECTORY)
