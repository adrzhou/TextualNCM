from pyncm import apis
from menu import MenuTree
from table import TrackTable
from downloader import Downloader
from player import Player
from pyncm import DumpSessionAsString, SetCurrentSession, LoadSessionFromString, GetCurrentSession
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable


class NeteaseCloudMusic(App):
    """A textual user interface for Netease Cloud Music"""

    CSS_PATH = 'app.css'
    BINDINGS = [('p', 'play', 'Play'), ('l', 'like', 'Like/Unlike'),
                ('d', 'download', 'Download'), ('q', 'quit', 'Quit')]
    downloader = Downloader()

    def compose(self) -> ComposeResult:
        yield Header()
        yield MenuTree()
        yield TrackTable()
        yield Player()
        yield Footer()

    def action_play(self):
        table: TrackTable = self.query_one(DataTable)
        track = table.tracks[table.cursor_row]
        if not track.local:
            self.downloader.submit(track)
        player: Player = self.query_one(Player)
        player.play(track)

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
        self.exit()

    def on_menu_tree_update_table(self, message: MenuTree.UpdateTable):
        table: TrackTable = self.query_one(DataTable)
        table.tracks = message.tracks
        table.update()


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
        if input('Save current session for automatic login? (Y/n) ') == 'Y':
            session = DumpSessionAsString(GetCurrentSession())
            with open('save', 'w') as fp:
                fp.write(session)
    else:
        SetCurrentSession(LoadSessionFromString(save))


# if __name__ == '__main__':
login()
app = NeteaseCloudMusic()
app.run()
