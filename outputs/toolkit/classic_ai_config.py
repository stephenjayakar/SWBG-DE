"""Resolve one actual loader path, including constants defined in loaded files.

Used for offline validation only; the game still performs its own random draw.
"""
from pathlib import Path
from classic_ai_source import parse, render


def resolve_configuration(root, symbols, personality):
    root=Path(root).resolve()
    symbols=set(symbols)
    draws=[]
    loaded=[]
    def visit(path, ancestors=()):
        path=path.resolve()
        assert path.is_relative_to(root) and path not in ancestors
        loaded.append(path.relative_to(root).as_posix())
        out=[];stack=[];active=True
        for node in parse(path.read_text()):
            if isinstance(node,str) and node.startswith('#load-if'):
                directive,symbol=node.split()
                condition=symbol in symbols
                if directive=='#load-if-not-defined':condition=not condition
                stack.append((active,condition));active=active and condition
            elif node=='#else':
                parent,condition=stack[-1];active=parent and not condition
            elif node=='#end-if':active=stack.pop()[0]
            elif active:
                if isinstance(node,list) and node[0] in ('load','load-random'):
                    if node[0]=='load':name=node[1].strip('"')
                    else:
                        options=[(int(w),n.strip('"')) for w,n in zip(node[1::2],node[2::2])]
                        matches=[n for w,n in options if w>0 and n.endswith('dip-'+personality)]
                        # Wonder modes intentionally have only the feeder branch.
                        if not matches:
                            assert len(options)==1 and options[0][0]>0
                            matches=[options[0][1]]
                        assert len(matches)==1
                        name=matches[0];draws.append(dict(options=options,selected=name))
                    out.extend(visit(root/(name+'.per'),ancestors+(path,)))
                else:
                    if isinstance(node,list) and node[0]=='defconst':symbols.add(node[1])
                    out.append(render(node))
        assert not stack
        return out
    text='\n'.join(visit(root/'SWGB Classic AI.per'))+'\n'
    return text,dict(draws=draws,loaded=loaded)
