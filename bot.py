import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp
import logging
import asyncio
import tempfile

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
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'cachedir': False,
    'cookies-from-browser': 'chrome',
    'geo-bypass': True,
    'geo-bypass-country': 'US'
}

# Initialize bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        
        # Create a temporary directory for cookies
        temp_dir = tempfile.mkdtemp()
        cookies_path = os.path.join(temp_dir, 'cookies.txt')
        
        # Update options with cookies path
        ytdl_opts = dict(YTDL_OPTIONS)
        ytdl_opts['cookiefile'] = cookies_path
        
        try:
            # First try to extract cookies from Chrome
            print("Attempting to extract cookies from Chrome...")
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                try:
                    # Extract video info
                    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
                    
                    if 'entries' in data:
                        data = data['entries'][0]

                    filename = data['url'] if stream else ytdl.prepare_filename(data)
                    return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)
                    
                except Exception as e:
                    print(f"Error with Chrome cookies: {str(e)}")
                    # If Chrome fails, try without cookies
                    ytdl_opts.pop('cookies-from-browser', None)
                    ytdl_opts.pop('cookiefile', None)
                    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
                    
                    if 'entries' in data:
                        data = data['entries'][0]

                    filename = data['url'] if stream else ytdl.prepare_filename(data)
                    return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)
                    
        except Exception as e:
            print(f"Error in YTDLSource.from_url: {str(e)}")
            raise e
        finally:
            # Cleanup
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    for guild in bot.guilds:
        print(f'- {guild.name}')

@bot.command(name='play', help='تشغيل مقطع صوتي')
async def play(ctx, *, url):
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
                status_msg = await ctx.send("جاري تحميل المقطع...")

                # Get player
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
                
                # Play audio
                ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

                # Update status message
                await status_msg.edit(content=f'**جاري تشغيل:** {player.title}')
                
            except Exception as e:
                await ctx.send(f"حدث خطأ: {str(e)}")
                print(f"Error in play command: {str(e)}")

    except Exception as e:
        await ctx.send(f"حدث خطأ: {str(e)}")
        print(f"Error in play command: {str(e)}")

@bot.command(name='pause', help='إيقاف مؤقت')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("تم الإيقاف المؤقت ⏸️")
    else:
        await ctx.send("لا يوجد شيء قيد التشغيل!")

@bot.command(name='resume', help='استئناف التشغيل')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("تم استئناف التشغيل ▶️")
    else:
        await ctx.send("لا يوجد شيء متوقف مؤقتاً!")

@bot.command(name='stop', help='إيقاف التشغيل')
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("تم إيقاف التشغيل ⏹️")
    else:
        await ctx.send("لا يوجد شيء قيد التشغيل!")

@bot.command(name='leave', help='مغادرة القناة الصوتية')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("تمت المغادرة 👋")
    else:
        await ctx.send("لست في قناة صوتية!")

print("Starting bot...")
bot.run(token) 