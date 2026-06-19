import flet as ft
import asyncio
from typing import Any
from typing import TYPE_CHECKING, Literal
from tools.track import Track

if TYPE_CHECKING:
    from tools.library_manager import LibraryManager


views = Literal[
    "cover_image",
    "track_number",
    "title",
    "title_artist",
    "album",
    "duration",
    "add_playlist",
    "add_queue",
]


class View(ft.Column):
    def __init__(
        self,
        library_manager: "LibraryManager",
        db_available=False,
        view_config: list[views] = [
            "cover_image",
            "title_artist",
            "album",
            "duration",
            "add_playlist",
            "add_queue",
        ],
    ) -> None:
        super().__init__()
        self.library = library_manager
        self.expand = True
        self.header = Header(self, library_manager)
        self.track_list = TrackList(view_config)
        self.controls = [self.header, self.track_list]

        self.db_available = db_available
        if db_available:
            self.on_library_loaded()

    def on_library_loaded(self):
        self.db_available = True
        search = ft.Event("change", control=self.header.search_bar, data="")
        self.header.search_bar.run_search(search)


class TrackList(ft.ListView):
    def __init__(self, view_config) -> None:
        super().__init__()
        self.scroll = ft.ScrollMode.ADAPTIVE
        self.controls = [
            TrackItem(
                Track.from_file(
                    "/home/ice424/Music/Prefer not to say/strangers once again - Tanger, Treb, Ofir Tabakov.flac",
                ),
                view_config,
            )
        ]


class TrackItem(ft.Container):
    def __init__(self, track: Track, view_config) -> None:
        super().__init__()
        self.track = track
        view_config = ["cover_image", "title_artist"]

        self.main_row = ft.Row()
        for view in view_config:
            self.main_row.controls.append(views_map[view](track))

        self.content = self.main_row


class CoverImage(ft.Image):
    def __init__(self, track: Track) -> None:

        if track.cover_path:
            super().__init__(str(track.cover_path),
                width=50,
                height=50,
                border_radius=6)
        else:
            super().__init__(
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-music-icon lucide-music"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>',
                width=50,
                height=50,
                border_radius=6
            )


class TitleArtist(ft.Column):
    def __init__(self, track: Track) -> None:
        super().__init__()
        SongName = ft.Text(
            str(track.title),
            weight=ft.FontWeight.BOLD,
            overflow=ft.TextOverflow.CLIP,
            no_wrap=True,
        )
        if track.artists:
            artist = ", ".join(track.artists)
        else:
            artist = track.artist
        ArtistName = ft.Text(
            str(artist), size=10, overflow=ft.TextOverflow.CLIP, no_wrap=True
        )
        self.controls = [SongName, ArtistName]


views_map = {
    "cover_image": CoverImage,
    "track_number": "",
    "title": "",
    "title_artist": TitleArtist,
    "album": "",
    "duration": "",
    "add_playlist": "",
    "add_queue": "",
}


class Header(ft.Container):
    def __init__(self, view, library_manager) -> None:
        super().__init__()
        self.sort_mode = "Title"
        list_view_button = ft.IconButton(icon=ft.Icons.VIEW_HEADLINE)
        grid_view_button = ft.IconButton(icon=ft.Icons.GRID_VIEW_ROUNDED)

        self.button_label = ft.Text(self.sort_mode)

        sort_view = ft.PopupMenuButton(
            content=ft.Container(
                padding=10,
                border_radius=70,
                content=ft.Row(controls=[ft.Icon(ft.Icons.SORT), self.button_label]),
            ),
            items=[
                ft.PopupMenuItem(
                    content="Title", on_click=lambda: self.change_sort_mode("Title")
                ),
                ft.PopupMenuItem(
                    content="Artist", on_click=lambda: self.change_sort_mode("Artist")
                ),
                ft.PopupMenuItem(
                    content="Album", on_click=lambda: self.change_sort_mode("Album")
                ),
            ],
            menu_position=ft.PopupMenuPosition.UNDER,
        )
        self.search_bar = search_bar(self, view, library_manager)

        self.row = ft.Row(
            alignment=ft.MainAxisAlignment.END,
            height=70,
            controls=[self.search_bar, list_view_button, grid_view_button, sort_view],
        )
        self.content = self.row

    def change_sort_mode(self, mode=""):
        self.sort_mode = mode
        self.button_label.value = mode


class search_bar(ft.Container):
    def __init__(self, header, view, library_manager) -> None:
        self.view = view
        self.library_manager: LibraryManager = library_manager
        super().__init__()
        search_icon = ft.Icon(ft.Icons.SEARCH)
        self.header = header
        self.search_visible = False
        self.padding = 8
        self.search_box = ft.TextField(
            visible=False,
            margin=0,
            border=ft.InputBorder.NONE,
            max_lines=1,
            width=0,
            height=0,
            opacity=0,
            on_tap_outside=self.hide_search,
            on_submit=self.hide_search,
            animate_opacity=100,
            animate_size=150,
            on_change=self.run_search,
        )
        self.ink = True
        self.border_radius = 20

        self.content = ft.Row(controls=[search_icon, self.search_box])
        self.on_click = self.toggle_search

    async def toggle_search(self):
        if self.search_box.visible:
            await self.hide_search()
        else:
            await self.show_search()

    async def show_search(self):

        self.search_box.visible = True

        self.search_box.update()
        await asyncio.sleep(0.01)
        self.search_box.width = 300
        self.search_box.height = 70
        self.search_box.opacity = 1
        await self.search_box.focus()
        self.search_box.update()

    async def hide_search(self):

        self.search_box.width = 0
        self.search_box.height = 0
        self.search_box.opacity = 0
        self.search_box.update()
        await asyncio.sleep(0.1)
        self.search_box.visible = False
        self.update()
        self.page.update()

    def run_search(self, search: ft.Event[ft.TextField]):
        print(search)

        if self.view.db_available:
            print(self.library_manager.get_tracks(search.data, "album"))

        # await self.search_box.focus()
