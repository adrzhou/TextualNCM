from _login import login
from _menu import MenuTree
from _table import TrackTable
from _downloader import Downloader
from _player import Player
from _proxy import app as proxy
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, DataTable
from textual.containers import Container
from multiprocessing import Process


class NeteaseCloudMusic(App):
    """A textual user interface for Netease Cloud Music"""

    CSS_PATH = 'app.css'
    BINDINGS = [Binding('p', 'play', 'Play'),
                ('d', 'download', 'Download'), ('q', 'quit', 'Quit')]
    downloader = Downloader()

    def compose(self) -> ComposeResult:
        yield Header()
        yield MenuTree('我的', )
        yield TrackTable(id='table')
        yield Container(Player(), id='player')
        yield Footer()

    def action_download(self):
        table: TrackTable = self.query_one(DataTable)
        track = table.tracks[table.cursor_row]
        self.downloader.submit(track)
        table.watchlist.add(track)

    def action_like(self):
        table: TrackTable = self.query_one(DataTable)
        track = table.tracks[table.cursor_row]
        track.liked = not track.liked
        if track.liked:
            table.data[table.cursor_row][0] = ":sparkling_heart:"
        else:
            table.data[table.cursor_row][0] = ""
        table.refresh_cell(table.cursor_row, 0)
        table._clear_caches()  # noqa

    def action_quit(self):
        self.downloader.shutdown()
        self.exit()

    def on_menu_tree_update_table(self, message: MenuTree.UpdateTable):
        table: TrackTable = self.query_one(DataTable)
        table.tracks = message.tracks
        table.update()

    def on_track_table_play(self, message: TrackTable.Play):
        player: Player = self.query_one(Player)
        player.play(message.track)
        player.set_playlist(message.tracks)

    def key_space(self):
        player: Player = self.query_one(Player)
        player.pause()

    def key_m(self):
        player: Player = self.query_one(Player)
        player.toggle_mode()

    def key_left_square_bracket(self):
        player: Player = self.query_one(Player)
        player.prev()

    def key_right_square_bracket(self):
        player: Player = self.query_one(Player)
        player.next()


if __name__ == '__main__':
    login()
    server = Process(target=proxy.run)
    server.start()
    app = NeteaseCloudMusic()
    app.run()
    server.terminate()
    server.join()
