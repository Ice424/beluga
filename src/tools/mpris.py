import asyncio
import logging
import mpris_server
from mpris_server.adapters import MprisAdapter
from mpris_server.server import Server
from mpris_server import Metadata, PlayState, Position, Track, Rate, Volume, DbusObj, EventAdapter

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from audio_manager import AudioManager
    from tools.track import Track as TR


class MprisPlayer(MprisAdapter):
    def __init__(self, AudioManager):
        self.audio: AudioManager = AudioManager


        self.data = Metadata()
        self.data["xesam:title"] = "Test Track"
        self.data["xesam:album"] = "Test Album"
        self.data["xesam:artist"] = ["Test Artist"]

    

    def play(self):
        self.audio.play()

    def pause(self):
        self.audio.pause()

    def next(self):
        print("next track")

    def previous(self):
        print("previous track")

    def metadata(self):
        return self.data

    def get_playstate(self) -> PlayState:
        if self.audio.is_playing:
            return PlayState.PLAYING
        return PlayState.STOPPED

    def can_quit(self) -> bool:
        return True

    def can_control(self) -> bool:
        return True

    def can_go_next(self) -> bool:
        return True

    def can_go_previous(self) -> bool:
        return True

    def can_pause(self) -> bool:
        return True

    def can_play(self) -> bool:
        return True

    def can_seek(self) -> bool:
        return False

    def get_art_url(self, track: DbusObj | Track | None) -> str:
        return "file:///home/ice424/Downloads/small.jpg"
   
        
    def get_current_position(self) -> Position:
        try:
            return Position(self.audio.get_position()*1000000)
        except FileNotFoundError:
            return Position(0)
    def get_rate(self) -> Rate:
        return Rate(1)

    def get_maximum_rate(self) -> Rate:
        return Rate(1)

    def get_minimum_rate(self) -> Rate:
        return Rate(1)

    def get_shuffle(self) -> bool:
        return False

    def get_volume(self) -> Volume:
        return Volume(self.audio.get_volume())

    def is_mute(self) -> bool:
        return False

    def is_playlist(self) -> bool:
        return False

    def is_repeating(self) -> bool:
        return False

    def open_uri(self, uri: str):
        pass

    def resume(self):
        self.play()

    def seek(self, time: Position, track_id: DbusObj | None = None):
        print("SEEK")
        print(time)
        self.audio.set_position(time)

    def set_maximum_rate(self, value: Rate):
        print("max rate")

    def set_minimum_rate(self, value: Rate):
        print("min rate")

    def set_mute(self, value: bool):
        print("mute")

    def set_rate(self, value: Rate):
        print("rate")
        pass
    


    def set_repeating(self, value: bool):
        print("repeating")

    def set_shuffle(self, value: bool):
        print("shuffle")

    def set_volume(self, value: Volume):
        print("volume")

    def stop(self):
        self.pause()
        


class MprisEvents(EventAdapter):
    pass

   

class MprisController:
    def __init__(self, audio_manager: "AudioManager") -> None:
        self.audio = audio_manager
        self.player = MprisPlayer(audio_manager)
        
        self.audio.subscribe(self)
        
        self.mpris = Server("MyPythonPlayer", adapter=self.player)
        self.mpris.publish()
        self.event_handler = MprisEvents(self.mpris.root, self.mpris.player)
        self.mpris.loop(background=True)

 



        
        
    def on_state_change(self, is_playing: bool):
        self.event_handler.on_playback()
        
        pass

    def on_track_change(self, track: "TR"):
        self.player.data["xesam:title"] = str(track.title) # type: ignore
        self.player.data["xesam:album"] = str(track.album) # type: ignore
        self.player.data["xesam:artist"] = [str(track.artist)] # type: ignore
        self.player.data["mpris:artUrl"] = "file:///" + str(track.cover_path) # type: ignore
        self.player.data["mpris:length"] = int(track.duration * 1000000) # type: ignore
        self.event_handler.on_title()
      
    def on_position_change(self, position: float):
        self.event_handler.on_seek(Position(position * 1000000))
        pass

    def on_volume_change(self, volume: int):

        pass