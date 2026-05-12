import os
import json
from datetime import datetime
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

def get_channel_videos(api_key, channel_id):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    uploads_playlist_id = 'UU' + channel_id[2:]
    
    videos = []
    
    next_page_token = None
    
    while True:
        # Search for videos from the channel in the specified year
        request = youtube.playlistItems().list(
            part='snippet,contentDetails',
            playlistId=uploads_playlist_id,
            maxResults=5000,
            pageToken=next_page_token
        )
        
        response = request.execute()
        
        # Extract video information
        for item in response.get('items', []):
            videos.append(item)
        
        # Check if there are more pages
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    
    return videos


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
    
    print(f"Fetching videos from channel: {CHANNEL_ID}")
    print("-" * 50)
    
    videos = get_channel_videos(API_KEY, CHANNEL_ID)
    (API_KEY, CHANNEL_ID)
    
    timestamp = datetime.now().isoformat().replace(":", "-")
    json_output_file = os.path.join(DATA_DIRECTORY, f'videos_{timestamp}.json')

    # write video json to a file in the data directory
    with open(json_output_file, 'w') as f:
        json.dump(videos, f)
