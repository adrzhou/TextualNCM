from pyncm import apis
from functools import cache
from dataclasses import dataclass
from rich.progress import Progress, BarColumn
from textual.widgets import Tree, TreeNode
from textual.message import Message, MessageTarget


@dataclass
class Track:
    name: str = ''
    id: int = 0
    artists: str = ''
    album: str = ''
    album_id: int = 0
    local: bool | None = None
    liked: bool | None = None
    length: int = 0
    xfered: int = 0
    progress: Progress = Progress(BarColumn(), auto_refresh=False)
    bar = progress.add_task('', total=None)

    def get_progress(self):
        with self.progress as progress:
            progress.update(self.bar, total=self.length, completed=self.xfered)
            progress.refresh()
            return progress

    def __hash__(self):
        return self.id


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

    def request(self, page: int) -> tuple:
        # Abstract method: Requests data from API
        pass

    def get_tracks(self, entry_id: str) -> list:
        # Abstract method: Requests track list from API
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
            first = self._children[0]
            first.set_label('<上一页')
            first.data = 'prev'
            for i in range(len(data)):
                node = self._children[i + 1]
                node.set_label(data[i][0])
                node.data = data[i][1]
            if has_more:
                self.add_leaf('下一页>', 'next')
        else:
            for i in range(len(data)):
                node = self._children[i + 1]
                node.set_label(data[i][0])
                node.data = data[i][1]
            if not has_more:
                last = self._children[-1]
                self.remove(last)

    def prev(self) -> None:
        self.page -= 1
        _, data = self.request(self.page)
        if self.page == 0:
            first = self._children[0]
            self.remove(first)
            for i in range(len(data)):
                node = self._children[i]
                node.set_label(data[i][0])
                node.data = data[i][1]
        else:
            for i in range(len(data)):
                node = self._children[i + 1]
                node.set_label(data[i][0])
                node.data = data[i][1]

    def remove(self, node: TreeNode):
        self._updates += 1
        self._tree._updates += 1  # noqa
        del self._tree._nodes[node.id]  # noqa
        self._children.remove(node)
        self._tree._invalidate()  # noqa


class MenuTree(Tree):
    def __init__(self):
        super().__init__('我的')
        self.add_menu(ArtistMenu()).next()
        self.add_menu(AlbumMenu()).next()
        self.add_menu(PlaylistMenu()).next()

    def add_menu(self, node: MenuNode):
        node._tree = self
        node._parent = self.root
        node._id = self._new_id()
        node._label = self.process_label(node.label)
        self._nodes[node._id] = node  # noqa
        self._updates += 1
        self.root._updates += 1  # noqa
        self.root._children.append(node)  # noqa
        self._invalidate()
        return node

    def on_tree_node_selected(self, message: Tree.NodeSelected):
        cursor = message.node
        menu: MenuNode = cursor._parent  # noqa
        if cursor.data:
            if cursor.data == 'next':
                menu.next()
            elif cursor.data == 'prev':
                menu.prev()
            else:
                tracks = menu.get_tracks(cursor.data)
                message = self.UpdateTable(self, tracks)
                self.emit_no_wait(message)

    class UpdateTable(Message):
        """Update track table message"""

        def __init__(self, sender: MessageTarget, tracks: list):
            self.tracks = tracks
            super().__init__(sender)


class ArtistMenu(MenuNode):
    def __init__(self):
        super().__init__()
        self.label = '关注的艺人'

    @cache
    def request(self, page):
        offset = page * 7
        payload = apis.user.GetUserArtistSubs(7, offset)
        has_more = payload['hasMore']
        data = [(artist['name'], artist['id']) for artist in payload['data']]
        return has_more, data

    @cache
    def get_tracks(self, artist_id: str):
        payload = apis.user.GetArtistTopSongs(artist_id)['songs']
        tracks = []
        for track in payload:
            name = track['name']
            track_id = track['id']
            artists = ', '.join([artist['name'] for artist in track['ar']])
            album = track['al']['name']
            album_id = track['al']['id']
            tracks.append(Track(name, track_id, artists, album, album_id))
        return tracks


class AlbumMenu(MenuNode):
    def __init__(self):
        super().__init__()
        self.label = '收藏的专辑'

    @cache
    def request(self, page):
        offset = page * 7
        payload = apis.user.GetUserAlbumSubs(7, offset)
        has_more = payload['hasMore']
        data = [(artist['name'], artist['id']) for artist in payload['data']]
        return has_more, data

    @cache
    def get_tracks(self, album_id: str) -> list:
        payload = apis.album.GetAlbumInfo(album_id)['songs']
        tracks = []
        for track in payload:
            name = track['name']
            track_id = track['id']
            artists = ', '.join([artist['name'] for artist in track['ar']])
            album = track['al']['name']
            album_id = track['al']['id']
            tracks.append(Track(name, track_id, artists, album, album_id))
        return tracks


class PlaylistMenu(MenuNode):
    def __init__(self):
        super().__init__()
        self.label = '创建的歌单'

    def request(self, page=0):
        payload = apis.user.GetUserPlaylists()['playlist']
        data = [(pl['name'], pl['id']) for pl in payload]
        return False, data

    def next(self) -> None:
        _, data = self.request()
        for item in data:
            self.add_leaf(*item)

    @cache
    def get_tracks(self, playlist: str) -> list:
        payload = apis.playlist.GetPlaylistInfo(playlist)['playlist']['tracks']
        tracks = []
        for track in payload:
            name = track['name']
            track_id = track['id']
            artists = ', '.join([artist['name'] for artist in track['ar']])
            album = track['al']['name']
            album_id = track['al']['id']
            tracks.append(Track(name, track_id, artists, album, album_id))
        return tracks
