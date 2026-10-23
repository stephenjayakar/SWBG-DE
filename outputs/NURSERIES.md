# Animal Nurseries

Use a fresh match with the matching faction Data and Assets mods, on an **SWGB
Factions** map. These maps load the nursery food script.

1. Capture a herdable animal, such as a nerf or bantha, by bringing your unit near
   it. It must become yours and be selectable.
2. Finish building an **Animal Nursery**.
3. Select the animal, hold **Alt**, and **right-click the nursery**. This explicitly
   requests garrisoning. Ordinary right-click depends on your garrison setting.
4. Select the nursery to see its occupants. Use **Ungarrison** to release them.

Each nursery has **10 animal spaces**. Wild hunting animals and food eggs do not
have the nursery garrison ability. Workers do not carry animals inside.

Food is automatic while an animal is inside. The base source rate is **0.13 food
per animal per game second**: one animal produces 7.8 food per game minute; ten
produce 78. The displayed stockpile rounds, so a single animal's income is not
visible every second. Stimulants, Genetics, Cloning, and Efficient Buildings apply
their source multipliers. A Power Core does not multiply the animal food trickle.
Game speed changes how quickly game time passes; pausing stops income.

## This follow-up

- Recognizes all eight nursery variants (319–322 and 3550–3553) in the income
  script, including Rebel Evacuation Protocols replacements. The generator follows
  the source upgrade graph so these technology variants cannot be overlooked.
- Checks all 72 playable/Gaia animal records covering 24 garrisonable species,
  nursery capacity/masks, and source income/upgrade values against the current DAT.
- **SWGB Classic AI** now gives individual orders to idle captured animals.
  It chooses the nearest completed Nursery; when that Nursery is full, it tries
  the next nearest. With no completed Nursery, animals move toward the nearest
  Command Center or Food Processing Center. Busy and already housed animals are
  left alone. This replaces the older bulk-garrison requests. Human animals and
  the previous land AI (removed in October 2026) remained unchanged.
- Adds these controls to all eight nursery build tooltips.
- Repairs the shared Astromech script's stale aircraft-class lookup.

## Focused in-game check

With cheats and other food gathering off, garrison ten animals in an unupgraded
nursery and compare food across 60 **game seconds**: expect about 78 food, allowing
for the one-second update/display boundary. Ungarrison them and verify income
stops. Repeat after age advancement, then with nursery research and Rebel
Evacuation Protocols. For the AI,
select **SWGB Classic AI**, Hard, normal resources; after it builds a nursery,
check that its captured animals move inside.

The earlier data/income follow-up passed 338 nursery and package checks. The
individual-command follow-up adds 1,553 original-bytecode comparisons, 964
controller host cases and a fresh 81-configuration Classic AI parser matrix.
The game has not been launched for this update. Static data validation and script
checks do not prove command execution, save/load behavior, income timing, or
multiplayer synchronization. A 100% behavioral match remains unverified.

For the new AI check, use **SWGB Classic AI**, not the default AI. Watch one
captured animal approach a completed Nursery and enter it. Test two Nurseries
with the closer one full, and test capture before any Nursery has been built.
The implementation polls once per game second; source action scheduling and
equal-distance object ordering may still differ. The original also attempts the
second Nursery without rechecking its capacity; that behavior is retained.

Reference: [SWGB AI scripting differences, including the default animal-garrison
setting](https://airef.github.io/resources/articles/swgb-scripting.html).
