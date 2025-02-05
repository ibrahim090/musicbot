import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from utils.spotify_handler import SpotifyHandler
from utils.youtube_handler import YTDLSource
import asyncio

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

# Initialize Spotify handler
spotify_handler = SpotifyHandler(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

# Initialize bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

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
            try:
                await ctx.author.voice.channel.connect()
                # Add a small delay to ensure connection is established
                await asyncio.sleep(1)
            except Exception as e:
                return await ctx.send(f"❌ حدث خطأ أثناء الاتصال بالقناة الصوتية: {str(e)}")

        # Verify voice connection
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return await ctx.send("❌ لم يتم الاتصال بالقناة الصوتية بشكل صحيح. الرجاء المحاولة مرة أخرى.")

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
                        track_info, error_msg = await spotify_handler.get_track_info(query)
                        if not track_info:
                            await status_msg.edit(content=error_msg or "❌ حدث خطأ غير معروف")
                            return
                        
                        # Update status message
                        await status_msg.edit(content=f"🎵 تم العثور على: {track_info['track_name']} - {track_info['artists']}\n⏳ جاري التحضير...")
                        
                        try:
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
                            
                            # Play audio
                            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
                            
                            # Update status message
                            await status_msg.edit(content=None, embed=embed)
                            
                        except Exception as e:
                            print(f"Error playing track: {str(e)}")
                            await ctx.send(f"❌ حدث خطأ أثناء تشغيل المقطع: {str(e)}")
                        
                    elif 'playlist' in query:
                        # Handle Spotify playlist
                        playlist_info = await spotify_handler.get_playlist_tracks(query)
                        if playlist_info and playlist_info['tracks']:
                            await status_msg.edit(content=f"📝 تم العثور على قائمة التشغيل: {playlist_info['name']}\n⏳ جاري تحضير المقطع الأول...")
                            
                            # Get first track
                            track = playlist_info['tracks'][0]
                            
                            try:
                                # Get player for first track
                                player = await YTDLSource.from_url(track['search_query'], loop=bot.loop, stream=True)
                                
                                # Create embed for playlist
                                embed = discord.Embed(
                                    title="🎵 جاري التشغيل من قائمة Spotify",
                                    description=f"**{track['track_name']}**\nبواسطة {track['artists']}",
                                    color=discord.Color.green()
                                )
                                
                                if track['album_art']:
                                    embed.set_thumbnail(url=track['album_art'])
                                
                                embed.add_field(name="الألبوم", value=track['album_name'], inline=True)
                                minutes = track['duration_ms'] // 60000
                                seconds = (track['duration_ms'] % 60000) // 1000
                                embed.add_field(name="المدة", value=f"{minutes}:{seconds:02d}", inline=True)
                                embed.set_footer(text=f"المقطع 1 من {len(playlist_info['tracks'])} | {playlist_info['name']}")
                                
                                # Play audio
                                ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
                                
                                # Update status message
                                await status_msg.edit(content=None, embed=embed)
                                
                            except Exception as e:
                                print(f"Error playing playlist track: {str(e)}")
                                await ctx.send(f"❌ حدث خطأ أثناء تشغيل المقطع: {str(e)}")
                            
                        else:
                            await status_msg.edit(content="❌ لم يتم العثور على قائمة التشغيل في Spotify. تأكد من صحة الرابط وأن القائمة متاحة.")
                            return
                            
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
                await status_msg.edit(content=f"❌ حدث خطأ: {str(e)}")
                print(f"Error in play command: {str(e)}")

    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {str(e)}")
        print(f"Error in play command: {str(e)}")

@bot.command(name='pause', help='إيقاف مؤقت')
async def pause(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        return await ctx.send("❌ البوت غير متصل بأي قناة صوتية!")
    
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ تم الإيقاف المؤقت")
    else:
        await ctx.send("❌ لا يوجد شيء قيد التشغيل!")

@bot.command(name='resume', help='استئناف التشغيل')
async def resume(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        return await ctx.send("❌ البوت غير متصل بأي قناة صوتية!")
    
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ تم استئناف التشغيل")
    else:
        await ctx.send("❌ لا يوجد شيء متوقف مؤقتاً!")

@bot.command(name='stop', help='إيقاف التشغيل')
async def stop(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        return await ctx.send("❌ البوت غير متصل بأي قناة صوتية!")
    
    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        ctx.voice_client.stop()
        await ctx.send("⏹️ تم إيقاف التشغيل")
    else:
        await ctx.send("❌ لا يوجد شيء قيد التشغيل!")

@bot.command(name='leave', help='مغادرة القناة الصوتية')
async def leave(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        return await ctx.send("❌ البوت غير متصل بأي قناة صوتية!")
    
    await ctx.voice_client.disconnect()
    await ctx.send("👋 تمت المغادرة")

if __name__ == "__main__":
    print("Starting bot...")
    bot.run(token) 