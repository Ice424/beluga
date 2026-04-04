import flet as ft


def main(page: ft.Page):
    counter = ft.Text("0", size=50, data=0)
    text = ft.Text("Hello", size=50, data=0)

    def increment_click(e):
        counter.data += 1
        counter.value = str(counter.data)

    def sidebar_tab(icon: ft.IconData, title: str):
        return ft.Container(
            margin=10,
            padding=10,
            alignment=ft.Alignment.CENTER,
            height=40,
            width=150,
            border_radius=10,
            ink=True,
            content=ft.Row(controls=[ft.Icon(icon), ft.Text(title)]),
            on_click=lambda e: print("Clickable transparent with Ink clicked!"),
        )

    songinfo = ft.Row(
        expand=True,
        controls=[
            ft.Image(src="/home/ice424/Downloads/small.jpg"),
            ft.ListView(
                controls=[
                    ft.Text("Somewhere Someday", weight=ft.FontWeight.BOLD),
                    ft.Text("Tanger", size=10),
                    ft.Text("Prefer Not To Say", size=10),
                ]
            ),
        ],
    )
    player = ft.Container(
        height=30,
        alignment=ft.Alignment.CENTER_LEFT,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    expand=1,
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PLAY_CIRCLE_FILLED_ROUNDED, size=40),
                            ft.Icon(ft.Icons.SKIP_PREVIOUS),
                            ft.Icon(ft.Icons.SKIP_NEXT),
                            ft.Icon(ft.Icons.SHUFFLE),
                            ft.Icon(
                                ft.Icons.REPEAT_ROUNDED, margin=ft.Margin(right=30)
                            ),
                            ft.Text("00:00", margin=ft.Margin(right=0)),
                            ft.Slider(expand=True, margin=ft.Margin(left=0, right=0)),
                            ft.Text("99:00", margin=ft.Margin(left=0, right=30)),
                            ft.Icon(ft.Icons.VOLUME_UP_ROUNDED, margin=ft.Margin(left=0, right=30)),
                        ]
                    ),
                ),
                ft.Container(
                    expand=1,
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=ft.Row(controls=[
                        songinfo, 
                        ft.Icon(ft.Icons.PLAYLIST_ADD),
                        ft.Icon(ft.Icons.LYRICS_OUTLINED),
                        ft.Icon(ft.Icons.INFO_OUTLINED),
                        ft.Icon(ft.Icons.QUEUE_MUSIC)]),
                ),
            ],
        ),
    )
    page.bottom_appbar = ft.BottomAppBar(height=70, content=player)
    page.add(
        ft.SafeArea(
            ft.Row(
                expand=True,
                controls=[
                    ft.ListView(
                        width=150,
                        controls=[
                            sidebar_tab(
                                ft.Icons.FORMAT_LIST_BULLETED_ROUNDED, "Tracks"
                            ),
                            sidebar_tab(ft.Icons.ALBUM, "Albums"),
                            sidebar_tab(ft.Icons.PERSON, "Artists"),
                            sidebar_tab(ft.Icons.LIBRARY_MUSIC_ROUNDED, "Playlists"),
                        ],
                    ),
                    ft.Text("Main"),
                ],
            )
        )
    )


ft.run(main)
