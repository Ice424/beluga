# audio_manager.py
import vlc
import os
from tools.track import Track


class AudioManager:
    def __init__(self, audio_file: str | None = None):
        self.audio_file = audio_file
    
        self.vlc_instance: vlc.EventManager = vlc.Instance()
        if not self.vlc_instance:
            raise
     
        self.player = self.vlc_instance.media_player_new()
        if audio_file:
            media = self.vlc_instance.media_new(audio_file)
            self.player.set_media(media)
        
        self.saved_audio_value = None
        self.is_playing = False
        self.track: Track | None = None
        
        self._observers = []
        
    def subscribe(self, observer):
        self._observers.append(observer)

    def _notify(self, event_name: str, **kwargs):
        for obs in self._observers:
            getattr(obs, f"on_{event_name}")(**kwargs)
        

    def load_file(self, file):
        self.player.stop()
        media = self.vlc_instance.media_new(file)
        
        self.track = Track.from_file(file)
        self.player.set_media(media)
        self.audio_file = file
        print(self.track)
        self._notify("track_change", track = self.track)
    
    def test_file(self):
        if self.audio_file is None:
            raise FileNotFoundError(f"Audio file is None")
        if not os.path.exists(self.audio_file):
            raise FileNotFoundError(f"Audio file not found: {self.audio_file}")
        return True
    
    def toggle_playback(self) -> bool:
        self.test_file()
        """Play or pause the audio."""
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
        else:
            self.player.play()
            self.is_playing = True
        self._notify("state_change", is_playing = self.is_playing)
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
        
        return self.player.get_time() / 1000

    def get_duration(self) -> float:
        self.test_file()
        return self.player.get_length() / 1000

    def set_volume(self, volume: int):

        self.player.audio_set_volume(volume)
        self._notify("volume_change", volume=volume)
    
    def get_volume(self) -> int:
        volume = self.player.audio_get_volume()
        return volume
    
    def stop(self):
        self.player.stop()
        
    

