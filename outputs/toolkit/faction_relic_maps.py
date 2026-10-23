"""Explicit Gaia holocrons (DE relics must be Gaia-owned). Placement is otherwise source-exact."""
import re

def repair_relics(body):
    def rewrite(match):
        block=match[0]
        if 'set_gaia_object_only' not in block:
            block=block.replace('{','{\n        set_gaia_object_only',1)
        return block
    result,count=re.subn(r'create_object\s+(?:SWGB_)?OBJ-HOLOCRON\s*\{[^{}]*\}',rewrite,body)
    assert count==2,('Unexpected source holocron branches',count)
    return result
