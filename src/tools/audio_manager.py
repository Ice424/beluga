# audio_manager.py
import vlc
import os
from tools.track import Track


class AudioManager:
    def __init__(
        self,
        page,
        audio_file: str | None = None,
    ):
        self.audio_file = audio_file
        self._observers = []
        self.saved_audio_value = None
        self.is_playing = False
        self.track: Track | None = None
        self.page = page
        
        self.vlc_instance: vlc.Instance = vlc.Instance()
        if not self.vlc_instance:
            raise

        self.player: vlc.MediaPlayer = self.vlc_instance.media_player_new()
        self.media: vlc.Media = self.vlc_instance.media_new_as_node("temp")
        if audio_file:
            self.load_file(audio_file)

    def subscribe(self, observer):
        self._observers.append(observer)

    def _notify(self, event_name: str, **kwargs):
        
        for obs in self._observers:
            try:
                getattr(obs, f"on_{event_name}")(**kwargs)
            except Exception:
                pass

    def load_file(self, file):
        self.player.stop()
        self.media: vlc.Media = self.vlc_instance.media_new(file)
 
        self.media.parse()
        
        self.track = Track.from_file(file)
        self.player.set_media(self.media)
        
        self.audio_file = file
        print(self.track)
        self._notify("track_change", track=self.track)

    def load_track(self, track: "Track"):
        self.player.stop()
        self.audio_file = track.file_path
        self.media: vlc.Media = self.vlc_instance.media_new(self.audio_file)

        self.media.parse()

        self.track = track
        self.player.set_media(self.media)
        print(self.track)
        print(self.track.artists)
        self._notify("track_change", track=self.track)

    def test_file(self):
        if self.audio_file is None:
            raise FileNotFoundError(f"Audio file is None")
        if not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file not found: {self.audio_file}")
        return True

    def toggle_playback(self) -> bool:
        """Play or pause the audio."""
        self.test_file()

        if self.is_playing:
            self.player.pause()
            self.is_playing = False
        else:
            self.player.play()
            self.is_playing = True
        self._notify("state_change", is_playing=self.is_playing)
        return self.is_playing

    def play(self):
        self.test_file()
        self.player.play()
        self.is_playing = True
        self._notify("state_change", is_playing=True)

    def pause(self):
        self.test_file()
        self.player.pause()
        self.is_playing = False
        self._notify("state_change", is_playing=False)

    def set_position(self, seconds: float):
        self.test_file()
        self.player.set_time(int(seconds * 1000))
        self._notify("position_change", position=seconds)

    def get_position(self) -> float:
        self.test_file()
        pos = self.player.get_time() / 1000 
        if pos <= self.get_duration(): #vlc why do you do this
            return pos
        return 0.0

    def get_duration(self) -> float:
        self.test_file()
        return self.media.get_duration() / 1000

    def set_volume(self, volume: int):

        self.player.audio_set_volume(volume)
        self._notify("volume_change", volume=volume)

    def get_volume(self) -> int:
        volume = self.player.audio_get_volume()
        return volume

    def stop(self):
        self.player.stop()
