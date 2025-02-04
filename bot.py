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
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Get tokens
token = os.getenv('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

if not token:
    print("Error: No Discord token found in .env file!")
    exit(1)
print(f"Discord token loaded: {token[:20]}...")

# Initialize Spotify client if credentials are available
sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    try:
        sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET
        ))
        print("Spotify client initialized successfully")
    except Exception as e:
        print(f"Error initializing Spotify client: {str(e)}")
else:
    print("No Spotify credentials found, Spotify support will be limited")

# Regular expressions for Spotify URLs
SPOTIFY_TRACK_URL_REGEX = r'https?://open\.spotify\.com/track/([a-zA-Z0-9]+)'
SPOTIFY_PLAYLIST_URL_REGEX = r'https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)'
SPOTIFY_ALBUM_URL_REGEX = r'https?://open\.spotify\.com/album/([a-zA-Z0-9]+)'

async def get_spotify_track_info(url):
    """Get track information from Spotify URL"""
    if not sp:
        return None
        
    try:
        # Extract track ID from URL
        track_match = re.match(SPOTIFY_TRACK_URL_REGEX, url)
        if not track_match:
            return None
            
        track_id = track_match.group(1)
        track_info = sp.track(track_id)
        
        # Format artist and track name for YouTube search
        artists = ", ".join([artist['name'] for artist in track_info['artists']])
        track_name = track_info['name']
        search_query = f"{artists} - {track_name}"
        
        return {
            'search_query': search_query,
            'track_name': track_name,
            'artists': artists,
            'duration_ms': track_info['duration_ms'],
            'album_name': track_info['album']['name'],
            'album_art': track_info['album']['images'][0]['url'] if track_info['album']['images'] else None
        }
    except Exception as e:
        print(f"Error getting Spotify track info: {str(e)}")
        return None

async def get_spotify_playlist_tracks(url):
    """Get all tracks from a Spotify playlist"""
    if not sp:
        return None
        
    try:
        # Extract playlist ID from URL
        playlist_match = re.match(SPOTIFY_PLAYLIST_URL_REGEX, url)
        if not playlist_match:
            return None
            
        playlist_id = playlist_match.group(1)
        results = sp.playlist_tracks(playlist_id)
        tracks = []
        
        for item in results['items']:
            track = item['track']
            artists = ", ".join([artist['name'] for artist in track['artists']])
            tracks.append({
                'search_query': f"{artists} - {track['name']}",
                'track_name': track['name'],
                'artists': artists
            })
            
        return tracks
    except Exception as e:
        print(f"Error getting Spotify playlist: {str(e)}")
        return None

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

@bot.command(name='play', help='تشغيل مقطع صوتي (رابط يوتيوب/سبوتيفاي أو بحث)')
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
                # Send initial status message
                status_msg = await ctx.send("🔍 جاري البحث...")
                
                # Check if query is a Spotify URL
                if 'open.spotify.com' in query:
                    if 'track' in query:
                        # Handle single Spotify track
                        track_info = await get_spotify_track_info(query)
                        if track_info:
                            # Update status message
                            await status_msg.edit(content=f"🎵 تم العثور على: {track_info['track_name']} - {track_info['artists']}\n⏳ جاري التحضير...")
                            # Get player using the search query
                            player = await YTDLSource.from_url(track_info['search_query'], loop=bot.loop, stream=True)
                            
                            # Create rich embed
                            embed = discord.Embed(
                                title="🎵 جاري التشغيل من Spotify",
                                description=f"**{track_info['track_name']}**\nبواسطة {track_info['artists']}",
                                color=discord.Color.green()
                            )
                            
                            if track_info['album_art']:
                                embed.set_thumbnail(url=track_info['album_art'])
                            
                            embed.add_field(name="الألبوم", value=track_info['album_name'], inline=True)
                            minutes = track_info['duration_ms'] // 60000
                            seconds = (track_info['duration_ms'] % 60000) // 1000
                            embed.add_field(name="المدة", value=f"{minutes}:{seconds:02d}", inline=True)
                            
                        else:
                            await ctx.send("❌ لم يتم العثور على المقطع في Spotify")
                            return
                    
                    elif 'playlist' in query:
                        await status_msg.edit(content="⏳ جاري تحميل قائمة التشغيل من Spotify...")
                        tracks = await get_spotify_playlist_tracks(query)
                        if not tracks:
                            await ctx.send("❌ لم يتم العثور على قائمة التشغيل في Spotify")
                            return
                            
                        # For now, just play the first track
                        track = tracks[0]
                        await status_msg.edit(content=f"🎵 تم العثور على قائمة التشغيل\n⏳ جاري تحضير: {track['track_name']}")
                        player = await YTDLSource.from_url(track['search_query'], loop=bot.loop, stream=True)
                        
                        # Create embed for playlist
                        embed = discord.Embed(
                            title="🎵 جاري التشغيل من قائمة Spotify",
                            description=f"**{track['track_name']}**\nبواسطة {track['artists']}",
                            color=discord.Color.green()
                        )
                        embed.set_footer(text=f"المقطع 1 من {len(tracks)}")
                        
                else:
                    # Regular YouTube playback
                    player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
                    
                    # Create regular embed
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