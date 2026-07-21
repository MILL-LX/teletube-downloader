# teletube-downloader
Download YouTube Videos for Teletube application

## Overview

teletube-downloader fetches all videos from a YouTube channel and downloads them to local storage, organized by publish year.

It runs in two stages:

**1. Metadata fetch** — queries the YouTube Data API for the channel's full upload history and saves the results as a timestamped JSON file. Metadata files are written to `data/metadata/in-progress/` while being written, then moved to `data/metadata/ready/` once complete, preventing consumers from reading a partially written file.

**2. Video download** — reads the latest metadata file and downloads any videos not already present locally. Videos are downloaded as MP4, favouring the smallest file at the lowest resolution of 360p or above. Files are downloaded to `data/videos/in-progress/` and moved to `data/videos/ready/{year}/` on completion, again preventing partial reads. Already-downloaded videos are skipped.

## Setup

### 1. Install uv
Follow the installation instructions at https://docs.astral.sh/uv/getting-started/installation/

### 2. Clone the repository
```
git clone https://github.com/MILL-LX/teletube-downloader.git
```

## 3. Install System Dependencies

### ffmpeg
Video downloading relies on [ffmpeg](https://ffmpeg.org) for post-processing and merging audio/video streams. Install it before running the app.

Installation instructions: https://ffmpeg.org/download.html

### Deno
yt-dlp requires Deno to solve YouTube's JavaScript challenge when fetching video formats. Without it, some videos may show no available formats.

Installation instructions: https://docs.deno.com/runtime/getting_started/installation/

### Linux CFFI Dependencies

On Raspberry Pi OS install the following system dependencies.

```bash
sudo apt update
sudo apt install -y python3-dev libffi-dev pkg-config build-essential
```

### 4. Install App Dependencies
```
cd teletube-downloader
uv sync
```

### 5. Update app/.env 

```bash
cp app/.env-example app/.env
```

Update the values for your YouTube API Key, ChannelID, and the data directory where downloaded data will be written.

## Usage

Run the full pipeline — fetch metadata then download videos:
```
uv run python app.py
```

Skip the metadata fetch and use the latest already-downloaded metadata:
```
uv run python app.py --skip-metadata-download
```

## Running on a schedule with cron

To run the downloader once a day, add a cron entry with `crontab -e`:

```
0 3 * * * cd /path/to/teletube-downloader/app && /path/to/uv run python app.py >> /path/to/teletube-downloader/cron.log 2>&1
```

This runs the program at 3am every day and appends output to `cron.log`. Adjust the time and paths as needed.

Note: cron runs with a minimal environment, so full paths are required for both the working directory and the `uv` binary. On non-macOS systems or if uv was installed differently, find the correct path with `which uv`.
