import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config.config import SPOTIFY_PATTERNS

class SpotifyHandler:
    def __init__(self, client_id=None, client_secret=None):
        self.sp = None
        self.client_id = client_id
        self.client_secret = client_secret
        if client_id and client_secret:
            try:
                self.sp = spotipy.Spotify(
                    client_credentials_manager=SpotifyClientCredentials(
                        client_id=client_id,
                        client_secret=client_secret
                    )
                )
                print("Spotify client initialized successfully")
            except Exception as e:
                print(f"Error initializing Spotify client: {str(e)}")
        else:
            print("No Spotify credentials provided")

    async def get_track_info(self, url):
        """Get track information from Spotify URL"""
        if not self.sp:
            print("Spotify client not initialized - checking credentials")
            if not self.client_id or not self.client_secret:
                print("Missing Spotify credentials")
                return None, "❌ لم يتم تكوين حساب Spotify بشكل صحيح"
            else:
                print(f"Credentials present but client failed to initialize")
                return None, "❌ فشل الاتصال بـ Spotify"
        
        try:
            # Extract track ID from URL
            track_match = re.match(SPOTIFY_PATTERNS['track'], url)
            if not track_match:
                print(f"Invalid Spotify track URL format: {url}")
                return None, "❌ رابط Spotify غير صالح. تأكد من نسخ الرابط بشكل صحيح"
                
            track_id = track_match.group(1)
            print(f"Attempting to get track info for ID: {track_id}")
            
            try:
                track_info = self.sp.track(track_id)
                print("Successfully retrieved track info from Spotify")
            except spotipy.exceptions.SpotifyException as e:
                print(f"Spotify API error: {str(e)}")
                if "not found" in str(e).lower():
                    return None, "❌ لم يتم العثور على المقطع. قد يكون غير متاح في منطقتك أو تم إزالته"
                elif "forbidden" in str(e).lower():
                    return None, "❌ لا يمكن الوصول إلى المقطع. تأكد من أنه متاح في منطقتك"
                return None, f"❌ حدث خطأ في Spotify: {str(e)}"
            
            # Check if track is playable
            if not track_info.get('is_playable', True):
                return None, "❌ هذا المقطع غير متاح للتشغيل في منطقتك"
            
            # Format artist and track name for YouTube search
            artists = ", ".join([artist['name'] for artist in track_info['artists']])
            track_name = track_info['name']
            search_query = f"{artists} - {track_name} official audio"
            
            print(f"Generated search query: {search_query}")
            
            return {
                'search_query': search_query,
                'track_name': track_name,
                'artists': artists,
                'duration_ms': track_info['duration_ms'],
                'album_name': track_info['album']['name'],
                'album_art': track_info['album']['images'][0]['url'] if track_info['album']['images'] else None
            }, None
            
        except Exception as e:
            print(f"Unexpected error getting Spotify track info: {str(e)}")
            return None, f"❌ حدث خطأ غير متوقع: {str(e)}"

    async def get_playlist_tracks(self, url):
        """Get all tracks from a Spotify playlist"""
        if not self.sp:
            print("Spotify client not initialized")
            return None
            
        try:
            # Extract playlist ID from URL
            playlist_match = re.match(SPOTIFY_PATTERNS['playlist'], url)
            if not playlist_match:
                print("Invalid Spotify playlist URL")
                return None
                
            playlist_id = playlist_match.group(1)
            print(f"Getting playlist info for ID: {playlist_id}")
            
            # Get playlist info
            playlist_info = self.sp.playlist(playlist_id)
            playlist_name = playlist_info['name']
            
            # Get all tracks
            tracks = []
            results = self.sp.playlist_tracks(playlist_id)
            
            while results:
                for item in results['items']:
                    if item['track']:
                        track = item['track']
                        artists = ", ".join([artist['name'] for artist in track['artists']])
                        tracks.append({
                            'search_query': f"{artists} - {track['name']} official audio",
                            'track_name': track['name'],
                            'artists': artists,
                            'duration_ms': track['duration_ms'],
                            'album_name': track['album']['name'],
                            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None
                        })
                
                if results['next']:
                    results = self.sp.next(results)
                else:
                    break
                    
            print(f"Found {len(tracks)} tracks in playlist: {playlist_name}")
            return {
                'name': playlist_name,
                'tracks': tracks
            }
        except Exception as e:
            print(f"Error getting Spotify playlist: {str(e)}")
            return None 