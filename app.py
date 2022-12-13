import json
from pyncm import apis
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, TreeNode, DataTable


class MenuTree(Tree):
    def __init__(self):
        super().__init__('我的')
        artists = self.root.add('关注的艺人')
        artists.api = apis.user.GetUserArtistSubs
        albums = self.root.add('收藏的专辑')
        albums.api = apis.user.GetUserAlbumSubs
        playlists = self.root.add('创建的歌单')
        playlists.api = apis.user.GetUserPlaylists

    def get_children(self, node: TreeNode):
        payload = node.api()


class TrackTable(DataTable):
    def __init__(self):
        super().__init__()


class NeteaseCloudMusic(App):
    """A textual user interface for Netease Cloud Music"""

    def compose(self) -> ComposeResult:
        yield Header()
        yield MenuTree()
        yield Footer()


def login():
    with open('credentials') as fp:
        credentials = json.load(fp)

    def choose():
        print('Please choose')
        print('1. Login via email')
        print('2. Login via cellphone')
        via = input('Choice: ')
        if via not in '12':
            print('Invalid choice')
            return choose()
        return via

    if not credentials['password']:
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
        save = input('Save login info for automatic login? (y/N) ')
        if save:
            credentials['email'] = email
            credentials['phone'] = phone
            credentials['password'] = passwd
            with open('credentials', 'w') as fp:
                json.dump(credentials, fp)
    elif email := credentials['email']:
        passwd = credentials['password']
        try:
            apis.login.LoginViaEmail(email, passwd)
        except apis.login.LoginFailedException:
            print('Login failed')
            credentials['password'] = ''
            login()
    elif phone := credentials['phone']:
        passwd = credentials['password']
        try:
            apis.login.LoginViaCellphone(phone, passwd)
        except apis.login.LoginFailedException:
            print('Login failed')
            credentials['password'] = ''
            login()


if __name__ == '__main__':
    login()
    app = NeteaseCloudMusic()
    app.run()
