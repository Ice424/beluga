from mpris_server.server import Server
from mpris_server.adapters import Metadata


class MPRISController:

    def __init__(self, audio_manager):
        self.audio = audio_manager
        self.server = Server("fletmusicplayer")

        self.server.on_play = self.play
        self.server.on_pause = self.pause
        self.server.on_next = self.next
        self.server.on_previous = self.previous
        self.server.on_seek = self.seek

        self.server.publish()

    def update_metadata(self, title, artist, album, art_url, length):

        self.server.metadata = Metadata(
            title=title,
            artist=[artist],
            album=album,
            art_url=art_url,
            length=length * 1_000_000
        )

    def update_playback(self):
        self.server.playback_status = (
            "Playing" if self.audio.is_playing else "Paused"
        )

        self.server.position = int(self.audio.get_position() * 1_000_000)

    def play(self):
        self.audio.play()
        self.update_playback()

    def pause(self):
        self.audio.pause()
        self.update_playback()

    def next(self):
        print("Next track requested")
        # hook queue manager here

    def previous(self):
        print("Previous track requested")

    def seek(self, offset):
        seconds = offset / 1_000_000
        self.audio.set_position(self.audio.get_position() + seconds)