from vlc import MediaPlayer
from _track import Track
from datetime import timedelta
from random import randint
from textual.widgets import Static
from textual.reactive import reactive
from rich.progress import Progress, BarColumn, TextColumn
from rich.console import group
from rich.text import Text
from rich.columns import Columns
from pyncm import apis


class Player(Static):  
    player: MediaPlayer = MediaPlayer()
    track: Track = Track.EmptyTrack()
    progress = Progress(TextColumn('{task.fields[elapsed]}'),
                        BarColumn(bar_width=None),
                        TextColumn('{task.fields[length]}'),
                        auto_refresh=False,
                        expand=True)
    bar = progress.add_task('', total=None, elapsed='0:00', length='0:00')
    time: int = reactive(0)
    playing: bool = reactive(player.is_playing)
    paused: bool = True
    mode: str = 'loop'
    playlist: list = []
    index: int = 0

    def on_mount(self):
        self.update(self.get_renderable())
        self.set_interval(0.9, self.update_time)
        self.set_interval(0.5, self.update_playing)

    @group()
    def get_renderable(self):
        last = "⏮ [ 上一首"
        play = "⏯ [ 空格]播放" if self.paused else "⏯ [ 空格]暂停"
        _next = "⏭ ] 下一首"
        if self.mode == 'loop':
            mode = '🔁 [M]列表循环'
        elif self.mode == 'single':
            mode = '🔂 [M]单曲循环'
        else:
            mode = '🔀 [M]随机播放'
        columns = (last, play, _next, mode)
        yield Text(self.track.name, justify='center')
        yield Text(self.track.artists, justify='center')
        yield self.progress
        yield Columns(columns, expand=True)

    def play(self, track: Track):
        self.player.stop()
        self.track = track
        if track.local:
            url = f'downloads/{track.id}.mp3'
        else:
            track.length = apis.track.GetTrackDetail([track.id])['songs'][0]['dt']
            url = f'http://127.0.0.1:5000/track/{track.id}'
        self.player = MediaPlayer(url)
        self.player.play()
        self.paused = False
        self.update(self.get_renderable())

    def pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.paused = True
        elif self.player.will_play():
            self.player.play()
            self.paused = False
        self.update(self.get_renderable())

    def set_playlist(self, playlist: list[Track]):
        self.playlist = playlist
        self.index = playlist.index(self.track)

    def prev(self):
        if self.playlist:
            self.index = (self.index - 1) % len(self.playlist)
            track = self.playlist[self.index]
            self.play(track)

    def next(self):
        if self.playlist:
            if self.mode == 'shuffle':
                self.index = randint(0, len(self.playlist))
            else:
                self.index = (self.index + 1) % len(self.playlist)
            track = self.playlist[self.index]
            self.play(track)

    def toggle_mode(self):
        if self.mode == 'loop':
            self.mode = 'single'
        elif self.mode == 'single':
            self.mode = 'shuffle'
        elif self.mode == 'shuffle':
            self.mode = 'loop'
        self.update(self.get_renderable())

    def update_time(self) -> None:
        if self.player.is_playing():
            self.time = self.player.get_time()

    def update_playing(self) -> None:
        self.playing = self.player.is_playing()

    def watch_time(self, time: int):
        with self.progress as progress:
            elapsed = str(timedelta(seconds=round(time/1000)))[2:]
            if self.track.local:
                length = str(timedelta(seconds=round(self.player.get_length()/1000)))[2:]
                progress.update(self.bar, elapsed=elapsed, length=length, total=self.player.get_length(),
                                completed=time)
            else:
                length = str(timedelta(seconds=round(self.track.length/1000)))[2:]
                progress.update(self.bar, elapsed=elapsed, length=length, total=self.track.length, completed=time)
            progress.refresh()

    def watch_playing(self):
        if not self.paused and not self.playing:
            if self.mode == 'single':
                self.play(self.track)
            else:
                self.next()