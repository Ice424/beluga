import asyncio
import time
from tools.fetch import GetCover
from pypresence.presence import AioPresence
from pypresence.types import ActivityType, StatusDisplayType
from pypresence.exceptions import PipeClosed, InvalidPipe


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from audio_manager import AudioManager
    from tools.track import Track as TR


class PresenceManager:
    def __init__(self, audio_manager: AudioManager) -> None:
        client_id = "1497704959377146047"
        self.RPC = AioPresence(client_id)
        self.start = int(time.time())
        self.audio_manager = audio_manager
        self.track_title = "Not Playing"
        self.track_artist = "Beluga"
        self.cover_url = ""
        self.track_duration = 0
        self.end = +self.start + 999
        self.audio_manager.subscribe(self)
        self.is_playing = False
        if audio_manager.track:
            self.track_duration = audio_manager.track.duration
            self.track_title = audio_manager.track.title
            self.track_artist = audio_manager.track.artists
            self.end = self.start + int(audio_manager.track.duration)

            GetCover(audio_manager.track, self)

    async def update_loop(self):
        attempts = 0
        await self.RPC.connect()
        self.connected = True

        while self.connected:
            try:
                await self.update()
            except PipeClosed, InvalidPipe:
                if attempts <= 3:
                    await asyncio.sleep(30)
                    attempts += 1
                else:
                    self.connected = False
            await asyncio.sleep(15)

    def on_track_change(self, track: TR):
        if track:
            self.track_duration = track.duration
            self.track_title = track.title
            self.track_artist = track.artist
            self.start = int(time.time())
            self.end = self.start + int(self.track_duration)
    
            GetCover(track, self)

    def on_position_change(self, position):
        asyncio.create_task(self.update())

    async def on_cover_received(self, cover):
        self.cover_url = cover
        await self.update()

    def on_state_change(self, is_playing):
        self.is_playing = is_playing
        asyncio.create_task(self.update())

    async def update(self):
        self.start = int(time.time()) - self.audio_manager.get_position()
        self.end = self.start + int(self.audio_manager.get_duration())
        if self.is_playing:
            await self.RPC.update(
                activity_type=ActivityType.LISTENING,
                status_display_type=StatusDisplayType.DETAILS,
                details=self.track_title,
                state=self.track_artist,
                large_url="https://github.com/Ice424/beluga",
                large_image=self.cover_url,
                start=self.start,
                end=self.end,
            )
        else:
            await self.RPC.update(
                activity_type=ActivityType.LISTENING,
                status_display_type=StatusDisplayType.DETAILS,
                details=self.track_title,
                state=self.track_artist,
                large_url="https://github.com/Ice424/beluga",
                large_image=self.cover_url,
                start=None,
                end=None,
            )
            
