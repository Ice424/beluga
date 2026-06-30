from typing import Any
import flet as ft
import asyncio


from tools.audio_manager import AudioManager
from tools.library_manager import LibraryManager
from tools.presence import PresenceManager
import tools.config as config

from ui.playbar import Playbar
from ui.views import TrackView




class Main:
    def __init__(
        self,
        page: ft.Page,
    ):
        self.page = page
        self.audio = AudioManager(self)
        self.presance = PresenceManager(self.audio)

        self.library = LibraryManager()

        self.playbar = Playbar(page, self.audio)

        self.track_view = TrackView(self.library, self.audio)

        self.showing_dialog = False
        self.page.window.prevent_close = True
        self.page.window.on_event = self.window_event

        page.run_task(
            self.library.scan_folder,
            "/home/ice424/Music",
            observers=[self, self.track_view],
        )
        page.run_task(self.presance.update_loop)

        self.build_ui()

        if config.LINUX:
            mpris = MprisController(self.audio)

    class SidebarTab(ft.Container):
       
        
        def __init__(self, icon: ft.IconData, title: str, main: Main):
            super().__init__()
            mapping = {
                "Tracks": [0, TrackView],
                "Albums": [0, TrackView],
                "Artists": [0, TrackView],
                "Playlists": [0, TrackView],
                "Settings": [0, TrackView],
            
            }
            self.index = mapping[title][0]
            self.main_class = main
            
            self.margin = 10
            self.padding=10
            self.alignment=ft.Alignment.CENTER
            self.height=50
            self.width=150
            self.border_radius=10
            self.ink=True
            self.content=ft.Row(controls=[ft.Icon(icon), ft.Text(title)])
            
            self.on_click=self.clicked
            
            self.view = mapping[title][1]
            
        def clicked(self):
            self.main_class.current_page = self.index
            self.page.update()

    def build_ui(self):
        self.current_page = 0
        self.sidebar =  [
        self.SidebarTab(ft.Icons.MY_LIBRARY_BOOKS, "Tracks", self),
        self.SidebarTab(ft.Icons.ALBUM, "Albums", self),
        self.SidebarTab(ft.Icons.PERSON, "Artists", self),
        self.SidebarTab(ft.Icons.LIBRARY_MUSIC, "Playlists", self),
        self.SidebarTab(ft.Icons.SETTINGS, "Settings",self),
        ]
        
        
        self.page.fonts = {
            "RobotoMono": "/fonts/RobotoMono-Regular.ttf",
            "NotoSansMono": "/fonts/NotoSansMono-Regular.ttf",
        }
        self.page.title = "beluga"
        self.page.theme = ft.Theme(font_family="NotoSansMono")
        self.page.bottom_appbar = ft.BottomAppBar(height=80, content=self.playbar)
        self.main_page = self.sidebar[self.current_page].view(self.library, self.audio)
        
        self.page.add(
            ft.SafeArea(
                expand=True,
                minimum_padding=0,
                content=ft.Row(
                    expand=True,
                    controls=[
                        ft.Column(
                            intrinsic_width=True,
                            controls=self.sidebar,
                        ),
                        ft.VerticalDivider(width=1),
                        self.main_page
                    ],
                ),
            )
        )

    async def handle_yes_click(self, e: ft.Event[ft.Button]):
        self.library.close()
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
        self.main_page.on_library_loaded()
        asyncio.create_task(
            self.library.update_fingerprints(
                "/home/ice424/Music", observers=[self, self.track_view]
            )
        )

    def on_fingerprints_loaded(self):
        self.page.show_dialog(ft.SnackBar(ft.Text("Fingerprinted files")))


def main(page: ft.Page):
    Main(page)


ft.run(main, assets_dir="assets")
