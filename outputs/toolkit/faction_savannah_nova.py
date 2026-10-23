"""Reserve Savannah's primary Nova deposit before competing object placement.

The replay regression had ordinary resources and no Nova within 78 tiles of
player one's command center. This patch preserves seven primary crystals per
player, placing their group inside the already-protected starting clearing.
It is a placement repair candidate until verified with native map generation.
"""
import re

MARKER='/* Protected primary Nova: place before competing object groups. */'

def repair_savannah_nova(body):
    if MARKER in body:return body
    blocks=list(re.finditer(r'create_object\s+(?:SWGB_)?OBJ-NOVA\s*\{[^{}]*\}',body))
    primary=[m for m in blocks if 'set_place_for_every_player' in m[0]]
    assert len(primary)==3,('Unexpected Savannah per-player Nova blocks',len(primary))
    first=primary[0]
    assert re.search(r'number_of_objects\s+7\b',first[0]),'Unexpected primary Nova count'
    prefix='SWGB_' if 'SWGB_OBJ-NOVA' in first[0] else ''
    block=f'''{MARKER}
create_object {prefix}OBJ-NOVA
{{
    number_of_groups 1
    number_of_objects 7
    group_variance 0
    group_placement_radius 2
    set_tight_grouping
    set_gaia_object_only
    set_place_for_every_player
    terrain_to_place_on {prefix}GRASS2
    min_distance_to_players 12
    max_distance_to_players 16
    min_distance_group_placement 1
}}
'''
    body=body[:first.start()]+body[first.end():]
    assert body.count('<OBJECTS_GENERATION>')==1
    return body.replace('<OBJECTS_GENERATION>','<OBJECTS_GENERATION>\n\n'+block,1)
