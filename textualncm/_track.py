import sys
from weakref import WeakValueDictionary
from pathlib import Path
from rich.progress import Progress, BarColumn


if getattr(sys, "frozen", False):
    datadir = Path(sys.executable).parent
else:
    datadir = Path(__file__).parent
downloads = datadir.joinpath('downloads')
if not downloads.exists():
    downloads.mkdir()


class Track:
    _initialized = False
    _registry = WeakValueDictionary()

    # The '_locals' variable does not need to be updated during runtime
    # It only stores the ids of local tracks at start time
    _locals = [int(path.stem) for path in downloads.iterdir()]

    def __init__(self, name, _id, artists, album, album_id):
        # Prevent initialization on created instance
        if self._initialized:
            return

        self.name: str = name
        self.id: int = _id
        self.artist_ids: dict[int, str] = artists
        self.album: str = album
        self.album_id: int = album_id
        self.local: bool = _id in self._locals
        self.liked: bool = False
        self.downloading: bool = False
        self.length: int = 0
        self.size: int = 0
        self.xfered: int = 0
        self._progress: Progress = Progress(BarColumn(), auto_refresh=False)
        self.task = self._progress.add_task('', total=None)
        self._initialized = True

    def __new__(cls, name, _id, artists, album, album_id):
        if _id in cls._registry:
            return cls._registry[_id]
        instance = super().__new__(cls)
        cls._registry[_id] = instance
        return instance

    def __hash__(self):
        return self.id

    @property
    def progress(self):
        if self.local:
            return ':white_heavy_check_mark:'
        if self.downloading:
            with self._progress as p:
                p.update(self.task, total=self.size, completed=self.xfered)
                return p
        return ''

    @property
    def artists(self):
        return ', '.join(self.artist_ids.values())

    class EmptyTrack:
        # The player receives this placeholder object at startup
        name: str = ''
        artists: str = ''
        local: bool = False
        liked: bool = False
        length: int = 0

        def __bool__(self):
            return False
