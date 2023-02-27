import asyncio
from pyncm import apis
from _track import Track
from _menu import AlbumMenu
from textual import events
from textual.widgets import DataTable
from textual.widgets.data_table import CellDoesNotExist
from textual.coordinate import Coordinate
from textual.binding import Binding
from textual.message import Message, MessageTarget
from pathlib import Path


class TrackTable(DataTable):
    tracks: list[Track] = []
    likes: list[Track] = []
    watchlist: set[Track] = set()

    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("h", "cursor_left", "Cursor Left", show=False),
        Binding("l", "cursor_right", "Cursor Right", show=False),
        Binding("p", "play", "Play"),
        Binding("f", "like", "Like/Unlike"),
        Binding("d", "download", "Download/Delete"),
        Binding("s", "subset", "Subset")
    ]

    def on_mount(self):
        self.add_column('Liked', key='liked')
        self.add_column('Track', width=40, key='track')
        self.add_column('Artist', width=30, key='artist')
        self.add_column('Album', width=30, key='album')
        self.add_column('Local', width=30, key='local')
        self.set_interval(1, self.update_progress)

    def update(self):
        self.clear()

        for track in self.tracks:
            row = []

            if track.liked:
                row.append(":sparkling_heart:")
            else:
                row.append('')
            row.extend([track.name, track.artists, track.album])

            if track.local:
                row.append(':white_heavy_check_mark:')
            else:
                row.append(track.progress)
            self.add_row(*row, key=str(track.id))

        self.refresh()

    def update_progress(self):
        for track in tuple(self.watchlist):
            if track.local:
                self.watchlist.remove(track)
            try:
                self.update_cell(str(track.id), 'local', track.progress)
            except CellDoesNotExist:
                pass

    def unlocal(self, track: Track):
        """Called when the local file of a track is deleted"""
        try:
            self.watchlist.remove(track)
        except KeyError:
            pass

        try:
            self.update_cell(str(track.id), 'local', '')
        except CellDoesNotExist:
            pass

    def _on_blur(self, event: events.Blur) -> None:
        super()._on_blur(event)
        self.show_cursor = False

    def _on_focus(self, event: events.Focus) -> None:
        super()._on_focus(event)
        self.show_cursor = True

    class Play(Message):
        """Tell the app to play a track from the track table"""

        def __init__(self, sender: MessageTarget, track: Track, tracks: list):
            self.track = track
            self.tracks = tracks
            super().__init__(sender)

    def action_play(self):
        track = self.tracks[self.cursor_row]
        message = self.Play(self, track, self.tracks)
        self.post_message_no_wait(message)

    class Liked(Message):
        """Notify the app that a track has been liked/unliked"""

        def __init__(self, sender: MessageTarget, track: Track):
            self.track = track
            super().__init__(sender)

    def like(self, track: Track):
        loop = asyncio.get_event_loop()
        track.liked = not track.liked

        def _like():
            apis.track.SetLikeTrack(track.id, like=True)

        def _unlike():
            apis.track.SetLikeTrack(track.id, like=False)

        if track in self.tracks:
            if track.liked:
                self.update_cell(str(track.id), 'liked', ":sparkling_heart:")
            else:
                self.update_cell(str(track.id), 'liked', '')

        if track.liked:
            self.likes.insert(0, track)
            thread = _like
        else:
            self.likes.remove(track)
            thread = _unlike

        if self.tracks is self.likes:
            self.update()

        message = self.Liked(self, track)
        self.post_message_no_wait(message)
        loop.run_in_executor(None, thread)

    def action_like(self):
        track = self.tracks[self.cursor_row]
        self.like(track)

    class Download(Message):
        """Tell the app to download a track from the track table"""

        def __init__(self, sender: MessageTarget, track: Track):
            self.track = track
            super().__init__(sender)

    def action_download(self):
        track = self.tracks[self.cursor_row]

        if track.local:
            Path().joinpath('downloads', f'{track.id}.mp3').unlink()
            track.local = False
            self.unlocal(track)
        else:
            self.watchlist.add(track)
            message = self.Download(self, track)
            self.post_message_no_wait(message)

    def scroll_to_track(self, track: Track) -> None:
        row = self.tracks.index(track)
        column = 0
        self.cursor_coordinate: Coordinate = Coordinate(row, column)
        self.focus()
        self._scroll_cursor_into_view()

    def action_select_cursor(self) -> None:
        super().action_select_cursor()
        cursor_keys = self.coordinate_to_cell_key(self.cursor_coordinate)
        col_key = cursor_keys.column_key
        if col_key == 'liked':
            self.action_like()
        elif col_key == 'track':
            self.action_play()
        elif col_key == 'artist':
            # TODO
            pass
        elif col_key == 'album':
            track = self.tracks[self.cursor_row]
            self.tracks = AlbumMenu.get_tracks(str(track.album_id))
            self.update()
        elif col_key == 'local':
            self.action_download()

    def action_subset(self) -> None:
        cursor_keys = self.coordinate_to_cell_key(self.cursor_coordinate)
        col_key = cursor_keys.column_key
        cursor_track = self.tracks[self.cursor_row]
        if col_key == 'liked':
            self.tracks = [track for track in self.tracks if track.liked]
        elif col_key == 'artist':
            # TODO
            pass
        elif col_key == 'album':
            self.tracks = [track for track in self.tracks if track.album_id == cursor_track.album_id]
        elif col_key == 'local':
            self.tracks = [track for track in self.tracks if track.local]
        else:
            return
        self.update()
