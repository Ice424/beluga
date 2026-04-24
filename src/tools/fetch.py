import aiohttp
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.track import AutoTrack


class GetLyrics():
    def __init__(self, track, observer) -> None:
        self.observer = observer
        asyncio.create_task(self.get_lyrics(track))

            

    async def get_lyrics(self, track: "AutoTrack"):
        request = {
            "track_name": track.title,
            "artist_name": track.raw_artist,
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
        from tools.track import AutoTrack
        track = AutoTrack("/home/ice424/Music/Prefer not to say/depressed hermit girl touches grass - Tanger, ISSBROKIE.flac")
        GetLyrics(track, self)
        print("Fetching lyrics in background...")
        await asyncio.sleep(100) 



    