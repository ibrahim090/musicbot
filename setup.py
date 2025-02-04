from setuptools import setup, find_packages

setup(
    name="discord-music-bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'discord.py[voice]>=2.3.2',
        'python-dotenv>=1.0.1',
        'yt-dlp>=2023.12.30',
        'spotipy>=2.23.0',
        'PyNaCl>=1.5.0',
        'ffmpeg-python>=0.2.0',
    ],
) 