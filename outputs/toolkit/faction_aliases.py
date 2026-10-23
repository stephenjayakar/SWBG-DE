"""Expected source-record substitutions for the isolated faction dataset."""
def source_aliases(rows,field='id'):
    result=[r for r in rows if not (r.get('civ')=='3' and r.get(field)=='550' and r.get('kind','unit')=='unit')]
    result.extend(dict(r,**{field:'550'}) for r in rows if r.get('civ')=='3' and r.get(field)=='556' and r.get('kind','unit')=='unit')
    return result
