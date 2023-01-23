import logging
from pyncm import apis, GetCurrentSession
from flask import Flask

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.logger.disabled = True
log.disabled = True


@app.route('/track/<int:track_id>')
def stream_track(track_id):
    audio = apis.track.GetTrackAudioV1([track_id], level='exhigh')
    audio = audio.get("data", [{"url": ""}])[0]
    response = GetCurrentSession().get(audio['url'], stream=True)

    def stream():
        for chunk in response.iter_content(128 * 2 ** 10):
            yield chunk
    return stream(), response.status_code
