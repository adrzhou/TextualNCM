import os
import vlc
from pyncm import apis
from pyncm import DumpSessionAsString, SetCurrentSession, LoadSessionFromString, GetCurrentSession
from functools import cache
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, TreeNode, DataTable


class MenuNode(TreeNode):
    def __init__(self):  # noqa
        self.data = None
        self._expanded = True
        self._children: list[TreeNode] = []
        self.page: int = -1

        self._hover_ = False
        self._selected_ = False
        self._allow_expand = True
        self._updates: int = 0
        self._line: int = -1

    def request(self, page: int) -> tuple:
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

    def get_tracks(self, node: TreeNode) -> list:
        pass


class ArtistMenu(MenuNode):
    def __init__(self):
        super().__init__()
        self.label = '关注的艺人'

    @cache
    def request(self, page):
        offset = page * 5
        payload = apis.user.GetUserArtistSubs(5, offset)
        has_more = payload['hasMore']
        data = [(artist['name'], artist['id']) for artist in payload['data']]
        return has_more, data


class AlbumMenu(MenuNode):
    def __init__(self):
        super().__init__()
        self.label = '收藏的专辑'

    @cache
    def request(self, page):
        offset = page * 5
        payload = apis.user.GetUserAlbumSubs(5, offset)
        has_more = payload['hasMore']
        data = [(artist['name'], artist['id']) for artist in payload['data']]
        return has_more, data

    @cache
    def get_tracks(self, node: TreeNode) -> list:
        tracks = apis.album.GetAlbumInfo(node.data)['songs']
        rows = []
        for track in tracks:
            name = track['name']
            artists = ', '.join([artist['name'] for artist in track['ar']])
            album = track['al']['name']
            local = str(False)
            track_id = track['id']
            rows.append((name, artists, album, local, track_id))
        return rows


class PlaylistMenu(MenuNode):
    def __init__(self):
        super().__init__()
        self.label = '创建的歌单'

    def request(self, page=0):
        payload = apis.user.GetUserPlaylists()
        data = [(pl['name'], pl['id']) for pl in payload['playlist']]
        return False, data

    def next(self) -> None:
        _, data = self.request()
        for item in data:
            self.add_leaf(*item)

    @cache
    def get_tracks(self, node: TreeNode) -> list:
        tracks = apis.playlist.GetPlaylistInfo(node.data)['playlist']['tracks']
        rows = []
        for track in tracks:
            name = track['name']
            artists = ', '.join([artist['name'] for artist in track['ar']])
            album = track['al']['name']
            local = str(False)
            track_id = track['id']
            rows.append((name, artists, album, local, track_id))
        return rows


class TrackTable(DataTable):
    def __init__(self):
        super().__init__()
        self.add_columns('Track', 'Artist', 'Album', 'Local')
        self.tracks: list = []
        self.player: vlc.MediaPlayer | None = None

    def add_tracks(self):
        self.add_rows(self.tracks)
        self.refresh()

    def download(self):
        track_id = self.tracks[self.cursor_row][-1]
        audio = apis.track.GetTrackAudioV1(track_id, level='exhigh')
        audio = audio.get("data", [{"url": ""}])[0]
        if not audio['url']:
            print('无法下载，资源不存在')
            return
        response = GetCurrentSession().get(audio['url'], stream=True)
        dst = rf'downloads/{track_id}.{audio["type"].lower()}'
        with open(dst, 'wb') as fp:
            for chunk in response.iter_content(128 * 2 ** 10):
                fp.write(chunk)

    def play(self):
        if self.player and self.player.is_playing():
            self.player.stop()
        track_id = self.tracks[self.cursor_row][-1]
        if f'{track_id}.mp3' not in os.listdir('downloads'):
            self.download()
        self.player = vlc.MediaPlayer(f'downloads/{track_id}.mp3')
        self.player.play()

    def pause(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        if self.player:
            self.player.stop()


class MenuTree(Tree):
    def __init__(self, table: TrackTable):
        super().__init__('我的')
        self.table = table
        artist = self.add_menu(ArtistMenu())
        artist.next()
        album = self.add_menu(AlbumMenu())
        album.next()
        playlist = self.add_menu(PlaylistMenu())
        playlist.next()

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
                self.table.clear()
                self.table.tracks = menu.get_tracks(cursor)
                self.table.add_tracks()


class NeteaseCloudMusic(App):
    """A textual user interface for Netease Cloud Music"""

    CSS_PATH = 'app.css'
    BINDINGS = [('d', 'download', 'Download'), ('p', 'play', 'Play'),
                ('x', 'pause', 'Pause'), ('s', 'stop', 'Stop'), ('q', 'quit', 'Quit')]

    def compose(self) -> ComposeResult:
        table = TrackTable()
        yield Header()
        yield MenuTree(table)
        yield table
        yield Footer()

    def action_download(self):
        table: TrackTable = self.query_one(DataTable)
        table.download()

    def action_play(self):
        table: TrackTable = self.query_one(DataTable)
        table.play()

    def action_pause(self):
        table: TrackTable = self.query_one(DataTable)
        table.pause()

    def action_stop(self):
        table: TrackTable = self.query_one(DataTable)
        table.stop()

    def action_quit(self):
        self.exit()


def login():
    with open('save') as fp:
        save = fp.read()

    def choose():
        print('Please choose')
        print('1. Login via email')
        print('2. Login via cellphone')
        via = input('Choice: ')
        if via not in '12':
            print('Invalid choice')
            return choose()
        return via

    if not save:
        choice = choose()
        if choice == '1':
            email, phone = input('Email: '), ''
            passwd = input('Password: ')
            try:
                apis.login.LoginViaEmail(email, passwd)
            except apis.login.LoginFailedException:
                print('Login failed')
                login()
        else:
            phone, email = input('Phone: '), ''
            passwd = input('Password: ')
            try:
                apis.login.LoginViaCellphone(phone, passwd)
            except apis.login.LoginFailedException:
                print('Login failed')
                login()
        if input('Save current session for automatic login? (y/N) ') == 'y':
            session = DumpSessionAsString(GetCurrentSession())
            with open('save', 'w') as fp:
                fp.write(session)
    else:
        SetCurrentSession(LoadSessionFromString(save))


# if __name__ == '__main__':
login()
app = NeteaseCloudMusic()
app.run()
