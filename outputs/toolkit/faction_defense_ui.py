"""Shared strings and free construction-layout switch hotkeys."""
from faction_language_ids import text_ids


def layout_hotkeys():
    return [dict(data_name=f'SWGB_LAYOUT_{mode}', name_string_id=898010+mode,
                 string_index_list=[1100010+mode],
                 defaults_list=[dict(name=preset, key='ZX'[mode]) for preset in
                                ('classic','definitive','high definition','left handed')])
            for mode in range(2)]


def defense_strings():
    result = {}
    for mode, title, help_text in (
        (0, 'Military construction layout', 'Free, repeatable layout switch. Show Shipyard (W), Mech Factory (T) and Jedi/Sith Temple (A) on the worker military page. Troop Center, Sentry Post, walls, gates and turrets are always there.'),
        (1, 'Advanced defense construction layout', 'Free, repeatable layout switch. Show Anti-Air Battery (W), Shield Generator (T) and Trip Mine (A) on the worker military page in place of Shipyard, Mech Factory and Jedi/Sith Temple. Use Military construction layout here to switch back. Original technology requirements still apply.')):
        result.update({898010+mode:title,899010+mode:title,919010+mode:help_text})
    for civ in (1,2):
        for uid in (213,215,335,336):
            result[text_ids('unit',civ,uid)[2]] = ('Build <b>Shield Generator<b> (<cost>). DE adaptation: while powered, projects bonus maximum health and regeneration onto your ground units and buildings, excluding walls. Requires an SWGB Factions map. This is not the original separate shield-health pool.')
        for uid in (5075,5081):
            result[text_ids('unit',civ,uid)[2]] = ('Build <b>Trip Mine<b> (<cost>). Visible proximity defense using native demolition behavior against ground targets. SWGB stealth and detector mechanics are not implemented.')
    return result
