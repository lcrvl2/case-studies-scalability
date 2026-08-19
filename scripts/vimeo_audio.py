"""Reassemble Vimeo DASH audio from a signed playlist.json into an .m4a file.

Vimeo videos embedded on a site are often domain-restricted: yt-dlp returns 401,
the /config endpoint is CORS-blocked, and there is usually no subtitle track.
What does work: let the browser play the video, grab the signed playlist.json URL
from the network log, and reassemble the audio segments yourself.

The playlist gives a base64 init segment plus N media segments whose URLs are
relative to <playlist dir>/../../../../../range/prot/. Concatenating init +
segments yields a valid fragmented MP4.

Usage: python vimeo_audio.py <playlist.json> <out.m4a>

The JSON must contain a "_playlist_url" key holding the URL it was fetched from
(grab.py adds it for you).
"""
import base64, json, sys, urllib.parse, urllib.request

UA = 'Mozilla/5.0'


def resolve(playlist_url, base_url, seg_url):
    d = playlist_url.rsplit('/', 1)[0] + '/'
    return urllib.parse.urljoin(urllib.parse.urljoin(d, base_url), seg_url)


def fetch(url, referer, tries=3):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': UA,
                'Referer': referer,
            })
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            last = e
    raise last


def main():
    pl_path, out_path = sys.argv[1], sys.argv[2]
    pl = json.load(open(pl_path))
    pl_url = pl['_playlist_url']
    referer = pl.get('_referer', '')

    # prefer AAC (mp4a) over opus: broader ffmpeg / ASR compatibility
    audios = pl.get('audio', [])
    if not audios:
        raise SystemExit('no audio track in playlist')
    aac = [a for a in audios if 'mp4a' in (a.get('codecs') or '')]
    track = max(aac or audios, key=lambda a: a.get('bitrate', 0))

    tbase = urllib.parse.urljoin(pl['base_url'], track.get('base_url', ''))
    data = bytearray(base64.b64decode(track['init_segment']))
    segs = track['segments']
    for i, s in enumerate(segs, 1):
        data += fetch(resolve(pl_url, tbase, s['url']), referer)
        print(f'  segment {i}/{len(segs)}', end='\r', flush=True)
    open(out_path, 'wb').write(data)
    print(f'\n  wrote {out_path} ({len(data)/1e6:.2f} MB, '
          f'{track.get("duration", 0):.0f}s, {track.get("codecs")})')


if __name__ == '__main__':
    main()
