import discord
import yt_dlp
import asyncio
import ssl
from config.config import YTDL_OPTIONS, FFMPEG_OPTIONS, BROWSER_PATHS, CURRENT_OS
import os

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.webpage_url = data.get('webpage_url')

    @classmethod
    async def get_browser_cookie_path(cls):
        """Get the path to browser cookies based on OS"""
        if CURRENT_OS not in BROWSER_PATHS:
            print(f"Unsupported OS: {CURRENT_OS}")
            return None
        
        paths = BROWSER_PATHS[CURRENT_OS]
        for browser, path in paths.items():
            if os.path.exists(path):
                print(f"Found {browser} at {path}")
                return browser, path
        
        return None

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        # Get browser and cookie path
        browser_info = await cls.get_browser_cookie_path()
        if browser_info:
            browser, path = browser_info
            print(f"Using {browser} cookies from {path}")
            YTDL_OPTIONS['cookies-from-browser'] = f"{browser}:{path}"
        
        try:
            # Create a copy of options and add SSL context
            ytdl_opts = dict(YTDL_OPTIONS)
            
            # Create SSL context that ignores certificate verification
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            ssl_context.verify_mode = ssl.CERT_NONE
            ssl_context.check_hostname = False
            
            # Add SSL context to options
            ytdl_opts['http_headers'] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                # Check if URL is a search query
                if not ('youtube.com' in url or 'youtu.be' in url):
                    print("Searching YouTube...")
                    url = f"ytsearch:{url}"

                # Extract video info
                print("Extracting video info...")
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
                
                if 'entries' in data:
                    data = data['entries'][0]

                filename = data['url'] if stream else ytdl.prepare_filename(data)
                print("Successfully extracted info")
                return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)
                
        except Exception as e:
            print(f"Error in YTDLSource.from_url: {str(e)}")
            # Try without cookies if failed
            if 'cookies-from-browser' in ytdl_opts:
                print("Retrying without cookies...")
                ytdl_opts.pop('cookies-from-browser', None)
                return await cls.from_url(url, loop=loop, stream=stream)
            raise e 