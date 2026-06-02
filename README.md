# teletube-downloader
Download YouTube Videos for Teletube application

## Setup

### 1. Install uv
Follow the installation instructions at https://docs.astral.sh/uv/getting-started/installation/

### 2. Clone the repository
```
git clone https://github.com/MILL-LX/teletube-downloader.git
```

### 3. Install App Dependencies
```
cd teletube-downloader/app
uv sync
```

### 4. Install System Dependencies

### ffmpeg
Video downloading relies on [ffmpeg](https://ffmpeg.org) for post-processing and merging audio/video streams. Install it before running the app.

Installation instructions: https://ffmpeg.org/download.html
