"""Load the Classic AI's Hardest rules on DE's Extreme difficulty without a defconst alias.

The port made Extreme behave like the source's Hardest with
    #load-if-defined DIFFICULTY-EXTREME
    (defconst DIFFICULTY-HARDEST 1)
    #end-if
DE's preprocessor does not treat a defconst as a defined symbol. A 2026-10-21 Extreme match
(SWGB Factions Savannah) opened "AI Script Error ... SWGB Classic AI.per2, Line 19634:
ERR2005: Invalid identifier": `ce-unit-max` is only defined inside
`#load-if-defined DIFFICULTY-<level>` blocks, and with DIFFICULTY-HARDEST undefined no block
matched on Extreme. Every other DIFFICULTY-HARDEST block was also skipped (and every
`#load-if-not-defined DIFFICULTY-HARDEST` block loaded), so Extreme ran a mix of rule sets
instead of the Hardest ones. Hardest itself showed no error.

This transformation removes the alias and gives every DIFFICULTY-HARDEST conditional an
Extreme twin, using only directives DE supports (#load-if-defined, #else, #end-if, nested):
    #load-if-defined DIFFICULTY-HARDEST A [#else B] #end-if
 -> #load-if-defined DIFFICULTY-HARDEST A #else #load-if-defined DIFFICULTY-EXTREME A [#else B] #end-if #end-if
    #load-if-not-defined DIFFICULTY-HARDEST A [#else B] #end-if
 -> #load-if-defined DIFFICULTY-HARDEST [B] #else #load-if-defined DIFFICULTY-EXTREME [B] #else A #end-if #end-if
Hardest and Extreme are mutually exclusive, so exactly one copy loads: Hardest and Extreme
load the same rules, and every other difficulty loads what it loaded before.

Run from the repository root to apply it to an existing script tree in place (idempotent):
  python outputs/toolkit/classic_ai_extreme.py --root payload/SWBG-Data
"""
import argparse
from pathlib import Path

HARDEST, EXTREME = 'DIFFICULTY-HARDEST', 'DIFFICULTY-EXTREME'
ALIAS = ['#load-if-defined DIFFICULTY-EXTREME', '(defconst DIFFICULTY-HARDEST 1)', '#end-if']
MARKER = '; Extreme loads the Hardest rules through twin conditionals (classic_ai_extreme.py).'
PER = 'resources/_common/ai/SWGB Classic AI.per'


def parse(lines, i=0, top=True):
    """Lines -> nodes: str or [kind, symbol, then_nodes, else_nodes_or_None]."""
    nodes = []
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith('#load-if-defined ') or s.startswith('#load-if-not-defined '):
            kind, symbol = s.split()[0], s.split()[1]
            then, i, end = parse(lines, i + 1, False)
            other = None
            if end == '#else':
                other, i, end = parse(lines, i + 1, False)
            assert end == '#end-if', (kind, symbol, end)
            nodes.append([kind, symbol, then, other])
            i += 1
            continue
        if s in ('#else', '#end-if'):
            assert not top, f'unbalanced {s} at line {i + 1}'
            return nodes, i, s
        nodes.append(lines[i])
        i += 1
    assert top, 'missing #end-if'
    return nodes, i, None


def emit(nodes, out):
    for n in nodes:
        if isinstance(n, str):
            out.append(n)
            continue
        kind, symbol, then, other = n
        out.append(f'{kind} {symbol}')
        emit(then, out)
        if other is not None:
            out.append('#else')
            emit(other, out)
        out.append('#end-if')


def twin(nodes):
    result = []
    for n in nodes:
        if isinstance(n, str):
            result.append(n)
            continue
        kind, symbol, then, other = n
        then = twin(then)
        other = twin(other) if other is not None else None
        if symbol != HARDEST:
            result.append([kind, symbol, then, other])
            continue
        if kind == '#load-if-defined':
            hardest, rest = then, other
        else:  # not-defined: the else branch is the Hardest one
            hardest, rest = (other or []), then
        if rest:
            inner = ['#load-if-defined', EXTREME, list(hardest), rest]
        else:
            inner = ['#load-if-defined', EXTREME, list(hardest), None]
        result.append(['#load-if-defined', HARDEST, hardest, [inner]])
    return result


def rewrite(text):
    """(text, changed). Idempotent: an already twinned script is returned unchanged."""
    newline = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(newline)
    if MARKER in lines:
        return text, False
    for k in range(len(lines) - 2):
        if [l.strip() for l in lines[k:k + 3]] == ALIAS:
            del lines[k:k + 3]
            lines.insert(k, MARKER)
            break
    else:
        raise SystemExit('Extreme alias block not found')
    nodes, _, _ = parse(lines)
    out = []
    emit(twin(nodes), out)
    return newline.join(out), True


def untwin(text):
    """Inverse view for checks written against the single-copy script: collapse every
    Hardest/Extreme twin back to one DIFFICULTY-HARDEST conditional and restore the alias,
    so rule counts and the offline (alias-aware) preprocessors see the logical script.
    check_classic_extreme.py proves both forms load the same rules for every difficulty."""
    newline = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(newline)
    if MARKER not in lines:
        return text
    k = lines.index(MARKER)
    lines[k:k + 1] = ALIAS

    def collapse(nodes):
        result = []
        for n in nodes:
            if isinstance(n, str):
                result.append(n)
                continue
            kind, symbol, then, other = n
            then = collapse(then)
            other = collapse(other) if other is not None else None
            twinned = (kind, symbol) == ('#load-if-defined', HARDEST) and other and len(other) == 1 \
                and not isinstance(other[0], str) and other[0][:2] == ['#load-if-defined', EXTREME] \
                and collapse(other[0][2]) == then
            if twinned:
                result.append([kind, symbol, then, other[0][3]])
                continue
            result.append([kind, symbol, then, other])
        return result

    nodes, _, _ = parse(lines)
    out = []
    emit(collapse(nodes), out)
    return newline.join(out)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--root', type=Path, default=Path('payload/SWBG-Data'))
    args = cli.parse_args()
    path = args.root / PER
    with path.open(encoding='utf-8', newline='') as handle:
        raw = handle.read()
    text, changed = rewrite(raw)
    if changed:
        with path.open('w', encoding='utf-8', newline='') as handle:
            handle.write(text)
    print(PER, 'changed' if changed else 'unchanged', f'{raw.count(chr(10))} -> {text.count(chr(10))} lines')


if __name__ == '__main__':
    main()
