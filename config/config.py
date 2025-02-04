import os
from pathlib import Path
import platform

# Get user's home directory
HOME = str(Path.home())

# Browser paths based on OS
BROWSER_PATHS = {
    'Windows': {
        'chrome': os.path.join(HOME, 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default'),
        'firefox': os.path.join(HOME, 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles'),
        'edge': os.path.join(HOME, 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default'),
    },
    'Darwin': {  # macOS
        'chrome': os.path.join(HOME, 'Library', 'Application Support', 'Google', 'Chrome', 'Default'),
        'firefox': os.path.join(HOME, 'Library', 'Application Support', 'Firefox', 'Profiles'),
        'edge': os.path.join(HOME, 'Library', 'Application Support', 'Microsoft Edge', 'Default'),
    },
    'Linux': {
        'chrome': os.path.join(HOME, '.config', 'google-chrome', 'Default'),
        'firefox': os.path.join(HOME, '.mozilla', 'firefox'),
        'edge': os.path.join(HOME, '.config', 'microsoft-edge', 'Default'),
    }
}

# FFmpeg options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -ar 48000 -ac 2 -b:a 192k'
}

# YouTube DL options
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'cachedir': False,
    'extractor-args': {
        'youtube': {
            'player_skip': ['webpage', 'configs'],
            'skip': ['dash', 'hls']
        }
    },
    'geo-bypass': True,
    'geo-bypass-country': 'US',
    'cookies-from-browser': 'chrome',
    'nocheckcertificate': True,
    'no-check-certificates': True,
    'prefer-insecure': True,
    'http-chunk-size': '10M',
    'buffersize': '50M',
    'external-downloader': 'ffmpeg',
    'external-downloader-args': {
        'ffmpeg_i': ['-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '5']
    }
}

# Spotify URL patterns
SPOTIFY_PATTERNS = {
    'track': r'https?://open\.spotify\.com/track/([a-zA-Z0-9]+)',
    'playlist': r'https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)',
    'album': r'https?://open\.spotify\.com/album/([a-zA-Z0-9]+)'
}

# Current OS
CURRENT_OS = platform.system() 