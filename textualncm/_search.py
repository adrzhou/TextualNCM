from _track import Track
from datetime import date
from pyncm.apis.cloudsearch import GetSearchResult
from textual.widgets import Input
from textual.binding import Binding
from textual.message import Message, MessageTarget

SONG = 1         # 单曲
ALBUM = 10       # 专辑
ARTIST = 100     # 创作者
PLAYLIST = 1000  # 歌单


class Search(Input):
    mode = SONG

    BINDINGS = [
        Binding('up', 'prev_mode', 'Search Type', show=False),
        Binding('down', 'next_mode', 'Search Type', show=False)
    ]

    def action_next_mode(self) -> None:
        if self.mode == SONG:
            self.mode = ALBUM
            self.placeholder = '搜索专辑'
        elif self.mode == ALBUM:
            self.mode = ARTIST
            self.placeholder = '搜索创作者'
        elif self.mode == ARTIST:
            self.mode = PLAYLIST
            self.placeholder = '搜索歌单'
        else:
            self.mode = SONG
            self.placeholder = '搜索单曲'

    def action_prev_mode(self) -> None:
        if self.mode == SONG:
            self.mode = PLAYLIST
            self.placeholder = '搜索歌单'
        elif self.mode == ALBUM:
            self.mode = SONG
            self.placeholder = '搜索单曲'
        elif self.mode == ARTIST:
            self.mode = ALBUM
            self.placeholder = '搜索专辑'
        else:
            self.mode = ARTIST
            self.placeholder = '搜索创作者'

    def action_submit(self) -> None:
        super().action_submit()
        payload = GetSearchResult(self.value, stype=self.mode, limit=50)
        if self.mode == SONG:
            results = self.search_song(payload)
        elif self.mode == ALBUM:
            results = self.search_album(payload)
        elif self.mode == ARTIST:
            results = self.search_artist(payload)
        else:
            results = self.search_playlists(payload)

        message = self.UpdateTable(self, mode=self.mode, results=results)
        self.post_message_no_wait(message)

    class UpdateTable(Message):
        """Tell the app to update the table with search results"""

        def __init__(self, sender: MessageTarget, mode: int, results: list):
            super().__init__(sender)
            self.mode = mode
            self.results = results

    @staticmethod
    def search_song(payload: dict):
        tracks = []
        for track in payload['result']['songs']:
            name = track['name']
            track_id = track['id']
            artists = ', '.join([artist['name'] for artist in track['ar']])
            album = track['al']['name']
            album_id = track['al']['id']
            tracks.append(Track(name, track_id, artists, album, album_id))
        return tracks

    @staticmethod
    def search_album(payload: dict):
        albums = []
        for album in payload['result']['albums']:
            name = album['name']
            album_id = album['id']
            artist = album['artist']['name']
            release = date.fromtimestamp(album['publishTime'] / 1000).isoformat()
            number = album['size']
            albums.append(
                {'name': name,
                 'album_id': album_id,
                 'artist': artist,
                 'release': release,
                 'number': number
                 }
            )
        return albums

    @staticmethod
    def search_artist(payload: dict):
        artists = []
        for artist in payload['result']['artists']:
            name = artist['name']
            artist_id = artist['id']
            artists.append({'name': name, 'artist_id': artist_id})
        return artists

    @staticmethod
    def search_playlists(payload: dict) -> list:
        playlists = []
        for pl in payload['result']['playlists']:
            name = pl['name']
            playlist_id = pl['id']
            curator = pl['creator']
            count = pl['trackCount']
            playlists.append(
                {'name': name,
                 'playlist_id': playlist_id,
                 'curator': curator,
                 'count': count
                 }
            )
        return playlists
