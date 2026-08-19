"""Compare two transcripts of the same audio and surface only the disagreements.

Two independent ASR models fail differently. Where they agree, the word is reliable.
Where they diverge, a human decides. This turns "relisten to 19 minutes of audio"
into "arbitrate N specific words".

Usage:
    python compare.py <a.txt> <b.txt> [out.md]

Prints an agreement rate and writes a table of every divergence with its context.

What this catches, and what it does not:
  CATCHES  one model mangling a name, a whole clause dropped by one model,
           a number heard differently
  MISSES   both models making the SAME mistake. That happens on proper nouns
           more often than you would expect. Verify names externally.
"""
import difflib, io, re, sys, unicodedata


def strip_speakers(t):
    return re.sub(r'^Speaker \d+:\s*', '', t, flags=re.M)


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    w = ''.join(c for c in w if unicodedata.category(c) != 'Mn')
    return re.sub(r"[^a-z0-9%]", '', w)


def words(t):
    return [w for w in re.findall(r"[\w'’%À-ſ-]+", t) if w.strip()]


def main():
    a_txt = strip_speakers(io.open(sys.argv[1], encoding='utf-8').read())
    b_txt = strip_speakers(io.open(sys.argv[2], encoding='utf-8').read())
    out = sys.argv[3] if len(sys.argv) > 3 else None

    a, b = words(a_txt), words(b_txt)
    sm = difflib.SequenceMatcher(None, [norm(x) for x in a], [norm(x) for x in b])

    diffs, agreed = [], 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            agreed += i2 - i1
        else:
            diffs.append({
                'ctx': ' '.join(a[max(0, i1 - 6):i1]),
                'a': ' '.join(a[i1:i2]),
                'b': ' '.join(b[j1:j2]),
            })

    total = max(len(a), len(b))
    rate = agreed / total if total else 0
    print(f'{len(a)} vs {len(b)} words — {rate*100:.1f}% agreement, {len(diffs)} divergences')

    lines = [f'# {sys.argv[1]} vs {sys.argv[2]}', '',
             f'{rate*100:.1f}% agreement ({agreed} identical words), {len(diffs)} divergences', '',
             '| context | A | B |', '|---|---|---|']
    for d in diffs:
        if not d['a'].strip() and not d['b'].strip():
            continue
        ctx = d['ctx'].replace('|', '/')[-60:]
        lines.append(f'| …{ctx} | **{d["a"] or "—"}** | {d["b"] or "—"} |')

    if out:
        io.open(out, 'w', encoding='utf-8').write('\n'.join(lines))
        print(f'wrote {out}')
    else:
        print('\n'.join(lines[4:]))


if __name__ == '__main__':
    main()
