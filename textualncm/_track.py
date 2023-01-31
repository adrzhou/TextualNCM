from dataclasses import dataclass
from rich.progress import Progress, BarColumn


@dataclass
class Track:
    name: str
    id: int
    artists: str
    album: str
    album_id: int
    local: bool | None = None
    liked: bool | None = None
    length: int = 0
    size: int = 0
    xfered: int = 0
    _progress: Progress = Progress(BarColumn(), auto_refresh=False)
    task = _progress.add_task('', total=None)

    @property
    def progress(self):
        with self._progress as p:
            p.update(self.task, total=self.size, completed=self.xfered)
            return p

    @dataclass
    class EmptyTrack:
        # The player receives this placeholder object at startup
        name: str = ''
        artists: str = ''
        local: bool = False
        liked: bool = False
        length: int = 0

    def __hash__(self):
        return self.id
