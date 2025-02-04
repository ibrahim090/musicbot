import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp
import logging
import asyncio
import tempfile
import platform
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Get the token
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("Error: No token found in .env file!")
    exit(1)
print(f"Token loaded: {token[:20]}...")

# FFmpeg options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -ar 48000 -ac 2 -b:a 192k'
}

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

# Get current OS
current_os = platform.system()
print(f"Current OS: {current_os}")

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
    'geo-bypass-country': 'US'
}

def get_browser_cookie_path():
    """Get the path to browser cookies based on OS"""
    if current_os not in BROWSER_PATHS:
        print(f"Unsupported OS: {current_os}")
        return None
    
    paths = BROWSER_PATHS[current_os]
    for browser, path in paths.items():
        if os.path.exists(path):
            print(f"Found {browser} at {path}")
            return browser, path
    
    return None

# Initialize bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

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
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        # Get browser and cookie path
        browser_info = get_browser_cookie_path()
        if browser_info:
            browser, path = browser_info
            print(f"Using {browser} cookies from {path}")
            YTDL_OPTIONS['cookies-from-browser'] = f"{browser}:{path}"
        
        try:
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
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
            if 'cookies-from-browser' in YTDL_OPTIONS:
                print("Retrying without cookies...")
                YTDL_OPTIONS.pop('cookies-from-browser', None)
                return await cls.from_url(url, loop=loop, stream=stream)
            raise e

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    for guild in bot.guilds:
        print(f'- {guild.name}')

@bot.command(name='play', help='تشغيل مقطع صوتي (رابط أو بحث)')
async def play(ctx, *, query):
    try:
        # Check if user is in voice channel
        if not ctx.message.author.voice:
            return await ctx.send("يجب أن تكون في قناة صوتية!")

        # Join voice channel if not already in one
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        # Stop current audio if playing
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        async with ctx.typing():
            try:
                # Send status message
                status_msg = await ctx.send("🔍 جاري البحث...")

                # Get player
                player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
                
                # Create embed
                embed = discord.Embed(
                    title="🎵 جاري التشغيل",
                    description=f"**{player.title}**",
                    color=discord.Color.green()
                )
                
                if player.thumbnail:
                    embed.set_thumbnail(url=player.thumbnail)
                
                if player.duration:
                    minutes = player.duration // 60
                    seconds = player.duration % 60
                    embed.add_field(name="المدة", value=f"{minutes}:{seconds:02d}", inline=True)
                
                if player.webpage_url:
                    embed.add_field(name="الرابط", value=f"[YouTube]({player.webpage_url})", inline=True)
                
                # Play audio
                ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

                # Update status message
                await status_msg.edit(content=None, embed=embed)
                
            except Exception as e:
                await ctx.send(f"❌ حدث خطأ: {str(e)}")
                print(f"Error in play command: {str(e)}")

    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {str(e)}")
        print(f"Error in play command: {str(e)}")

@bot.command(name='pause', help='إيقاف مؤقت')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ تم الإيقاف المؤقت")
    else:
        await ctx.send("❌ لا يوجد شيء قيد التشغيل!")

@bot.command(name='resume', help='استئناف التشغيل')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ تم استئناف التشغيل")
    else:
        await ctx.send("❌ لا يوجد شيء متوقف مؤقتاً!")

@bot.command(name='stop', help='إيقاف التشغيل')
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏹️ تم إيقاف التشغيل")
    else:
        await ctx.send("❌ لا يوجد شيء قيد التشغيل!")

@bot.command(name='leave', help='مغادرة القناة الصوتية')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 تمت المغادرة")
    else:
        await ctx.send("❌ لست في قناة صوتية!")

print("Starting bot...")
bot.run(token) 