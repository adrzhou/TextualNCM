from pyncm import apis
from _track import Track
from pathlib import Path
from textual import events
from textual.widgets import DataTable
from textual.binding import Binding
from textual.message import Message, MessageTarget
from functools import cached_property


class TrackTable(DataTable):
    tracks: list[Track] = []
    watchlist: set[Track] = set()

    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("h", "cursor_left", "Cursor Left", show=False),
        Binding("l", "cursor_right", "Cursor Right", show=False)
    ]

    def on_mount(self):
        self.add_column('Liked')
        self.add_column('Track', width=40)
        self.add_column('Artist', width=30)
        self.add_column('Album', width=30)
        self.add_column('Local', width=30)
        self.set_interval(1, self.update_progress)

    @cached_property
    def likelist(self):
        return apis.user.GetUserLikeList()['ids']

    def update(self):
        self.clear()
        for track in self.tracks:
            row = []
            if track.liked is None:
                track.liked = track.id in self.likelist
            if track.liked:
                row.append(":sparkling_heart:")
            else:
                row.append('')
            row.extend([track.name, track.artists, track.album])
            if track.local is None:
                track.local = Path().joinpath('downloads', f'{track.id}.mp3').exists()
            if track.local:
                row.append(':white_heavy_check_mark:')
            else:
                row.append('')
            self.add_row(*row)
        self.refresh()

    def update_progress(self):
        for track in tuple(self.watchlist):
            try:
                row = self.tracks.index(track)
            except ValueError:
                continue
            if track.local:
                self.watchlist.remove(track)
                self.data[row][-1] = ':white_heavy_check_mark:'
            else:
                self.data[row][-1] = track.progress
            self.refresh_cell(row, 4)
            self._clear_caches()

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

    def key_p(self):
        track = self.tracks[self.cursor_row]
        message = self.Play(self, track, self.tracks)
        self.emit_no_wait(message)
