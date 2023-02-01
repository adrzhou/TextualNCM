from _track import Track
from pyncm import apis, GetCurrentSession
from concurrent.futures import ThreadPoolExecutor


class Downloader:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    def shutdown(self):
        self.executor.shutdown(wait=True)

    def submit(self, track: Track):
        if not track.local:
            return self.executor.submit(download, track)


def download(track: Track):
    track_id = [track.id]
    audio = apis.track.GetTrackAudioV1(track_id, level='exhigh')
    audio = audio.get("data", [{"url": ""}])[0]
    if not audio['url']:
        return
    response = GetCurrentSession().get(audio['url'], stream=True)
    track.size = int(response.headers.get("content-length"))
    dst = rf'downloads/{track_id[0]}.mp3'
    with open(dst, 'wb') as fp:
        for chunk in response.iter_content(128 * 2 ** 10):
            fp.write(chunk)
            track.xfered += len(chunk)
    track.local = True
