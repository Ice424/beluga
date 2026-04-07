from typing import Any
import flet as ft
import os
import asyncio


from tools.audio_manager import AudioManager
from ui.playbar import Playbar

from tools.mpris import MPRISController


class Main:
    def __init__(
        self,
        page: ft.Page,
    ):
        self.page = page
        self.audio = AudioManager(
            "/home/ice424/Music/Prefer not to say/somewhere, someday, - Tanger, lorem ipsum.flac"
        )
        self.mpris = MPRISController(self.audio)

        self.mpris.update_metadata(
            title="Somewhere Someday",
            artist="Tanger",
            album="Prefer Not To Say",
            art_url="file:///home/user/Music/cover.jpg",
            length=240,
        )

        self.playbar = Playbar(page, self.audio)

        self.showing_dialog = False
        self.page.window.prevent_close = True
        self.page.window.on_event = self.window_event

        self.build_ui()
        self.page.run_task(self.mpris_loop)
        
    async def mpris_loop(self):
        while True:
            self.mpris.update_playback()
            await asyncio.sleep(0.5)

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
        self.page.bottom_appbar = ft.BottomAppBar(height=80, content=self.playbar)
        self.page.add(
            ft.SafeArea(
                ft.Row(
                    expand=True,
                    controls=[
                        ft.ListView(
                            width=150,
                            controls=[
                                self.sidebar_tab(
                                    ft.Icons.FORMAT_LIST_BULLETED_ROUNDED, "Tracks"
                                ),
                                self.sidebar_tab(ft.Icons.ALBUM, "Albums"),
                                self.sidebar_tab(ft.Icons.PERSON, "Artists"),
                                self.sidebar_tab(
                                    ft.Icons.LIBRARY_MUSIC_ROUNDED, "Playlists"
                                ),
                            ],
                        ),
                        ft.Text("Main"),
                    ],
                )
            )
        )

    async def handle_yes_click(self, e: ft.Event[ft.Button]):
        self.audio.stop()
        await self.page.window.destroy()

    def handle_no_click(self, e: ft.Event[ft.OutlinedButton] | ft.Event[ft.Button]):
        self.showing_dialog = False
        self.page.pop_dialog()
        self.page.update()

    async def window_event(self, e: ft.WindowEvent):

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Please confirm"),
            content=ft.Text("Do you really want to exit this app?"),
            actions=[
                ft.Button(content="Yes", on_click=self.handle_yes_click),
                ft.OutlinedButton(content="Minimise", on_click=self.handle_no_click),
                ft.Button(content="No", on_click=self.handle_no_click),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        if e.type == ft.WindowEventType.CLOSE and not self.showing_dialog:
            await self.handle_yes_click(e)
            self.showing_dialog = True
            self.page.show_dialog(confirm_dialog)
            self.page.update()


def main(page: ft.Page):
    Main(page)


ft.run(main)
