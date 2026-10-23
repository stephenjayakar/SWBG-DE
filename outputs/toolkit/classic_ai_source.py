"""Lossless source reader for the installed Computer Classic AI.

Includes random-load alternatives in the dependency graph. No game executable is run.
"""
from pathlib import Path
import hashlib
import re

SOURCE = Path('E:/GOG Games/Star Wars - Galactic Battlegrounds/Game/AI')
FACTIONS = set('EMPIRE REBEL GUNGANS NABOO FEDERATION WOOKIEES REPUBLIC CONFEDERACY CONFEDERATE ZANN GEONOSIANS FIRSTORDER RESISTANCE IMPERIALREMNANT NEWREPUBLIC BLACKSUN'.split())


def clean(text):
    return re.sub(r'"[^"\n]*"|;[^\n]*', lambda m: m[0] if m[0].startswith('"') else '', text)


def parse(text):
    tokens = re.findall(r'#[^\n]*|"[^"\n]*"|[()]|[^\s()]+', clean(text))
    root, stack = [], []
    current = root
    for token in tokens:
        if token == '(':
            node = []
            current.append(node)
            stack.append(current)
            current = node
        elif token == ')':
            assert stack, 'Extra closing parenthesis'
            current = stack.pop()
        else:
            current.append(token.strip())
    assert not stack, 'Unclosed expression'
    return root


def render(node):
    if isinstance(node, str):
        return node
    if node[0] == 'defrule':
        return '(defrule\n' + '\n'.join('  '+render(x) for x in node[1:])+'\n)'
    text='('+' '.join(render(x) for x in node)+')'
    if len(text)>180 and any(isinstance(x,list) for x in node):
        return '('+node[0]+'\n'+'\n'.join('  '+render(x).replace('\n','\n  ') for x in node[1:])+'\n)'
    return text


def resolve(name):
    path = SOURCE / (name.strip('"').lstrip('/')+'.per')
    if not path.exists() and path.name.startswith('dip-'):
        path = SOURCE / 'Computer Classic' / ('CC_'+path.name)
    assert path.resolve().is_relative_to(SOURCE.resolve())
    return path


def graph():
    files, randoms = {}, {}
    def visit(path, ancestors=()):
        assert path not in ancestors, 'Include cycle'
        raw = path.read_bytes()
        files[path.relative_to(SOURCE).as_posix()] = hashlib.sha256(raw).hexdigest()
        nodes = []
        for node in parse(raw.decode('cp1252')):
            if isinstance(node, list) and node[0] == 'load':
                nodes.extend(visit(resolve(node[1]), ancestors+(path,)))
            elif isinstance(node, list) and node[0] == 'load-random':
                for name in node[2::2]:
                    randoms[name.strip('"')] = visit(resolve(name), ancestors+(path,))
                nodes.append(node)
            else:
                nodes.append(node)
        return nodes
    root = visit(SOURCE/'Computer Classic.per')
    return root, randoms, files


def specialize(nodes, faction):
    """Resolve only faction conditions; leave match settings to DE's loader."""
    out, stack, active = [], [], True
    for node in nodes:
        if isinstance(node, str) and node.startswith('#load-if'):
            directive, symbol = node.split()
            known = symbol in FACTIONS
            condition = (symbol == faction) if known else True
            if known and directive == '#load-if-not-defined':
                condition = not condition
            stack.append((active, condition, known))
            if active and not known:
                out.append(node)
            active = active and condition
        elif node == '#else':
            parent, condition, known = stack[-1]
            if known:
                active = parent and not condition
            elif parent:
                out.append(node)
        elif node == '#end-if':
            parent, condition, known = stack.pop()
            if parent and not known:
                out.append(node)
            active = parent
        elif active:
            out.append(node)
    assert not stack
    return out


def atoms(nodes):
    for node in nodes:
        if isinstance(node, list):
            yield from atoms(node)
        else:
            yield node


if __name__ == '__main__':
    import json
    root, randoms, files = graph()
    path = Path('work/original-ai')
    path.mkdir(parents=True, exist_ok=True)
    for faction in ('EMPIRE', 'REBEL'):
        nodes = specialize(root, faction)
        for values in randoms.values():
            nodes.extend(specialize(values, faction))
        (path/(faction.lower()+'-source.per')).write_text('\n'.join(map(render,nodes)))
        defined = {n[1].lower() for n in nodes if isinstance(n,list) and n[0]=='defconst'}
        builtins = sorted({a.lower() for a in atoms(nodes) if a.lower().startswith(('rt-','ut-','unit-','boat-','bldg-','gaia-','sn-')) and a.lower() not in defined})
        (path/(faction.lower()+'-symbols.json')).write_text(json.dumps(builtins,indent=2))
    print('Source files:', len(files))
