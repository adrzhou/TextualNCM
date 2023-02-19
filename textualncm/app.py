from _login import login
from _menu import MenuTree
from _table import TrackTable
from _downloader import Downloader
from _player import Player
from _proxy import app as proxy
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, DataTable
from multiprocessing import Process


class NeteaseCloudMusic(App):
    """A textual user interface for Netease Cloud Music"""

    CSS_PATH = 'app.css'
    BINDINGS = [
        Binding('p', 'play', 'Play'),
        Binding('d', 'download', 'Download'),
        Binding('q', 'quit', 'Quit'),
        Binding('m', 'mode', 'Toggle Mode', show=False),
        Binding('space', 'pause', 'Play/Pause', show=False, priority=True),
        Binding('left_square_bracket', 'prev', 'Prev', show=False),
        Binding('right_square_bracket', 'next', 'Next', show=False),
        Binding('ctrl+f', 'like', 'Like/Unlike', show=False)
    ]
    downloader = Downloader()

    def compose(self) -> ComposeResult:
        yield Header()
        yield MenuTree('我的', )
        yield TrackTable(id='table')
        yield Player(id='player')
        yield Footer()

    def action_download(self):
        table: TrackTable = self.query_one(DataTable)
        track = table.tracks[table.cursor_row]

        def done(_):
            table.locals.append(track.id)

        future = self.downloader.submit(track)
        future.add_done_callback(done)
        table.watchlist.add(track)

    def action_like(self):
        player: Player = self.query_one(Player)
        table: TrackTable = self.query_one(DataTable)
        track = player.track
        table.like(track)

    def action_quit(self):
        self.downloader.shutdown()
        self.exit()

    def action_pause(self):
        print('action triggered')
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

    def on_menu_tree_likes(self, message: MenuTree.Likes):
        table: TrackTable = self.query_one(TrackTable)
        table.likes = message.tracks

    def on_track_table_play(self, message: TrackTable.Play):
        player: Player = self.query_one(Player)
        player.play(message.track)
        player.set_playlist(message.tracks)

    def on_track_table_liked(self, message: TrackTable.Liked):
        player: Player = self.query_one(Player)
        if player.track is message.track:
            player.refresh()


# if __name__ == '__main__':
login()
server = Process(target=proxy.run)
server.start()
app = NeteaseCloudMusic()
app.run()
server.terminate()
server.join()
