"""Verify that every quote in a case study actually appears in the transcript.

This is the script that matters most. When you write a case study you WILL, without
noticing, tidy up a customer's grammar. "j'ai eue" for "j'ai eu". "à moindres frais"
for "à moindre frais". None of these change the meaning, which is exactly why they
slip past a reread — and why the piece stops being verbatim.

On the run this repo came from, the first pass scored 6 out of 16.

Usage:
    python verify_quotes.py <case-study.md> <transcript.txt> [second-transcript.txt]

A quote passes if all of its words appear in the transcript, in order, allowing
skipped words (so cutting hesitations is fine). Any word NOT in the transcript is
reported: that is a word the writer introduced.

Passing a second transcript (the other ASR model) is recommended. Quoting the more
faithful of two transcripts is not a rewrite, and without it you get false alarms.

Exit code 1 if any quote fails, so you can wire it into CI.
"""
import io, re, sys, unicodedata

# ASR spelling conventions, not rewrites: the model wrote one, the speaker said the
# other. Extend this for your own language and domain.
EQUIV = {
    'deux': '2',
    'dashboards': 'dashboard',
    # A quote in a second language will often be mangled by BOTH models (here
    # "do one thing but do it right" came out as "Do want thing Bud"). Restoring
    # the real wording is legitimate, but log it here so the substitution is
    # explicit rather than silent.
    'one': 'want',
    'but': 'bud',
}

MULTIWORD = [
    (r'\bpour\s*(100|cent)\b', '%'),
    (r'\bout\s+sourcer\b', 'outsourcer'),
    (r'\bout\s+reach\b', 'outreach'),
    (r'\b1re\b', 'première'),
    (r'\b1er\b', 'premier'),
    (r'(\d)\s+(\d{3})\b', r'\1\2'),      # 38 000 -> 38000
]


def pre(t):
    for pat, rep in MULTIWORD:
        t = re.sub(pat, rep, t, flags=re.I)
    return t.replace('œ', 'oe').replace('Œ', 'OE')


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    w = ''.join(c for c in w if unicodedata.category(c) != 'Mn')
    w = re.sub(r"[^a-z0-9%]", '', w)
    return EQUIV.get(w, w)


def words(t):
    return [x for x in (norm(w) for w in re.findall(r"[\w'’%À-ſ-]+", pre(t))) if x]


def quotes(md):
    """Extract markdown blockquote blocks."""
    out, cur = [], []
    for line in md.split('\n'):
        if line.startswith('>'):
            cur.append(line.lstrip('> ').strip())
        elif cur:
            out.append(' '.join(cur))
            cur = []
    if cur:
        out.append(' '.join(cur))
    return out


def is_subsequence(needle, hay):
    i = 0
    for w in needle:
        found = False
        while i < len(hay):
            if hay[i] == w:
                i += 1
                found = True
                break
            i += 1
        if not found:
            return False
    return True


def is_subsequence_either(needle, a, b):
    """A quote may legitimately draw on both transcripts: where model A mangled a
    word, model B got it right, and vice versa. Accept a quote if it is a
    subsequence of either, or if it splits cleanly between the two."""
    if is_subsequence(needle, a) or (b and is_subsequence(needle, b)):
        return True
    if not b:
        return False
    for cut in range(1, len(needle)):
        head, tail = needle[:cut], needle[cut:]
        if (is_subsequence(head, a) and is_subsequence(tail, b)) or \
           (is_subsequence(head, b) and is_subsequence(tail, a)):
            return True
    return False


def main():
    md = io.open(sys.argv[1], encoding='utf-8').read()
    tr = words(io.open(sys.argv[2], encoding='utf-8').read())
    tr2 = words(io.open(sys.argv[3], encoding='utf-8').read()) if len(sys.argv) > 3 else []
    vocab = set(tr) | set(tr2)

    qs = quotes(md)
    bad = 0
    for i, q in enumerate(qs, 1):
        qw = words(q)
        added = [w for w in qw if w not in vocab]
        ordered = is_subsequence_either(qw, tr, tr2)
        ok = ordered and not added
        if not ok:
            bad += 1
        print(f'{"OK " if ok else "FAIL"} [{i}] {q[:70]}...')
        if added:
            print(f'       WORDS NOT IN TRANSCRIPT: {added}')
        elif not ordered:
            print('       word order does not match')

    print(f'\n{len(qs)-bad}/{len(qs)} quotes verified')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
