from typing import Any
import flet as ft
from sys import platform
import asyncio

from tools.mpris import MprisController
from tools.audio_manager import AudioManager
from tools.library_manager import LibraryManager
from tools.presence import PresenceManager

from ui.playbar import Playbar
from ui.tracks import TrackView


if platform == "linux" or platform == "linux2":
    LINUX = True
elif platform == "darwin":
    MACOS = True
elif platform == "win32":
    WINDOWS = True


class Main:
    def __init__(
        self,
        page: ft.Page,
    ):
        self.page = page
        self.audio = AudioManager()
        self.presance = PresenceManager(self.audio)
        
        self.library = LibraryManager()
        
        self.playbar = Playbar(page, self.audio)

        self.showing_dialog = False
        self.page.window.prevent_close = True
        self.page.window.on_event = self.window_event

        asyncio.create_task(self.library.scan_folder("/home/ice424/Music", observer=self))
        page.run_task(self.presance.update_loop)
        
        self.build_ui()
        
        self.audio.load_file("/home/ice424/Music/Prefer not to say/depressed hermit girl touches grass - Tanger, ISSBROKIE.flac")
        if LINUX:
            mpris = MprisController(self.audio)
            mpris.on_track_change(self.audio.track)

    def sidebar_tab(self, icon: ft.IconData, title: str):
        
        return ft.Container(
            margin=10,
            padding=10,
            alignment=ft.Alignment.CENTER,
            height=50,
            width=150,
            border_radius=10,
            ink=True,
            content=ft.Row(controls=[ft.Icon(icon), ft.Text(title)]),
            on_click=lambda e: print("Clickable transparent with Ink clicked!"),
        )

    def build_ui(self):
        self.page.fonts = {"RobotoMono": "/fonts/RobotoMono-Regular.ttf"}
        self.page.title = "beluga"
        self.page.theme = ft.Theme(font_family="RobotoMono")
        self.page.bottom_appbar = ft.BottomAppBar(height=80, content=self.playbar)
        self.page.add(
            ft.SafeArea(
                expand=True,
                minimum_padding=0,
                content=ft.Row(
                    
                    expand=True,
                    controls=[
                        ft.Column(
                            intrinsic_width=True,
                            controls=[
                                self.sidebar_tab(
                                    ft.Icons.MY_LIBRARY_BOOKS, "Tracks"
                                ),
                                self.sidebar_tab(ft.Icons.ALBUM, "Albums"),
                                self.sidebar_tab(ft.Icons.PERSON, "Artists"),
                                self.sidebar_tab(
                                    ft.Icons.LIBRARY_MUSIC, "Playlists"
                                ),
                        
                           ],
                        ),
                        ft.VerticalDivider(width=1),
                        TrackView(self.library)
                    ],
                ),
            )
        )

    async def handle_yes_click(self, e: ft.Event[ft.Button]):
        self.audio.stop()
        await self.page.window.destroy()

    def handle_no_click(self, e: ft.Event[ft.OutlinedButton] | ft.Event[ft.Button]):
        self.showing_dialog = False
        self.page.pop_dialog()
        self.page.update()

    async def handle_minimise_click(self, e: ft.Event[ft.OutlinedButton]):
        self.showing_dialog = False
        self.page.pop_dialog()
        self.page.update()
        self.page.show_semantics_debugger = not self.page.show_semantics_debugger

    async def window_event(self, e: ft.WindowEvent):

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Please confirm"),
            content=ft.Text("Do you really want to exit this app?"),
            actions=[
                ft.Button(content="Yes", on_click=self.handle_yes_click),
                ft.OutlinedButton(
                    content="Minimise", on_click=self.handle_minimise_click
                ),
                ft.Button(content="No", on_click=self.handle_no_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if e.type == ft.WindowEventType.CLOSE and not self.showing_dialog:
            self.showing_dialog = True
            self.page.show_dialog(confirm_dialog)
            self.page.update()

    def on_library_loaded(self):
        self.page.show_dialog(ft.SnackBar(ft.Text("Refreshed Library")))

def main(page: ft.Page):
    Main(page)


ft.run(main)
