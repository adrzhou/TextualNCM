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
        self.page: int = -1
        self._expanded = True
        self._children: list[TreeNode] = []
        self._hover_ = False
        self._selected_ = False
        self._allow_expand = True
        self._updates: int = 0
        self._line: int = -1

    @staticmethod
    def request(page: int) -> tuple[bool, list]:
        # Abstract method: Requests data from API for children nodes
        pass

    @staticmethod
    def get_tracks(entry_id: str) -> list[Track]:
        # Abstract method: Requests track list from API for track table
        pass

    def next(self) -> None:
        self.page += 1
        has_more, data = self.request(self.page)
        if self.page == 0:
            for item in data:
                self.add_leaf(*item)
            if has_more:
                self.add_leaf('下一页>', 'next')
        elif self.page == 1:
            first = self.children[0]
            first.set_label('<上一页')
            first.data = 'prev'
            for i in range(len(data)):
                node = self.children[i + 1]
                node.set_label(data[i][0])
                node.data = data[i][1]
            if has_more:
                self.add_leaf('下一页>', 'next')
        else:
            for i in range(len(data)):
                node = self.children[i + 1]
                node.set_label(data[i][0])
                node.data = data[i][1]
            if not has_more:
                last = self.children[-1]
                self.remove(last)

    def prev(self) -> None:
        self.page -= 1
        _, data = self.request(self.page)
        if self.page == 0:
            first = self.children[0]
            self.remove(first)
            for i in range(len(data)):
                node = self.children[i]
                node.set_label(data[i][0])
                node.data = data[i][1]
        else:
            for i in range(len(data)):
                node = self.children[i + 1]
                node.set_label(data[i][0])
                node.data = data[i][1]

    def remove(self, node: TreeNode):
        self._updates += 1
        self._tree._updates += 1  # noqa
        del self._tree._nodes[node.id]  # noqa
        self._children.remove(node)
        self._tree._invalidate()  # noqa


class MenuTree(Tree):
    BINDINGS = [
        Binding("k", "cursor_up", "Cursor Up", show=False),
        Binding("j", "cursor_down", "Cursor Down", show=False),
        Binding("p", "play", "Play"),
        Binding("d", "download", "Download"),
        Binding('space', 'space', 'Space')  # Override default binding
    ]

    def on_mount(self):
        self.root.add_leaf('每日推荐歌曲')
        self.add_menu(ArtistMenu()).next()
        self.add_menu(AlbumMenu()).next()
        self.add_menu(PlaylistMenu()).next()
        self.action_select_cursor()

        playlist_menu: MenuNode = self.root.children[2]
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

    def action_select_cursor(self):
        super().action_select_cursor()
        cursor = self.cursor_node
        menu = cursor.parent
        if cursor.data == 'next':
            menu.next()
            self.refresh()
        elif cursor.data == 'prev':
            menu.prev()
            self.refresh()
        elif cursor.label.plain == '每日推荐歌曲':
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
    def request(page):
        offset = page * 7
        payload = apis.user.GetUserArtistSubs(7, offset)
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
    def request(page):
        offset = page * 7
        payload = apis.user.GetUserAlbumSubs(7, offset)
        has_more = payload['hasMore']
        data = [(ar['name'], ar['id']) for ar in payload['data']]
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

    def next(self) -> None:
        _, data = self.request()
        for item in data:
            self.add_leaf(*item)

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
