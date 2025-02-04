import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp as youtube_dl
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG for more detailed logs
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)  # Changed to DEBUG for more detailed logs

# Load environment variables
print("Loading environment variables...")
load_dotenv()

# Get the token
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("Error: No token found in .env file!")
    exit(1)
print(f"Token loaded: {token[:20]}...")

# FFmpeg path - for Railway deployment
FFMPEG_PATH = os.getenv('FFMPEG_PATH', 'ffmpeg')
print(f"FFmpeg path: {FFMPEG_PATH}")

# YouTube DL Options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': True,  # Changed to True for more logs
    'quiet': False,  # Changed to False for more logs
    'no_warnings': False,  # Changed to False for more logs
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    # Add these options to bypass age restriction and other limitations
    'no_check_certificate': True,
    'http_chunk_size': 10485760,
    'extractor_retries': 3,
    'socket_timeout': 30,
    'external_downloader_args': [],
    'youtube_include_dash_manifest': False,
    'cachedir': False
}

# Create a custom HTTP header to mimic a web browser
custom_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5',
    'Sec-Fetch-Mode': 'navigate',
}
ytdl_format_options['http_headers'] = custom_headers

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# Bot configuration
print("Setting up bot...")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    for guild in bot.guilds:
        print(f'- {guild.name} (id: {guild.id})')

@bot.command(name='join', help='Joins a voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send('أنت لست متصل بقناة صوتية!')
        return
    
    channel = ctx.message.author.voice.channel
    print(f"Joining voice channel: {channel.name}")
    await channel.connect()

@bot.command(name='leave', help='Leaves the voice channel')
async def leave(ctx):
    if not ctx.voice_client:
        await ctx.send("البوت غير متصل بأي قناة صوتية!")
        return
    
    print(f"Leaving voice channel in {ctx.guild.name}")
    await ctx.voice_client.disconnect()
    await ctx.send("تم مغادرة القناة الصوتية")

@bot.command(name='play', help='Plays a song')
async def play(ctx, *, url: str):
    print(f"Received play command with URL: {url}")
    
    if not ctx.message.author.voice:
        await ctx.send('أنت لست متصل بقناة صوتية!')
        return

    if not ctx.voice_client:
        print("Bot not in voice channel, joining now...")
        try:
            await ctx.author.voice.channel.connect()
            print("Successfully joined voice channel")
        except Exception as e:
            print(f"Error joining voice channel: {str(e)}")
            await ctx.send("حدث خطأ أثناء الانضمام للقناة الصوتية!")
            return

    try:
        async with ctx.typing():
            print("Extracting video info...")
            try:
                # Get video info and stream URL
                data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                print("Successfully extracted video info")
                
                if 'entries' in data:
                    # Take first item from a playlist
                    data = data['entries'][0]

                stream_url = data['url']
                title = data['title']
                print(f"Got stream URL for: {title}")

                ctx.voice_client.stop()
                voice_client = ctx.voice_client
                print(f"Starting playback with FFmpeg at path: {FFMPEG_PATH}")
                try:
                    voice_client.play(discord.FFmpegPCMAudio(executable=FFMPEG_PATH, source=stream_url, **ffmpeg_options))
                    print("Successfully started playback")
                    await ctx.send(f'**جاري تشغيل:** {title}')
                except Exception as e:
                    print(f"Error during playback: {str(e)}")
                    await ctx.send(f"حدث خطأ أثناء التشغيل: {str(e)}")
            except Exception as e:
                print(f"Error extracting video info: {str(e)}")
                await ctx.send(f"حدث خطأ أثناء استخراج معلومات الفيديو: {str(e)}")
    except Exception as e:
        print(f"Error in play command: {str(e)}")
        await ctx.send("حدث خطأ أثناء تشغيل الأغنية!")

@bot.command(name='pause', help='Pauses the current song')
async def pause(ctx):
    if not ctx.voice_client:
        await ctx.send("البوت غير متصل بأي قناة صوتية!")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("لا يوجد شيء قيد التشغيل!")
        return

    print("Pausing playback")
    ctx.voice_client.pause()
    await ctx.send("تم إيقاف الأغنية مؤقتاً ⏸️")

@bot.command(name='resume', help='Resumes the current song')
async def resume(ctx):
    if not ctx.voice_client:
        await ctx.send("البوت غير متصل بأي قناة صوتية!")
        return
    
    if not ctx.voice_client.is_paused():
        await ctx.send("الأغنية ليست متوقفة مؤقتاً!")
        return

    print("Resuming playback")
    ctx.voice_client.resume()
    await ctx.send("تم استئناف التشغيل ▶️")

@bot.command(name='stop', help='Stops the current song')
async def stop(ctx):
    if not ctx.voice_client:
        await ctx.send("البوت غير متصل بأي قناة صوتية!")
        return
    
    if not ctx.voice_client.is_playing():
        await ctx.send("لا يوجد شيء قيد التشغيل!")
        return

    print("Stopping playback")
    ctx.voice_client.stop()
    await ctx.send("تم إيقاف التشغيل ⏹️")

print("Starting bot...")
try:
    # Run the bot
    bot.run(token)
except Exception as e:
    print(f"Error starting bot: {str(e)}")
    print("Token used:", token) 