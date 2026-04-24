import flet as ft
import asyncio
from typing import Any
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from tools.library_manager import LibraryManager
    from tools.track import Track

view = Literal[
    "track_number",
    "title",
    "album",
    "duration",
    "add_playlist",
    "add_queue",
]


class TrackView(ft.Column):
    def __init__(self, library_manager: "LibraryManager") -> None:
        super().__init__()
        self.library = library_manager
        self.tracks = library_manager.get_tracks()
        self.expand = True
        self.header = Header()
        self.controls = [
            self.header,
            ListView(
                self.tracks,
                [
                    "track_number",
                    "title",
                    "album",
                    "duration",
                    "add_playlist",
                    "add_queue",
                ],
            ),
        ]


class ListView(ft.ListView):
    def __init__(self, tracks: list[Track], views: list[view]) -> None:
        super().__init__()
        self.views = views
        self.expand = True
        self.header = self.build_header(self.views)
        self.controls = [self.header]

    def build_header(self, views: list[view]) -> ft.Row:
        labels = {
            "track_number": "#",
            "title": "Title",
            "album": "Album",
            "duration": "duration",
            "add_playlist": "",
            "add_queue": "",
        }

        return ft.Row(
            controls=[
                ft.Text(labels[v], weight=ft.FontWeight.BOLD, expand=1) for v in views
            ]
        )


class GridView(ft.GridView):
    def __init__(self, tracks: list[Track]) -> None:
        super().__init__()
        self.expand = True


class Header(ft.Container):
    def __init__(self) -> None:
        super().__init__()
        sort_mode = "Title"
        list_view_button = ft.IconButton(icon=ft.Icons.VIEW_HEADLINE)
        grid_view_button = ft.IconButton(icon=ft.Icons.GRID_VIEW_ROUNDED)

        sort_view = ft.PopupMenuButton(
            content= ft.Container(
                padding=10,
                border_radius=70,
                content=ft.Row(controls=[ft.Icon(ft.Icons.SORT), ft.Text(sort_mode)])
            ),
            items=[
                ft.PopupMenuItem(content="Sm"),
                ft.PopupMenuItem(content="Med"),
                ft.PopupMenuItem(content="Lg"),
            ],
            menu_position=ft.PopupMenuPosition.UNDER,
        )
        self.search_bar = search_bar(self)
        self.search = ft.KeyboardListener(
            content = self.search_bar,
            on_key_down= self.search_bar.show_search,
            autofocus=True
        )
        

        self.row = ft.Row(
            alignment=ft.MainAxisAlignment.END,
            height=70,
            controls=[list_view_button, grid_view_button, sort_view, self.search],
        )
        self.content = self.row


class search_bar(ft.Container):
    def __init__(
        self, header
    ) -> None:
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
            
    async def show_search(self ):
       
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
        

        await self.header.search.focus()
        self.page.update()
        
        

        # await self.search_box.focus()
