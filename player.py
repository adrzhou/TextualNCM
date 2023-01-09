from vlc import MediaPlayer
from menu import Track
from datetime import timedelta
from textual.widgets import Static
from textual.reactive import reactive
from rich.progress import Progress, BarColumn, TextColumn
from rich.console import group
from rich.text import Text


class Player(Static):
    player: MediaPlayer = MediaPlayer()
    track: Track = Track()
    progress = Progress(TextColumn('{task.fields[elapsed]}'),
                        BarColumn(bar_width=None),
                        TextColumn('{task.fields[length]}'),
                        auto_refresh=False,
                        expand=True)
    bar = progress.add_task('', total=None, elapsed='0:00', length='0:00')
    time = reactive(0)

    def on_mount(self):
        self.update(self.get_renderable())
        self.set_interval(0.9, self.update_time)

    @group()
    def get_renderable(self):
        title = Text(self.track.name, justify='center')
        artists = Text(self.track.artists, justify='center')
        yield title
        yield artists
        yield self.progress

    def play(self, track: Track):
        self.track = track
        self.update(self.get_renderable())
        filepath = f'downloads/{track.id}.mp3'
        self.player = MediaPlayer(filepath)
        self.player.play()

    def update_time(self) -> None:
        if self.player.is_playing():
            self.time = self.player.get_time()

    def watch_time(self, time: int):
        with self.progress as progress:
            elapsed = str(timedelta(seconds=round(time/1000)))[2:]
            length = str(timedelta(seconds=round(self.player.get_length()/1000)))[2:]
            progress.update(self.bar, elapsed=elapsed, length=length, total=self.player.get_length(), completed=time)
            progress.refresh()
