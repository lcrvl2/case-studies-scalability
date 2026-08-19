"""Transcribe an audio file with Deepgram, twice, using two different models.

Two independent ASR models make different mistakes. Where they agree, the word is
almost certainly right. Where they disagree, a human decides. That disagreement is
the error detector — see compare.py.

    nova-2        fast (~6s), good punctuation, speaker diarization
    whisper-large slower (~75s), noticeably better on proper nouns

Usage:
    python transcribe.py <audio> <out-prefix> [lang]

Writes <out-prefix>_nova.txt and <out-prefix>_whisper.txt.
Set DEEPGRAM_API_KEY in the environment, or put it in a .env file next to this script.

lang defaults to "fr". Pass "auto" to let Deepgram detect it — worth doing when you
are not certain, since forcing the wrong language returns near-empty output.
"""
import io, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def api_key():
    k = os.environ.get('DEEPGRAM_API_KEY') or os.environ.get('DEEPGRAM_API_TOKEN')
    if k:
        return k.strip()
    for name in ('.env', '../.env'):
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            for line in io.open(p, encoding='utf-8', errors='ignore'):
                if line.split('=')[0].strip() in ('DEEPGRAM_API_KEY', 'DEEPGRAM_API_TOKEN'):
                    return line.split('=', 1)[1].strip()
    raise SystemExit('Set DEEPGRAM_API_KEY (env var or .env file)')


def listen(audio, model, lang, diarize):
    params = [f'model={model}', 'punctuate=true', 'smart_format=true']
    params.append('detect_language=true' if lang == 'auto' else f'language={lang}')
    if diarize:
        params += ['paragraphs=true', 'diarize=true']
    url = 'https://api.deepgram.com/v1/listen?' + '&'.join(params)

    req = urllib.request.Request(url, data=open(audio, 'rb').read(), headers={
        'Authorization': 'Token ' + api_key(),
        'Content-Type': 'audio/mp4',
    })
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.load(r)

    ch = d['results']['channels'][0]
    alt = ch['alternatives'][0]
    text = (alt.get('paragraphs', {}) or {}).get('transcript') or alt['transcript']
    return text, alt.get('confidence', 0), ch.get('detected_language', lang), d


def main():
    audio, prefix = sys.argv[1], sys.argv[2]
    lang = sys.argv[3] if len(sys.argv) > 3 else 'fr'

    for model, suffix, diarize in (('nova-2', 'nova', True),
                                   ('whisper-large', 'whisper', False)):
        text, conf, detected, raw = listen(audio, model, lang, diarize)
        io.open(f'{prefix}_{suffix}.txt', 'w', encoding='utf-8').write(text)
        if diarize:  # keep word-level confidence from nova-2, used to arbitrate
            io.open(f'{prefix}_{suffix}.json', 'w', encoding='utf-8').write(
                json.dumps(raw, ensure_ascii=False))
        print(f'  {model:14s} conf={conf:.3f} lang={detected} chars={len(text)}')


if __name__ == '__main__':
    main()
