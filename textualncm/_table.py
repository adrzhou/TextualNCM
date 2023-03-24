import asyncio
from pyncm import apis
from _track import Track
from _menu import AlbumMenu, ArtistMenu, PlaylistMenu
from textual import events
from textual.app import ComposeResult
from textual.widgets import DataTable
from textual.widgets.data_table import CellDoesNotExist
from textual.coordinate import Coordinate
from textual.binding import Binding
from textual.message import Message
from textual.containers import Container
from pathlib import Path


class TableMixin(DataTable):
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("h", "cursor_left", "Cursor Left", show=False),
        Binding("l", "cursor_right", "Cursor Right", show=False)
    ]

    def _on_blur(self, event: events.Blur) -> None:
        super()._on_blur(event)
        self.show_cursor = False

    def _on_focus(self, event: events.Focus) -> None:
        super()._on_focus(event)
        self.show_cursor = True

    class ShowTracks(Message):
        def __init__(self, tracks: list[Track]):
            self.tracks = tracks
            super().__init__()


class TrackTable(TableMixin, DataTable):
    tracks: list[Track] = []
    likes: list[Track] = []
    watchlist: set[Track] = set()

    BINDINGS = [
        Binding("p", "play", "播放"),
        Binding("f", "like", "喜欢/取消喜欢"),
        Binding("d", "download", "下载/删除"),
        Binding("s", "subset", "筛选")
    ]

    def on_mount(self):
        self.add_column('喜欢', key='liked')
        self.add_column('曲名', width=40, key='track')
        self.add_column('艺人', width=30, key='artist')
        self.add_column('专辑', width=30, key='album')
        self.add_column('本地', width=30, key='local')
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

    class Play(Message):
        """Tell the app to play a track from the track table"""

        def __init__(self, track: Track, tracks: list):
            self.track = track
            self.tracks = tracks
            super().__init__()

    def action_play(self):
        track = self.tracks[self.cursor_row]
        message = self.Play(track, self.tracks)
        self.post_message(message)

    class Liked(Message):
        """Notify the app that a track has been liked/unliked"""

        def __init__(self, track: Track):
            self.track = track
            super().__init__()

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

        message = self.Liked(track)
        self.post_message(message)
        loop.run_in_executor(None, thread)

    def action_like(self):
        track = self.tracks[self.cursor_row]
        self.like(track)

    class Download(Message):
        """Tell the app to download a track from the track table"""

        def __init__(self, track: Track):
            self.track = track
            super().__init__()

    def action_download(self):
        track = self.tracks[self.cursor_row]

        if track.local:
            Path().joinpath('downloads', f'{track.id}.mp3').unlink()
            track.local = False
            self.unlocal(track)
        else:
            self.watchlist.add(track)
            message = self.Download(track)
            self.post_message(message)

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
            artists = self.tracks[self.cursor_row].artist_ids
            if len(artists) == 1:
                artist_id = list(artists.keys())[0]
                self.tracks = ArtistMenu.get_tracks(artist_id)
            else:
                artists = [{'name': v, 'id': k} for k, v in artists.items()]
                message = self.ShowArtists(artists)
                self.post_message(message)
            self.update()
        elif col_key == 'album':
            track = self.tracks[self.cursor_row]
            self.tracks = AlbumMenu.get_tracks(str(track.album_id))
            self.update()
        elif col_key == 'local':
            self.action_download()

    class ShowArtists(Message):
        """Show an artist table when selecting multiple arists"""

        def __init__(self, artists: list):
            super().__init__()
            self.artists = artists

    def action_subset(self) -> None:
        cursor_keys = self.coordinate_to_cell_key(self.cursor_coordinate)
        col_key = cursor_keys.column_key
        cursor_track = self.tracks[self.cursor_row]
        if col_key == 'liked':
            self.tracks = [track for track in self.tracks if track.liked]
        elif col_key == 'artist':
            artist_id = list(cursor_track.artist_ids)[0]
            self.tracks = [tr for tr in self.tracks if artist_id in tr.artist_ids]
        elif col_key == 'album':
            self.tracks = [track for track in self.tracks if track.album_id == cursor_track.album_id]
        elif col_key == 'local':
            self.tracks = [track for track in self.tracks if track.local]
        else:
            return
        self.update()


class AlbumTable(TableMixin, DataTable):
    albums: list = []

    def on_mount(self):
        self.display = False
        self.add_column('专辑', width=30, key='album')
        self.add_column('创作者', width=30, key='artist')
        self.add_column('发行日期', width=30, key='release')
        self.add_column('曲目', key='count')

    def update(self) -> None:
        self.clear()
        for album in self.albums:
            self.add_row(album['name'], album['artist'], album['release'], album['number'])

    def action_select_cursor(self) -> None:
        super().action_select_cursor()
        cursor_keys = self.coordinate_to_cell_key(self.cursor_coordinate)
        col_key = cursor_keys.column_key
        album = self.albums[self.cursor_row]
        if col_key == 'album':
            tracks = AlbumMenu.get_tracks(album['album_id'])
            message = self.ShowTracks(tracks)
            self.post_message(message)
        elif col_key == 'artist':
            tracks = ArtistMenu.get_tracks(album['artist_id'])
            message = self.ShowTracks(tracks)
            self.post_message(message)


class ArtistTable(TableMixin, DataTable):
    artists = []

    def on_mount(self):
        self.display = False
        self.add_column('创作者', width=30, key='artist')

    def update(self) -> None:
        self.clear()
        for artist in self.artists:
            self.add_row(artist['name'])

    def action_select_cursor(self) -> None:
        super().action_select_cursor()
        artist_id = self.artists[self.cursor_row]['id']
        tracks = ArtistMenu.get_tracks(artist_id)
        message = self.ShowTracks(tracks)
        self.post_message(message)


class PlaylistTable(TableMixin, DataTable):
    playlists = []

    def on_mount(self):
        self.display = False
        self.add_column('歌单', width=30, key='playlist')
        self.add_column('Curator', width=30, key='curator')
        self.add_column('曲目', key='count')

    def update(self) -> None:
        self.clear()
        for pl in self.playlists:
            self.add_row(pl['name'], pl['curator'], pl['count'])

    def action_select_cursor(self) -> None:
        super().action_select_cursor()
        plist_id = self.playlists[self.cursor_row]['playlist_id']
        tracks = PlaylistMenu.get_tracks(plist_id)
        message = self.ShowTracks(tracks)
        self.post_message(message)


class Tables(Container):
    def compose(self) -> ComposeResult:
        yield TrackTable(id='tracks')
        yield AlbumTable(id='albums')
        yield ArtistTable(id='artists')
        yield PlaylistTable(id='playlists')

    def switch(self, mode: int) -> None:
        for child in self.children:
            child.display = False
        if mode == 1:
            self.query_one(TrackTable).display = True
        elif mode == 10:
            self.query_one(AlbumTable).display = True
        elif mode == 100:
            self.query_one(ArtistTable).display = True
        else:
            self.query_one(PlaylistTable).display = True

    def on_table_mixin_show_tracks(self, message: AlbumTable.ShowTracks):
        self.switch(1)
        table = self.query_one(TrackTable)
        table.tracks = message.tracks
        table.update()
        table.focus()

    def on_track_table_show_artists(self, message: TrackTable.ShowArtists):
        self.switch(100)
        table = self.query_one(ArtistTable)
        table.artists = message.artists
        table.update()
        table.focus()
