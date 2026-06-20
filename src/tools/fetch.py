import aiohttp
import asyncio
from typing import TYPE_CHECKING
import acoustid

if TYPE_CHECKING:
    from tools.track import Track
    from tools.library_manager import LibraryManager


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
    def __init__(self, track: Track, observer, library_manger:LibraryManager|None = None) -> None:
        self.observer = observer
        self.library_manager = library_manger
        self.update_library = False
        self.track = track
        asyncio.create_task(self.get_cover())
    async def get_cover(self):
        if self.library_manager:
            cover_url = self.library_manager.get_cover_url(self.track)
            if cover_url:
                await getattr(self.observer, "on_cover_received")(cover_url)
                return
            self.update_library = True
        
        if not self.track.release_mbid:
            GenIDs(self.track, self)
            return
        else:
            id = self.track.release_mbid
        await self.lookup_cover(id)
        
    async def lookup_cover(self, id):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://coverartarchive.org/release/{id}") as covers_response:
                covers = await covers_response.json(content_type=None)
        print(covers)
        cover = covers["images"][0]["image"]
        
        if self.update_library and self.library_manager:
            self.library_manager.set_cover_url(self.track,cover)
            
        if self.observer:
            await getattr(self.observer, "on_cover_received")(cover)
            
    async def on_gen_ids(self, release_id, recording_id, acoust_id, artist_id):
        await self.lookup_cover(release_id)

class GenIDs():
    def __init__(self, track: Track, observer, library_manger: LibraryManager|None = None) -> None:
        self.observer = observer
        self.library_manager = library_manger
        asyncio.create_task(self.get_id(track))
    async def get_id(self, track:Track):
        data = acoustid.lookup("wyJ5f3DJ1C" , track.chromaprint, track.duration)
        if data["status"] == "ok" and len(data["results"]) != 0:
            data = data["results"][0]
        else:
            print(f"Failed to lookup: {track}")
            print(data)
            return
        acoust_id = data["id"]
        recording_id = data["recordings"][0]["id"]
        artist_id = ""
        
        url = f"https://musicbrainz.org/ws/2/recording/{recording_id}?inc=releases&fmt=json"
        if "artists" in data["recordings"][0]:
            artist_id = data["recordings"][0]["artists"][0]["id"]
        else:
            url = f"https://musicbrainz.org/ws/2/recording/{recording_id}?inc=artist-credits%2Breleases&fmt=json"
        
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as recording_lookup:
                recording_response = await recording_lookup.json()
        
        if not artist_id:
            artist_id = recording_response["artist-credit"][0]["artist"]["id"]
        
        release = self.find_preferred_release(recording_response["releases"])
        release_id = release["id"]
        
        if self.observer:
            await getattr(self.observer, "on_gen_ids")(release_id, recording_id, acoust_id, artist_id)
    
    


    def find_preferred_release(self, releases: list[dict]) -> dict:
        def score(r):
            lang = r.get("text-representation", {}).get("language")

            return (
                lang == "eng",
                r.get("status") == "Official",
                r.get("country") == "XW",
                r.get("date", "")
            )
        release = max(releases, key=score, default=None)
        if release:
            return release
        return releases[0]

        
        