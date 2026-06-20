import flet as ft
import asyncio
from typing import Any
from typing import TYPE_CHECKING, Literal
from tools.track import Track

if TYPE_CHECKING:
    from tools.library_manager import LibraryManager
    from tools.audio_manager import AudioManager


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
        audio_manager: "AudioManager",
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
        self.search_manager = SearchManager(self, self.library)
        self.expand = True
        self.header = Header(self.search_manager)
        self.track_list = TrackList(view_config, audio_manager, self.search_manager)
        self.controls = [self.header, self.track_list]

        self.db_available = db_available
        if db_available:
            self.on_library_loaded()

    def on_library_loaded(self):
        self.db_available = True
        
        self.search_manager.run_scheduled_search()
    
    def on_fingerprints_loaded(self):
        self.search_manager.run_last_search()


class TrackList(ft.ListView):
    def __init__(self, view_config, audio_manager:AudioManager, search_manager: SearchManager) -> None:
        super().__init__()
        self.audio_manager = audio_manager
        self.view_config = view_config
        self.scroll = ft.ScrollMode.ALWAYS
        self.controls = []
        self.spacing = 5
        self.expand = True
        self.on_scroll = self.handle_scroll
        self.search_manager = search_manager
        self.build_controls_on_demand = True
        self.first_item_prototype = True 
        
        
    def update_list(self, track_list: list[Track]):
        self.controls = []
        for track in track_list:
            self.controls.append(TrackItem(track, self.view_config, self.audio_manager))
        self.update()
    def add_tracks(self, track_list):
        for track in track_list:
            self.controls.append(TrackItem(track, self.view_config, self.audio_manager))
        self.update()
        
    def handle_scroll(self, e:ft.Event[ft.ListView]):
        scroll_percent = (e.pixels/e.max_scroll_extent)*100
        
        if scroll_percent == 100:
            print("start Query")
            self.search_manager.get_more_tracks()
            
        
    

class TrackItem(ft.Container):
    def __init__(self, track: Track, view_config, audio_manager:AudioManager) -> None:
        super().__init__()
        self.track = track
        self.audio_manager = audio_manager
        view_config = ["cover_image", "title_artist", "album", "duration"] #temp
        self.ink=True
        self.on_click = self.choose_track
        self.row = ft.Row()
        self.padding = 5
        self.border_radius = 6.5
        self.margin = ft.Margin(0,0,20,0)
        for view in view_config:
            self.row.controls.append(views_map[view](track))

        self.content = self.row
    def choose_track(self):
        if self.audio_manager.is_playing:
            self.audio_manager.pause()
        self.audio_manager.load_track(self.track)
        
        self.audio_manager.play()
            
        


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
    def __init__(self, track: Track, expand=True) -> None:
        super().__init__()
        self.expand= 8
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

class Duration(ft.Text):
    def __init__(self, track: Track) -> None:
        super().__init__()
        self.expand= 1
        self.max_lines = 1
        self.text_align = ft.TextAlign.RIGHT
        total_mins, total_secs = divmod(int(track.duration), 60)
        self.value = f"{total_mins:02}:{total_secs:02}"

class Album(ft.Text):
    
    def __init__(self, track: Track) -> None:
        super().__init__()
        self.expand= 5
        self.value = str(track.album)
        self.overflow = ft.TextOverflow.ELLIPSIS
views_map = {
    "cover_image": CoverImage,
    "track_number": "",
    "title": "",
    "title_artist": TitleArtist,
    "album": Album,
    "duration": Duration,
    "add_playlist": "",
    "add_queue": "",
}


class Header(ft.Container):
    def __init__(self, search_manager: SearchManager) -> None:
        super().__init__()
        self.search_manager = search_manager
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
        self.search_bar = search_bar(search_manager)

        self.row = ft.Row(
            alignment=ft.MainAxisAlignment.END,
            height=70,
            controls=[self.search_bar, list_view_button, grid_view_button, sort_view],
        )
        self.content = self.row

    def change_sort_mode(self, mode=""):
        self.search_manager.sort_mode = mode
        self.button_label.value = mode


class search_bar(ft.Container):
    def __init__(self, search_manager:SearchManager ) -> None:
        super().__init__()
        search_icon = ft.Icon(ft.Icons.SEARCH)
        self.search_manager = search_manager
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
    
        self.search_manager.run_search(str(search.data))


        

        # await self.search_box.focus()

class SearchManager():
    def __init__(self, view, library_manager: LibraryManager) -> None:
        self._search_task = None
        self._debounce_delay = 0.3
        self.current_tracks = []
        self.scheduled_search = ""
        self.last_search = ""
        self.library_manager = library_manager
        self.sort_mode = "Title"
        self.view: View = view
        self._last_queued_search = None

        
    def run_search(self, search:str):
        self.query_running = True
        if self.view.db_available:
            self.last_search = search
            self.current_tracks, self.total_tracks = self.library_manager.get_tracks(search, limit=-1)
            self.view.track_list.update_list(self.current_tracks)
        else:
            self.scheduled_search = search


    def get_more_tracks(self):
 
        if len(self.current_tracks) == self.total_tracks:
            return
        print(self.total_tracks, len(self.current_tracks))
        new_tracks, _ = self.library_manager.get_tracks(self.last_search, offset= len(self.current_tracks))
        self.current_tracks += new_tracks
        self.view.track_list.add_tracks(self.current_tracks)

        
        
    def run_scheduled_search(self):
        self.run_search(self.scheduled_search)
    
    def run_last_search(self):
        self.run_search(self.last_search)
        