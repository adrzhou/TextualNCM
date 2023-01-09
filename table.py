from pyncm import apis
from pathlib import Path
from textual.widgets import DataTable


class TrackTable(DataTable):
    def __init__(self):
        super().__init__(id='table')
        self.add_column('Liked')
        self.add_column('Track', width=40)
        self.add_column('Artist', width=30)
        self.add_column('Album', width=30)
        self.add_column('Local', width=30)
        self.tracks: list = []
        self.watchlist: set = set()
        self.set_interval(1, self.update_progress)

    def update(self):
        self.clear()
        like_list: list = apis.user.GetUserLikeList()['ids']
        for track in self.tracks:
            row = []
            if track.liked is None:
                track.liked = track.id in like_list
            if track.liked:
                row.append(":sparkling_heart:")
            else:
                row.append('')
            row.extend([track.name, track.artists, track.album])
            if track.local is None:
                track.local = Path().joinpath('downloads', f'{track.id}.mp3').exists()
            if track.local:
                row.append(':white_heavy_check_mark:')
            else:
                row.append('')
            self.add_row(*row)
        self.refresh()

    def update_progress(self):
        for track in tuple(self.watchlist):
            try:
                row = self.tracks.index(track)
            except ValueError:
                continue
            if track.local:
                self.watchlist.remove(track)
                self.data[row][-1] = ':white_heavy_check_mark:'
            else:
                self.data[row][-1] = track.get_progress()
            self.refresh_cell(row, 4)
            self._clear_caches()
