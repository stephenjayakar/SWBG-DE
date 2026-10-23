# Empire and Rebel defensive construction

Release checkpoint: `v0.0.2-dev-defenses.2`, based on the installed defenses.1
payload. The unfinished AI work stays on `ai-port`. No game was launched; native
placement, combat and aura behavior still need an in-game check.

## Building defenses

Select a worker and open the military construction page. The following remain
available in either construction layout, subject to the original faction,
technology and tech-level requirements:

| Default key | Family |
| --- | --- |
| E | Light wall |
| R | Medium/heavy/shield wall |
| S | Sentry Post |
| D | Gate |
| Z | Ground turret and upgrades |
| C | Anti-air turret and upgrades |

DE has two worker pages with 13 building slots each (position 14 is the next-page
arrow, 15 cancel); the source roster has 29 buildings a human can build. Select the
**Command Center** and choose **Advanced defense construction layout** (bottom
row, second position; default X). This free, instant, repeatable research changes
three positions on the worker military page:

| Default key | Advanced defense layout | Military layout (default) |
| --- | --- | --- |
| W | Anti-Air Battery (missile turret) | Shipyard |
| T | Shield generator | Mech Factory |
| A | Trip mine | Jedi/Sith Temple |

To restore the three production-building buttons, select **Military construction
layout** at the Command Center (bottom row, first position; default Z). Existing
buildings keep operating and the AI can still construct them in either layout.
Troop Center (Q), Sentry Post (S) and the other worker slots stay unchanged.
Custom hotkeys can override these defaults. The fishing ship can build the sea
lookout at its second slot. The existing fortress remains available. The Advanced
Infantry Center is not on the menu: only an SWGB cheat and hidden AI research enable
it, and the AI builds it by ID.

The layout research moves train buttons (DE attribute 43, "Train Button"); the
hidden family sits at button 0, which DE never shows. It takes 1 second: with a
research time of 0 and no prerequisite, DE researched both layouts at game start, so
every game began in the defense layout and the Command Center offered no switch.
Until 2026-10-21 the switch also changed the interface kind between 10 and 11. DE has
no kind-11 page and shows such buildings on the military page, so Sentry Post, Shield
Generator and Trip Mine covered Troop Center, Mech Factory and Temple.

The worker builds the Shipyard through a foundation (unit 1696, like the Fortress and
Command Center foundations) that turns into the real Shipyard (unit 45) when it is
finished. DE never shows the native Dock IDs 45, 133, 47 and 51 in a build menu. The
AI still builds unit 45 directly. `check_build_menu.py` guards the layout;
`fix_build_menu.py` applies it to an assembled mod pair.

## Mechanics and differences from SWGB

- Ground turrets select ground targets; anti-air and missile turrets select
  aircraft. Explicit DE tasks replace source executable class behavior.
- Trip mines retain source damage, range and blast statistics, with DE's Petard
  classification for one-shot demolition behavior. Mines are **visible**: SWGB
  stealth and detector mechanics have not been recreated. Lookouts provide LOS.
- Shield generators use a **DE adaptation**, with temporary bonus maximum health
  and regeneration for the owner's ground units and buildings, excluding walls.
  It is not the source game's independent blue shield-health pool. Regeneration
  repairs actual health; native overlap and health changes when leaving the aura
  need testing. Base regeneration is 2 HP per game second, with source recharge
  resource modifiers. Source radius and power-range upgrades feed the controller.
- A completed generator stack must be in range of a completed Power Core or an
  ungarrisoned Power Droid. The controller reevaluates power each game second.
  Foundations and heads remain neutral so they cannot duplicate the stack aura.
  Enable DE's building/aura range indicator to inspect the placement radius.
- Shield activation requires one of the 20 **SWGB Factions** maps, which include
  `swgb_factions.xs`. Vanilla maps do not run this controller. Other defense menu
  changes and native combat tasks are in the Data mod.

## Validation and focused test

Offline checks cover 323,456 land/air target pairs, all 13,760 neutral shield aura
tasks, repeatable layout research costs/slots/effect fields, both factions'
construction reachability and cross-family slot collisions, serialization round
trip, byte-exact restoration to the prior DAT after undoing reviewed defense
fields, standalone XS syntax/types and 98 controller scenarios in a mocked host.
The installer verifies all 4,892 payload hashes and can roll back its four-file
patch. These checks do not execute the DE engine.

In a fresh SWGB Factions Savannah match:

1. Test both Command Center layout switches and all new worker buttons for Empire
   and Rebels. Place walls, gates, both lookout types, turrets, mines and shields.
2. Check gate passage and upgraded art. Attack ground targets with a ground turret
   and aircraft with AA/missile turrets; try the wrong target type as well.
3. Move enemy ground units across a mine; confirm one explosion and mine removal.
4. With cheats off, place a generator near a core. Check placement circle, bonus
   health and regeneration. Remove the core, move units out of range, overlap two
   generators, convert one, and save/reload. Confirm unfinished generators do not
   protect units. Compare behavior at different game speeds.

The reported Empire Tech Level 4 crash remains unresolved. Both friends must use
matching Data and Assets for this update. Installing the local Draft does not
update the published online mod.

Reproduce this narrow patch with `stage_defense_extension.py`, or add `--install`
to install after validation. It requires the exact defenses.1 installed baseline.
The full-build generators include the same defense mapping, UI and XS changes.
