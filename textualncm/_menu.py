from pyncm import apis
from functools import cache
from _track import Track
from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from textual.message import Message
from textual.binding import Binding


class MenuNode(TreeNode):
    def __init__(self):  # noqa
        self.data = None
        self.page: int = 0
        self.has_more: bool = True
        self._expanded = True
        self._children: list[TreeNode] = []
        self._hover_ = False
        self._selected_ = False
        self._allow_expand = True
        self._updates: int = 0
        self._line: int = -1

    @staticmethod
    def request(page: int = 0) -> tuple[bool, list]:
        # Abstract method: Requests data from API for children nodes
        pass

    @staticmethod
    def get_tracks(entry_id: str) -> list[Track]:
        # Abstract method: Requests track list from API for track table
        pass

    def load(self) -> None:
        self.has_more, data = self.request()
        for item in data:
            self.add_leaf(*item)

    def next(self) -> None:
        if not self.has_more:
            return

        self.page += 1
        self.has_more, data = self.request(self.page)
        if self.page >= 1:
            for i in range(len(data)):
                node = self.children[i]
                node.set_label(data[i][0])
                node.data = data[i][1]

    def prev(self) -> None:
        if self.page == 0:
            return

        self.page -= 1
        self.has_more, data = self.request(self.page)
        for i in range(len(data)):
            node = self.children[i]
            node.set_label(data[i][0])
            node.data = data[i][1]


class MenuTree(Tree):
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("p", "play", "播放"),
        Binding("d", "download", "下载"),
        Binding('space', 'space', 'Space', show=False),  # Override default binding
        Binding('left', 'prev', 'Prev', show=False),
        Binding('right', 'next', 'Next', show=False),
        Binding('h', 'prev', 'Prev', show=False),
        Binding('l', 'next', 'Next', show=False)
    ]

    def on_mount(self):
        self.root.add_leaf('每日推荐歌曲')
        self.add_menu(ArtistMenu()).load()
        self.add_menu(AlbumMenu()).load()
        self.add_menu(PlaylistMenu()).load()
        self.action_select_cursor()
        self.focus()

        playlist_menu: MenuNode = self.root.children[3]
        liked_node = playlist_menu.children[0]
        liked = playlist_menu.get_tracks(liked_node.data)
        for track in liked:
            track.liked = True
        message = self.Likes(liked)
        self.post_message(message)

    def add_menu(self, node: MenuNode):
        node._tree = self
        node._parent = self.root
        node._id = self._new_id()
        node._label = self.process_label(node.label)
        self._tree_nodes[node.id] = node
        self._updates += 1
        self.root._updates += 1  # noqa
        self.root._children.append(node)  # noqa
        self._invalidate()
        return node

    def action_prev(self) -> None:
        if hasattr(self.cursor_node.parent, 'prev'):
            self.cursor_node.parent.prev()
            self.refresh()

    def action_next(self) -> None:
        if hasattr(self.cursor_node.parent, 'next'):
            self.cursor_node.parent.next()
            self.refresh()

    def action_select_cursor(self):
        super().action_select_cursor()
        cursor = self.cursor_node
        menu = cursor.parent
        if cursor.label.plain == '每日推荐歌曲':
            tracks = get_daily_songs()
            message = self.UpdateTable(tracks)
            self.post_message(message)
        elif cursor.data:
            tracks = menu.get_tracks(cursor.data)
            message = self.UpdateTable(tracks)
            self.post_message(message)

    class UpdateTable(Message):
        """Update track table message"""

        def __init__(self, tracks: list):
            self.tracks = tracks
            super().__init__()

    class Likes(Message):
        def __init__(self, tracks: list):
            self.tracks = tracks
            super().__init__()

    def action_play(self):
        cursor: TreeNode = self.cursor_node
        menu = cursor.parent
        if menu.data in ('next', 'prev'):
            return
        if cursor.data:
            tracks = menu.get_tracks(cursor.data)
            message = self.Play(tracks)
            self.post_message(message)

    class Play(Message):
        """Tell the app to play a playlist"""

        def __init__(self, tracks: list[Track]):
            self.tracks = tracks
            super().__init__()

    def action_download(self):
        cursor: TreeNode = self.cursor_node
        menu = cursor.parent
        if menu.data in ('next', 'prev'):
            return
        if cursor.data:
            tracks = menu.get_tracks(cursor.data)
            message = self.Download(tracks)
            self.post_message(message)

    class Download(Message):
        """Tell the app to download a playlist"""

        def __init__(self, tracks: list[Track]):
            self.tracks = tracks
            super().__init__()

    def action_space(self):
        self.app.action_pause()


class ArtistMenu(MenuNode):
    def __init__(self):
        super().__init__()
        self._label = '关注的艺人'

    @staticmethod
    @cache
    def request(page=0):
        offset = page * 9
        payload = apis.user.GetUserArtistSubs(9, offset)
        has_more = payload['hasMore']
        data = [(ar['name'], ar['id']) for ar in payload['data']]
        return has_more, data

    @staticmethod
    @cache
    def get_tracks(artist_id: str):
        payload = apis.user.GetArtistTopSongs(artist_id)['songs']
        tracks = []
        for tr in payload:
            name = tr['name']
            track_id = tr['id']
            artists = {ar['id']: ar['name'] for ar in tr['ar']}
            album = tr['al']['name']
            album_id = tr['al']['id']
            tracks.append(Track(name, track_id, artists, album, album_id))
        return tracks


class AlbumMenu(MenuNode):
    def __init__(self):
        super().__init__()
        self._label = '收藏的专辑'

    @staticmethod
    @cache
    def request(page=0):
        offset = page * 9
        payload = apis.user.GetUserAlbumSubs(9, offset)
        has_more = payload['hasMore']
        data = [(ar['name'][:30], ar['id']) for ar in payload['data']]
        return has_more, data

    @staticmethod
    @cache
    def get_tracks(album_id: str) -> list:
        payload = apis.album.GetAlbumInfo(album_id)['songs']
        tracks = []
        for tr in payload:
            name = tr['name']
            track_id = tr['id']
            artists = {ar['id']: ar['name'] for ar in tr['ar']}
            album = tr['al']['name']
            album_id = tr['al']['id']
            tracks.append(Track(name, track_id, artists, album, album_id))
        return tracks


class PlaylistMenu(MenuNode):
    def __init__(self):
        super().__init__()
        self._label = '创建的歌单'

    @staticmethod
    def request(page=0):
        payload = apis.user.GetUserPlaylists()['playlist']
        data = [(pl['name'], pl['id']) for pl in payload]
        return False, data

    def prev(self) -> None:
        return

    def next(self) -> None:
        return

    @staticmethod
    @cache
    def get_tracks(playlist: str) -> list:
        payload = apis.playlist.GetPlaylistInfo(playlist)['playlist']['tracks']
        tracks = []
        for tr in payload:
            name = tr['name']
            track_id = tr['id']
            artists = {ar['id']: ar['name'] for ar in tr['ar']}
            album = tr['al']['name']
            album_id = tr['al']['id']
            tracks.append(Track(name, track_id, artists, album, album_id))
        return tracks


@cache
def get_daily_songs() -> list[Track]:
    payload = apis.user.GetDailyRecommends()['data']['dailySongs']
    tracks = []
    for tr in payload:
        name = tr['name']
        track_id = tr['id']
        artists = {ar['id']: ar['name'] for ar in tr['ar']}
        album = tr['al']['name']
        album_id = tr['al']['id']
        tracks.append(Track(name, track_id, artists, album, album_id))
    return tracks
