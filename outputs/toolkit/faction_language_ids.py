"""Disjoint name blocks with room for DE's derived creation/help lookups."""
def name_id(kind, civ, uid):
    base = 4000000 if kind == 'tech' else 1000000 + civ * 1000000
    return base + (uid // 1000) * 100000 + uid % 1000

def text_ids(kind, civ, uid):
    name = name_id(kind, civ, uid)
    return name, name + 1000, name + 21000
