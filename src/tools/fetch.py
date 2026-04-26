import aiohttp
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.track import Track


class GetLyrics():
    def __init__(self, track, observer) -> None:
        self.observer = observer
        asyncio.create_task(self.get_lyrics(track))

            

    async def get_lyrics(self, track: "Track"):
        request = {
            "track_name": track.title,
            "artist_name": track.artist,
            "album_name": track.album,
            "duration": track.duration,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get("https://lrclib.net/api/get", params=request) as response:
                lyrics = await response.json()
        lyrics = lyrics["syncedLyrics"]
        if self.observer:
            getattr(self.observer, "on_lyrics_received")(lyrics)
    
   

class Receive():
    def on_lyrics_received(self,lyrics):
        print(lyrics)
    async def test(self):
        from tools.track import Track
        track = Track.from_file("/home/ice424/Music/Prefer not to say/depressed hermit girl touches grass - Tanger, ISSBROKIE.flac")
        GetLyrics(track, self)
        print("Fetching lyrics in background...")
        await asyncio.sleep(100) 

class GetCover():
    def __init__(self, track, observer) -> None:
        self.observer = observer
        asyncio.create_task(self.get_cover(track))
    async def get_cover(self, track):
        request = {
            "fmt": "json",
            "query": f"alias:{track.title} artist:{track.artists}",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get("https://musicbrainz.org/ws/2/recording", params=request) as search_response:
                search = await search_response.json()
        id = search["recordings"][0]["releases"][0]["id"]
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://coverartarchive.org/release/{id}") as covers_response:
                covers = await covers_response.json()
        cover = covers["images"][0]["thumbnails"]["250"]
        if self.observer:
            await getattr(self.observer, "on_cover_received")(cover)