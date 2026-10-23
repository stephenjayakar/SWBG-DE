"""Source combat-object UnitAI type selection; stable type IDs in catalog.TYPES."""
NONE_CLASSES=frozenset((3,20,22,23,24,25,26,27,29,30,31,41,42))
SIEGE_CLASSES=frozenset((11,16,32,33,34,35,36,37,40))
BUILDING_CLASSES=frozenset((6,7,8,9,10,18))


def unit_ai_type(source_class,volley_missile_id=-1):
    if source_class in NONE_CLASSES:return -1
    if source_class==1:return 0
    if source_class in (4,46):return 1
    if source_class==60:return 2
    if source_class==5:return 3
    if source_class==58:return 4
    if source_class==54:return 5
    if source_class in (50,51):return 6
    if source_class in (12,45):return 7
    if source_class in (17,59):return 8
    if source_class==14:return 9
    if source_class in (21,28):return 11
    if source_class in SIEGE_CLASSES:return 13
    if source_class in BUILDING_CLASSES:
        return 12 if source_class in (9,10) or volley_missile_id>=0 else 14
    return 10
