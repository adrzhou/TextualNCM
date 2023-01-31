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
    BINDINGS = [
        Binding('p', 'play', 'Play'),
        Binding('d', 'download', 'Download'),
        Binding('q', 'quit', 'Quit'),
        Binding('m', 'mode', 'Toggle Mode', show=False),
        Binding('space', 'pause', 'Play/Pause', show=False),
        Binding('left_square_bracket', 'prev', 'Prev', show=False),
        Binding('right_square_bracket', 'next', 'Next', show=False)
    ]
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

    def action_pause(self):
        player: Player = self.query_one(Player)
        player.pause()

    def action_mode(self):
        player: Player = self.query_one(Player)
        player.toggle_mode()

    def action_prev(self):
        player: Player = self.query_one(Player)
        player.prev()

    def action_next(self):
        player: Player = self.query_one(Player)
        player.next()

    def on_menu_tree_update_table(self, message: MenuTree.UpdateTable):
        table: TrackTable = self.query_one(DataTable)
        table.tracks = message.tracks
        table.update()

    def on_track_table_play(self, message: TrackTable.Play):
        player: Player = self.query_one(Player)
        player.play(message.track)
        player.set_playlist(message.tracks)


if __name__ == '__main__':
    login()
    server = Process(target=proxy.run)
    server.start()
    app = NeteaseCloudMusic()
    app.run()
    server.terminate()
    server.join()
