import sys
from _login import login
from _menu import MenuTree
from _table import *
from _downloader import Downloader
from _player import Player
from _proxy import app as proxy
from _search import Search
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer
from pathlib import Path
from multiprocessing import Process


if getattr(sys, "frozen", False):
    # The application is frozen
    datadir = Path(sys.executable).parent
else:
    # The application is not frozen
    datadir = Path(__file__).parent


class NeteaseCloudMusic(App):
    """A textual user interface for Netease Cloud Music"""

    CSS_PATH = datadir.joinpath('app.css')
    TITLE = '网易云音乐'
    BINDINGS = [
        Binding('q', 'quit', '退出'),
        Binding('m', 'mode', 'Toggle Mode', show=False),
        Binding('g', 'current', 'Current', show=False),
        Binding('space', 'pause', 'Play/Pause', show=False),
        Binding('left_square_bracket', 'prev', 'Prev', show=False),
        Binding('right_square_bracket', 'next', 'Next', show=False),
        Binding('ctrl+f', 'like', 'Like/Unlike', show=False),
        Binding('ctrl+d', 'download', 'Download/Delete', show=False)
    ]
    downloader = Downloader()

    def compose(self) -> ComposeResult:
        yield Header()
        yield MenuTree(label='我的', id='tree')
        yield Search(id='searchbar', placeholder='搜索歌曲')
        yield Tables(id='tables')
        yield Player(id='player')
        yield Footer()

    def action_like(self):
        player: Player = self.query_one(Player)
        table: TrackTable = self.query_one(TrackTable)
        if track := player.track:
            table.like(track)

    def action_download(self):
        player: Player = self.query_one(Player)
        table: TrackTable = self.query_one(TrackTable)
        track = player.track
        if not track:
            return

        # If track is already local, delete its file
        if track.local:
            Path().joinpath('downloads', f'{track.id}.mp3').unlink()
            track.local = False
            table.unlocal(track)
        else:
            table.watchlist.add(track)
            self.downloader.submit(track)

    def action_quit(self):
        self.downloader.shutdown()
        self.exit()

    def action_pause(self):
        player: Player = self.query_one(Player)
        player.pause()

    def action_mode(self):
        player: Player = self.query_one(Player)
        player.toggle_mode()

    def action_current(self):
        player: Player = self.query_one(Player)
        table: TrackTable = self.query_one(TrackTable)
        if player.playlist:
            table.tracks = player.playlist
            table.update()
            table.scroll_to_track(player.track)

    def action_prev(self):
        player: Player = self.query_one(Player)
        player.prev()

    def action_next(self):
        player: Player = self.query_one(Player)
        player.next()

    def on_menu_tree_update_table(self, message: MenuTree.UpdateTable):
        table: TrackTable = self.query_one(TrackTable)
        table.tracks = message.tracks
        table.update()

    def on_menu_tree_likes(self, message: MenuTree.Likes):
        table: TrackTable = self.query_one(TrackTable)
        table.likes = message.tracks

    def on_menu_tree_play(self, message: MenuTree.Play):
        player: Player = self.query_one(Player)
        if message.tracks:
            player.play_playlist(message.tracks)

    def on_menu_tree_download(self, message: MenuTree.Download):
        table: TrackTable = self.query_one(TrackTable)
        for track in message.tracks:
            if not track.local:
                table.watchlist.add(track)
                self.downloader.submit(track)

    def on_track_table_play(self, message: TrackTable.Play):
        player: Player = self.query_one(Player)
        player.play(message.track)
        player.set_playlist(message.tracks)

    def on_track_table_liked(self, message: TrackTable.Liked):
        player: Player = self.query_one(Player)
        if player.track is message.track:
            player.refresh()

    def on_track_table_download(self, message: TrackTable.Download):
        track = message.track
        self.downloader.submit(track)

    def on_search_update_table(self, message: Search.UpdateTable):
        tables = self.query_one(Tables)
        tables.switch(message.mode)

        if message.mode == 1:
            table = self.query_one(TrackTable)
            table.tracks = message.results
        elif message.mode == 10:
            table = self.query_one(AlbumTable)
            table.albums = message.results
        elif message.mode == 100:
            table = self.query_one(ArtistTable)
            table.artists = message.results
        else:
            table = self.query_one(PlaylistTable)
            table.playlists = message.results

        table.update()
        table.focus()


# if __name__ == '__main__':
login()
server = Process(target=proxy.run)
server.start()
app = NeteaseCloudMusic()
app.run()
server.terminate()
server.join()
