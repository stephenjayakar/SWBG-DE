# Source special-building resource generation

The installed `Data/resgen.txt` identifies eight consumers of resources 215–218. These are special map buildings, not Empire or Rebel production buildings. None appears in the current 20 map object inventories. Automatic age technologies update their rates even in games without these buildings; those technology effects alone do not imply ordinary buildings should generate income.

| Source ID | Building record | Output | Rate resource | Source work-rate multiplier |
|---|---|---|---|---|
| 2554 | Food storage | Food | 218 | 1 |
| 4072 | Fish processor | Food | 218 | 1 |
| 4076 | Jedi ruins | Nova | 216 | 1 |
| 4077 | Small Jedi ruins | Nova | 215 | 1 |
| 4078 | Kessel mine | Ore | 217 | 1 |
| 4083 | Moisture vaporator | Food | 218 | 0.5 |
| 4084 | Moisture vaporator | Food | 218 | 0.75 |
| 4519 | Jedi ruins variant | Nova | 216 | 1 |

The [Expanding Fronts implementation](https://github.com/rva2895/efpatch/blob/f2773079b3deb53737d86165351a7279fa71b5e9/cheatdll/resgenbldgs.cpp) reads this external list and hooks the building update at source address 0x5553C6. For loaded versions >= 6 it credits the building owner `controlResource / 60 * master.work_rate` per call through `TRIBE_Player__add_attribute_num(..., 1)`. Earlier versions omit the work-rate multiplier and directly update the resource stockpile. The original executable's preceding gate at 0x55537E–0x5553C6 runs once after at least one observed game second; it advances the stored timestamp by whole seconds but does not multiply the payout by skipped seconds.

The imported DAT cannot implement this list-driven code by itself. No adapter is installed for these buildings. If maps or scenario scope expands to include them, implement their source generation, ownership changes and earned-resource statistics, with engine tests. Do not award these resources globally or to unrelated buildings. The multiplier is the source master work rate, not the quarter-speed runtime rate used for unpowered production.

Reproduce the inventory with `python outputs/toolkit/audit_faction_resource_producers.py`; its JSON report records the installed list hash and current roster/map intersections. This is source-code and data evidence, not a running-game verification.
