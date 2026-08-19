"""Fetch a signed Vimeo playlist.json and reassemble its audio to .m4a.

Usage:
    python grab.py <slug> <playlist_url> [referer]

Where <playlist_url> is the signed .../playlist.json request the Vimeo player
made while the video was playing. Get it from your browser devtools network tab
(filter on "playlist.json"), or with Chrome DevTools MCP.

Signed URLs expire after roughly an hour. Grab them and use them promptly.
"""
import json, os, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    slug, url = sys.argv[1], sys.argv[2]
    referer = sys.argv[3] if len(sys.argv) > 3 else ''

    pl_path = os.path.join(HERE, f'pl_{slug}.json')
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': referer,
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    d['_playlist_url'] = url
    d['_referer'] = referer
    json.dump(d, open(pl_path, 'w'))

    subprocess.run([sys.executable, os.path.join(HERE, 'vimeo_audio.py'),
                    pl_path, os.path.join(HERE, f'{slug}.m4a')], check=True)
    os.remove(pl_path)


if __name__ == '__main__':
    main()
