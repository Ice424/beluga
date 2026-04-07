import asyncio
import flet as ft
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.audio_manager import AudioManager


class Playbar(ft.Row):
    class _SongInfo(ft.Row):
        def __init__(self) -> None:
            super().__init__()
            self.SongName = "Somewhere Someday"
            self.ArtistName = "Tanger"
            self.AlbumName = "Prefer Not To Say"
            self.expand = True
            self.controls = [
                ft.Image(
                    src="/home/ice424/Downloads/small.jpg",
                    width=50,
                    height=50,
                    border_radius=6,
                ),
                ft.Stack(
                    expand=True,
                    clip_behavior=ft.ClipBehavior.NONE,
                    controls=[
                        ft.Column(
                            spacing=0,
                            controls=[
                                ft.Text(
                                    self.SongName,
                                    weight=ft.FontWeight.BOLD,
                                    overflow=ft.TextOverflow.CLIP,
                                    no_wrap=True
                                ),
                                ft.Text(
                                    self.ArtistName,
                                    size=10,
                                    overflow=ft.TextOverflow.CLIP,
                                    no_wrap=True
                                ),
                                ft.Text(
                                    self.AlbumName,
                                    size=10,
                                    overflow=ft.TextOverflow.CLIP,
                                    no_wrap=True
                                ),
                            ],
                        )
                    ],
                ),
            ]

    def __init__(self, page: ft.Page, audio_manager: AudioManager) -> None:
        super().__init__()
        self.main_page = page
        self.audio = audio_manager
        self.SongInfo = self._SongInfo()
        self.saved_audio_value: None | int = None
        
        self.shuffle = False
        self.loop: int = 0
        
        ## BUTTONS
        self.play_button = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED,
            icon_size=40,
            on_click=self.toggle_play,
        )
        self.prev_button = ft.IconButton(icon=ft.Icons.SKIP_PREVIOUS)
        self.next_button = ft.IconButton(icon=ft.Icons.SKIP_NEXT)
        self.shuffle_button = ft.IconButton(icon=ft.Icons.SHUFFLE, on_click=self.on_shuffle_click)
        self.loop_button = ft.IconButton(
            icon=ft.Icons.REPEAT_ROUNDED, margin=ft.Margin(left=0, right=30), on_click=self.on_loop_click
        )
        self.time_label = ft.Text("00:00", margin=ft.Margin(right=10))
        self.scrubber = ft.Slider(
            padding=0,
            min=0,
            max=100,
            value=0,
            expand=True,
            on_change=self.on_scrubber_change,
            margin=ft.Margin(left=0, right=0),
        )
        self.song_length = ft.Text("00:00", margin=ft.Margin(left=0))

        self.volume_button = ft.IconButton(
            on_click=self.on_volume_click,
            icon=ft.Icons.VOLUME_UP_ROUNDED,
            margin=ft.Margin(left=10, right=0),
        )
        self.volume_slider = ft.Slider(
            on_change=self.on_volume_change,
            label="{value}%",
            max=100,
            min=0,
            value=50,
            visible=True,
            width=0,
            opacity=0,
            animate_opacity=100,
            animate_size=100,
            padding=0,
            margin=ft.Margin(left=0, right=0),
        )
        self.volume_container = ft.Container(
            on_hover=self.on_volume_hover,
            content=ft.Row(controls=[self.volume_button, self.volume_slider]),
        )

        self.playlist_add_button = ft.IconButton(icon=ft.Icons.PLAYLIST_ADD)
        self.lyrics_button = ft.IconButton(icon=ft.Icons.LYRICS_OUTLINED)
        self.info_button = ft.IconButton(icon=ft.Icons.INFO_OUTLINED)
        self.queue_button = ft.IconButton(icon=ft.Icons.QUEUE_MUSIC)

        alignment = (ft.MainAxisAlignment.START,)
        self.controls = [
            ft.Container(
                expand=4,
                alignment=ft.Alignment.CENTER_LEFT,
                content=ft.Row(
                    controls=[
                        self.play_button,
                        self.prev_button,
                        self.next_button,
                        self.shuffle_button,
                        self.loop_button,
                        self.time_label,
                        self.scrubber,
                        self.song_length,
                    ]
                ),
            ),
            ft.Container(
                expand=3,
                alignment=ft.Alignment.CENTER_LEFT,
                content=ft.Row(
                    controls=[
                        self.volume_container,
                        ft.VerticalDivider(leading_indent=0, trailing_indent=0),
                        self.SongInfo,
                        ft.VerticalDivider(leading_indent=0, trailing_indent=0),
                        self.playlist_add_button,
                        self.lyrics_button,
                        self.info_button,
                        self.queue_button,
                    ]
                ),
            ),
        ]
        self.on_volume_change(None)
        self._updating = True
        asyncio.create_task(self.update_position())

    async def update_position(self):
        while self._updating:
            try:
                self.audio.test_file()
            except:
                continue
            pos = self.audio.get_position()
            dur = self.audio.get_duration()
            if dur > 0:
                self.scrubber.value = pos / dur * 100
                mins, secs = divmod(int(pos), 60)
                total_mins, total_secs = divmod(int(dur), 60)
                self.time_label.value = f"{mins:02}:{secs:02}"
                self.song_length.value = f"{total_mins:02}:{total_secs:02}"
                self.main_page.update()
            await asyncio.sleep(0.2)

    def toggle_play(self, e):
        value = self.scrubber.value
        if self.audio.toggle_playback():
            dur = self.audio.get_duration()
            new_pos = value / 100 * dur
            self.audio.set_position(new_pos)
            self.play_button.icon = ft.Icons.PAUSE_CIRCLE_FILLED_ROUNDED
        else:
            self.play_button.icon = ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED

        pass

    def on_volume_hover(self, e: ft.Event[ft.Container]):
        if e.data:
            self.volume_slider.width = 100
            self.volume_slider.opacity = 1
            self.volume_slider.margin = ft.Margin(left=0, right=20)
        else:
            self.volume_slider.opacity = 0
            self.volume_slider.width = 0
            self.volume_slider.margin = ft.Margin(left=0, right=0)

    def on_scrubber_change(self, e):
        dur = self.audio.get_duration()
        new_pos = self.scrubber.value / 100 * dur
        self.audio.set_position(new_pos)

    def on_volume_change(self, e: ft.Event[ft.Slider]):
        self.saved_audio_value = None
        self.audio.set_volume(int(self.volume_slider.value))

        if self.volume_slider.value == 0:
            self.volume_button.icon = ft.Icons.VOLUME_OFF_ROUNDED
        elif self.volume_slider.value > 50:
            self.volume_button.icon = ft.Icons.VOLUME_UP_ROUNDED
        else:
            self.volume_button.icon = ft.Icons.VOLUME_DOWN_ROUNDED

    def on_volume_click(self, e: ft.Event[ft.IconButton]):
        if self.saved_audio_value:

            self.volume_slider.value = self.saved_audio_value
            self.on_volume_change(e)

        else:
            saved_vol = self.volume_slider.value

            self.volume_slider.value = 0
            self.on_volume_change(e)

            self.saved_audio_value = saved_vol

    def on_shuffle_click(self, e: ft.Event[ft.IconButton]):
        if self.shuffle:
            self.shuffle = False
            self.shuffle_button.icon_color = None
        else:
            self.shuffle = True
            self.shuffle_button.icon_color = ft.Colors.PRIMARY
    
    def on_loop_click(self,e: ft.Event[ft.IconButton]):
        if self.loop == 0:
            # goto loop once
            self.loop = 1
            self.loop_button.icon = ft.Icons.REPEAT_ONE_ROUNDED
            self.loop_button.icon_color = ft.Colors.PRIMARY
        elif self.loop == 1:
            # goto loop indef
            self.loop = 2
            self.loop_button.icon = ft.Icons.REPEAT_ROUNDED
            self.loop_button.icon_color = ft.Colors.PRIMARY
            
        else:
            # goto not loop
            self.loop = 0
            self.loop_button.icon = ft.Icons.REPEAT_ROUNDED
            self.loop_button.icon_color = None
            
            