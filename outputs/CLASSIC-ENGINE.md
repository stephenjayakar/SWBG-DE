# Classic AI engine port: aircraft selection and targeting

The aircraft and combat-targeting layers are development checkpoints, not yet
connected to live orders. The individual nursery controller below is a separate
runtime follow-up to `51956db` (`v0.0.2-dev-classic-ai.2`). The full AI goal remains
open. No game was launched.

## Active attack-group continuation (development)

`classic_active_attack.xs` connects the post-selection behavior of
`taskActiveGroupAttack` (`0x5A3C40`) to the existing per-player group store.
The source accepts ground, boat and air attack group kinds 100/102/108;
when its attack setting is zero, flag 3 must be present. Selection may set
flag 6 to defer the group, with separate air/ground continuation IDs.

With no selected record, elapsed time below 5000 milliseconds changes only
the action to 1. At or above that boundary the source optionally saves its
home position, sets action 18 and its timestamp, invokes taskGroup, then
marks the group in use, clears its target and restores its home destination.
The elapsed calculation preserves the signed interpretation of wrapping
32-bit subtraction before clamping negatives to zero.

A selected record sets flag 5. Ground groups needing transport invoke task
12 with force zero **before** storing action 11 and the target record.
Other selected groups store action 2 and the record **before** task 2 with
force one. The development controller exposes each task as a synchronous
request; `classicActiveTaskComplete` performs the remaining mutations after
the caller delivers it. An overlapping begin/selection is rejected while a
task request is outstanding. This does not deliver a native game command.

The caller supplies the original memory-record type and byte coordinates,
not an unrestricted live position of a hidden enemy. Target presence is
separate from its ID. The caller also loads/persists the group's position,
home and saved-home vectors, timestamps and deferred-selection state. The
single scratch context must not be interleaved between players or groups.

`check_classic_active_attack.py` executes the complete original wrapper,
original flag tests and group constructor, with target selection and
taskGroup as explicit callback fixtures. It compares final states and each
state visible at a task callback against the composed XS/group-store host.
All 3024 cases pass: 1458 selection calls, 651 task callbacks, 702 deferred
searches and 1566 early exits. Cases include ground/boat/air and invalid
group kinds, signed flag words, exact timeout boundaries and clock wrap,
non-boolean transport results, signed record types and present ID -1.
The report is `work/classic-engine/active-attack-validation.json` and XS
lint is clean. Actual transport-group availability, selection/path geometry,
native task delivery, scheduling and persistence remain unconnected.

The original scripts rely on hardcoded engine behavior. Translating their rules
does not reproduce that behavior in DE. The next controller is being built from
the original routines, with differential checks rather than guessed thresholds.

## Verified source decisions

`classic_engine_oracle.py` loads the user's local, hash-pinned executable into
Unicorn 2.1.4. It executes isolated x86 routines with explicit world fixtures.
It does not execute an installed game process, invoke OS APIs, modify game files,
or put executable bytes into a mod archive.

Source SHA-256:
`d64e7f0ecc546c3bd833c5c6a7bc97b75ee74940d89b1cb22349b0ace0f3fc58`.
Function names and structures come from the local
[EF patch source](https://github.com/rva2895/efpatch), commit
`f2773079b3deb53737d86165351a7279fa71b5e9`.

| Routine | Address | Verified decisions |
| --- | --- | --- |
| `TribeTacticalAIModule::addObject` | `0x0059FA80` | Separate ground, air, boat and worker lists; source class/flag precedence. |
| `VictoryConditionRuleSystem` constructor | `0x00596D10` | Source defaults, including 75% aircraft attack, 4/10 automatic air-group sizes, **zero** automatic air attack groups, 100% animal garrisoning, and formation distance 20. |
| `TribeTacticalAIModule::setStrategicNumber` | `0x005A5730` | Difficulty scaling of aircraft percentages, positive minimum one, scaling bypass. |
| `TribeTacticalAIModule::attackNow` | `0x005AE520` | Separate category percentages and upward rounding with the source float constant. Spatial grouping is stubbed in this specific fixture. |
| `BDifferentiator::groupAIUnits` | `0x004506F0` | Actual clustering, first-on-tie choice, input ordering, zone separation, 40-candidate window and early termination. World position/zone queries are fixtures. |

Important details:

- Ground soldier classes are 32–36, 44, 47 and 49–57. Aircraft use 43, 48,
  59 and 62–64, subject to source object flags. Air transports (59) belong to
  the aircraft inventory but are excluded from `numberUngroupedAir` attacks.
- Air percentages are multiplied by 1, 1, 0.75, 0.5 and 0.25 on Hardest,
  Hard, Moderate, Easy and Easiest, then truncated and clamped to at least one
  when originally positive. Hard multiplayer changes some other settings but
  **does not** change these percentages. Zero/negative values remain unchanged.
- Each category's requested count rounds upward. Spatial grouping examines only
  its first 40 eligible candidates. It selects the densest remaining cluster;
  ties select the first candidate. The leader comes first, followed by neighbors
  in input order. Attack dispatch then truncates the selected groups to the budget.
- The grouping stop condition uses the entire available count, even when it
  exceeds 40. That original quirk is retained in the reference implementation.
- Aircraft automatic group count defaults to **0**, not the unverified 40 stated
  in an external guide. Classic's active include graph does not set the three
  air-group size/count settings; the unused aggressive script does.

## Code and verification

- `outputs/toolkit/classic_engine_oracle.py`: isolated original-bytecode oracle.
- `outputs/toolkit/classic_air_model.py`: source-derived reference decisions.
- `outputs/toolkit/check_classic_engine.py`: **3,261 differential checks** against
  the original routines, including deterministic layouts and boundary cases.
- `outputs/toolkit/classic_air_planner.xs`: corresponding pure XS selection layer.
- `outputs/toolkit/check_classic_air_planner.py`: XS checker plus **4,059 cases**
  executing that algorithm in a small C++ host with explicit builtin adapters.

The C++ host translates only XS loop syntax. It is **not** a DE XS VM. Tests
check the planner's decisions and repeated array reuse, not engine execution or
synchronization. Floating-point behavior at arbitrary boundary positions still
requires verification in DE. No tests claim full-game behavioral parity.

Run `check_classic_engine.py`, then `check_classic_air_planner.py` from the
workspace. Reports are `work/classic-engine/validation.json` and
`work/classic-engine/planner-validation.json`. The second verifies the first
report's tool hashes before trusting its reference model.

## Remaining integration

The planner is deliberately not included in the installed AI yet. It needs:

1. An ordered aircraft inventory matching creation/conversion/removal, with
   transports excluded from attack dispatch and separate exploration groups.
2. Safe PER/XS bridging for actual group membership, zones and unit orders.
3. Original target selection, target memory, gathering, retargeting and retreat.
4. Separation from DE ground attack/scouting control and corrected soldier counts.
5. Source callback timing, save/load and multiplayer validation.

Useful next source routines: `numberUngroupedAir` `0x005ABF80`, `setupAirGroups`
`0x005AB600`, `fillAirGroups` `0x005ABCB0`, `taskIdleAir` `0x005A1ED0`,
`taskActiveAir` `0x005A20A0`, `taskActiveGroupAttack` `0x005A3C40`,
`objectToAttack2` `0x005931E0`, target heuristics `0x00592980`, and sorting
`0x00592C30`. Target scoring also has an EF hook in `cheatdll/aiattack.cpp`;
the current bytecode oracle does **not** execute injected EF hooks.

Other open systems—support/transport behavior, Force-user and Holocron behavior,
legacy strategic numbers, taunts and live match validation—remain listed in
`ORIGINAL-AI.md`. This checkpoint does not close them.

## Targeting checkpoint

The isolated source oracle now also executes target classification, combat-time
aggregation, heuristics and sorting. These development files are not installed:

- `classic_target_model.py`, `classic_target_oracle.py` and
  `check_classic_targets.py`: **3,633 comparisons across 406 fixtures**. Exact
  float32 scores, victory priorities, seven ranking passes, ties and unordered
  scores are compared with the original routines.
- `classic_target_ranker.xs` and `check_classic_target_ranker.py`: clean XS syntax
  and **522 C++ host cases**, including repeated calls and bounded array reuse.
- `classic_combat_model.py`, `classic_combat_oracle.py` and
  `check_classic_combat.py`: **2,562 original-routine comparisons across 427
  fixtures** for damage/reload aggregation, conversion fallback, missing units,
  zero damage and survival time.

The source gives score-100 victory targets first priority, then traverses six
reachability/wall/economic-target categories. Equal scores preserve input order.
Its “unit/building” flag actually excludes a small list of economic building IDs;
it is not a general unit-versus-building distinction. The source survival-score
formula reuses time-to-kill, despite gating on the time-to-be-killed range. That
quirk, including its possible NaN result, is preserved.

Combat-time collection executes the original `addUnit` routine at `0x00592430`.
Each member contributes damage divided by reload time. A qualifying zero-damage
converter contributes 10% of the victim's HP per second. Survival time sums each
friendly member's estimated survival against the supplied enemy set; an
unthreatened member can produce the maximum-float sentinel. Virtual damage and
conversion eligibility, positions and zones are explicit fixture inputs. Armor
calculation and live observations have not yet been ported by this checkpoint.

Reports are `work/classic-engine/target-validation.json`,
`target-ranker-validation.json`, and `combat-validation.json`. Run the corresponding
Python check scripts from the workspace. The ranker check requires a current
target-validation report and verifies its model/oracle hashes. Original sorting
is tested only through 128 targets; larger ranker tests compare the reference
algorithm, not the original marker-array tail. EF's injected special-type2 target
hook, live candidate admission/memory, commands and the DE XS runtime remain
outside these tests. No full-match parity claim follows from these counts.

## Individual nursery orders

The actual source idle-animal automation lives in `TRIBE_Action_Artifact::update`
at `0x005650F0`, outside the PER scripts. `classic_nursery_oracle.py` executes its
idle branch with explicit ownership/action-stack fixtures and records enter/move
requests. Separate fixtures execute the real nearest-object searches at
`0x004AF610` and `0x004AF3E0`, and the idle delay assignment at `0x00564F70`.
**1,553 comparisons** pass against `classic_nursery_model.py`.

The source skips humans, occupied action stacks and already housed animals. It
selects the nearest completed nursery (master ID 319), checks that first one's
capacity, and if full requests entry to the next nearest without checking the
second's capacity. With no nursery it moves toward the nearest Command Center or
Food Processing Center (109/68). These calls use no zone filter. Ties retain the
source object-list order. The owned-animal waiting state sets a one-second timer.

`classic_nursery_controller.xs` implements those choices using the mapped DE
building families. `classic_nursery_bridge.py` emits nine isolated PER rules to
read idle/order state and issue native commands. It uses target IDs directly,
clears search lists around commands and advances a bounded animal queue. The
backward jump is relative to the **next** rule (`7 + 1 - 7 = 1`), following the
[UserPatch scripting guide](https://userpatch.aiscripters.net/reference.html).
The independent PER parser does not detect a wrong jump offset; the dedicated
controller check verifies it explicitly.

`check_classic_nursery_controller.py` compares **964 C++ host cases** with the
source-tested policy, including repeated same-time calls, player separation,
full/unfinished/upgraded buildings, busy animals, housed animals and food-egg
exclusion. This is not native PER/XS execution. DE's idle reports, selected-target
retention, actual commands, one-second polling versus per-animal source timing,
array ordering, save/load and multiplayer remain runtime checks. Source workers
are class 58; source herdables are class 1 and map to DE class 58. Never confuse
source class numbers with the mapped DAT classes.

## Armor and attack modifiers

`classic_damage_oracle.py` runs the original combat armor formula
(`0x004449C0`) and the combat/building attack-modifier routines (`0x0055BBC0`,
`0x00557BA0`). `check_classic_damage.py` passes **3,716 comparisons** against
`classic_damage_model.py`: 2,180 armor cases and 1,536 modifier cases.

Armor entries match by class; missing classes use base armor and the last
duplicate armor entry wins. Nonpositive per-class contributions are discarded,
then a nonempty weapon list has a minimum damage of one. An empty weapon list
returns zero. Terrain defense multipliers below one are replaced by one.
Modifier checks cover the higher-ground predicate, lower elevation, the special
attack flag/action-133 gate, and building relic/special-relic multipliers.

The higher-ground predicate itself (including cliffs), action presence and live
DAT observations are fixtures here. Attack eligibility, shield application and
the DE observation adapter remain open. The report is
`work/classic-engine/damage-validation.json`. This checkpoint does not change the
installed nursery release `acec8b2` or either delivered archive.

## Candidate admission and group validity

`classic_admission_oracle.py` executes the original candidate-loop slice at
`0x005934A9` until its admission/rejection boundaries, and the complete
`verifyGroupValidity` routine at `0x005941A0`. The independent reference is
`classic_admission_model.py`. `check_classic_admission.py` passes **2,160 candidate
cases and 489 group cases**. World lookup, visibility, movement, conversion and
zone answers are explicit fixtures; the filtering branches, naval wall scan,
boat classification and group aggregation run from original executable bytes.

The gate uses remembered ownership for the requested-player filter, then live
existence/status/relation/state/HP. Non-buildings must pass visibility checks and
are rejected when `isMoving()` returns exactly one. Master type 80 buildings
bypass both checks; the source can select remembered buildings in fog. Do not
mistake virtual slot `0x300` for a garrison query: the source vtable identifies it
as `isMoving`. Easy/Easiest additionally reject source class 58 (workers).

Boat classification uses source object-flags bit 1 (`flags & 2`). Land groups
exclude boats and master type 45. Boat groups accept boats, raw source ID 45
(dock), or class-6 walls with a tile in the leader's zone within the clipped
seven-by-seven square. Wall coordinates truncate toward zero before scanning.
The all-monk gate checks the reference monk's conversion eligibility only when
that monk and its UnitAI exist. A missing reference does not itself reject the
candidate. A forced-other-zone request applies only to land groups.

Group validation rejects missing members, mixed source boat/land classification,
and differing zone bytes. It accumulates a float32 centroid and selects the first
source-class-50 monk as reference, retaining partial outputs on failure. Its
empty-group result includes a NaN centroid, although the caller rejects an empty
group before calling it. These details are covered explicitly.

`classic_target_admission.xs` contains the corresponding pure gates and bounded
wall-tile check. `check_classic_admission_xs.py` checks syntax without warnings and
passes **2,160 C++ host cases** against the source-tested fixtures. It is not
installed, does not query hidden units, and expects source-compatible observations
from a future adapter. The C++ host is not the DE XS VM. Reports are
`work/classic-engine/admission-validation.json` and `admission-xs-validation.json`.

The post-ranking source path was also traced: it tries normal attack paths,
conditional transport paths, then same-zone obstruction paths. Successful
obstruction paths queue blockers before the intended target. Selection can yield
and resume at a saved rank when its time budget expires. The control flow is
covered by the development checkpoint below; live path geometry, memory and
issued orders remain open. Admitting and ranking candidates alone is not enough
to reproduce the selected target.

## Path and identity development checkpoint

The next post-ranking layer is now implemented in `classic_path_model.py`,
`classic_path_oracle.py` and `classic_path_selector.xs`. The oracle executes
`0x00593938..0x005940C1`, with path geometry, time queries and memory refresh
provided as explicit fixtures. `check_classic_paths.py` passes 893 cases;
`check_classic_path_selector.py` passes the same 893 cases in a C++ host with
clean XS syntax. These cover minimum weapon range, transport fallback, exception
terrain checks, blocker queues, attack-attempt accounting and saved rank indices.
The original blocker queue accepts only 19 entries, despite its 20-slot storage.
Actual source pathfinding and live DE orders are not implemented by these tests.

`portdat classic-ai-identity` is a read-only export of the current/source DAT pair.
`classic_unit_identity.py` verifies the current raw DAT against the assembled
package, exports 21,744 records, and generates an XS lookup for original classes,
types, traits, fog flags and unit lines. `check_classic_unit_identity.py` passes
43,941 lookup cases, including absent IDs, unknown civilizations and explicit
ownership/copy-ID fixtures. Runtime upgrade/conversion semantics remain unverified.
Generated files and reports are under `work/classic-engine`; regeneration needs
the locally installed source assets and the compiled DAT tool.

## Runtime total-count bindings

`classic_ai_bindings.py` adds source-ground and source-warboat groups;
`port_classic_ai.py` rewrites `soldier-count`/`warboat-count` accordingly.
Identical ordered groups with matching building semantics share IDs: 90 names
use 87 custom entries, while native definitions remain intact.

`check_classic_counts.py` passes 27,960 checks. It executes the original class
dispatch and total-count getters, compares both factions' current records,
checks group aliases and preserves all 34 source comparisons and thresholds.
`check_classic_ai.py` also validates all 81 difficulty/mode/personality cases,
population branches and the unchanged nursery XS. The narrow assembler verifies
the current payload against both reports and changes only the main Classic PER
and `unitlines.json`. The binary DAT, maps and nursery controller stay unchanged.

This is the runtime count follow-up in `v0.0.2-dev-classic-ai.4`; matching Assets
and Data are required. Native DE count lifecycle still needs in-game verification.
Attack/defend counts require the source group controller. The path and identity
components above remain development-only. No game was launched.

## Attack-pool admission development checkpoint

`classic_army_pool.py` and `classic_army_pool_oracle.py` reproduce the next input
stage for dispatch. The oracle executes source linked-list group membership,
attack-group total getters and the ground/air ungrouped collectors. Object lookup
and difficulty are supplied fixtures, with preallocated storage. The original
membership searches and output deduplication run as x86.

Ground admission excludes medics (source class 51), and excludes force users
(class 50) on Easy/Easiest. Air admission excludes transports (class 59).
Missing objects and membership in any tactical group exclude either kind.
The collector preserves source-list order and counts repeated eligible input
entries in its return value while emitting each ID only once in the queue.
Attack counts sum all members of type 100/108/102 groups for ground/air/boats;
they do not query current object existence. Lifecycle updates must keep those
groups consistent before these counts can replace the native DE facts.

`check_classic_army_pool.py` passes 1,582 executable comparisons, including
overlapping groups, missing objects, duplicates, transport/force-user exclusions
and input sizes up to 1,024. `classic_army_pool.xs` supplies a scratch admission
queue for the future controller; its caller must provide source classification
and original group membership. `check_classic_army_pool_xs.py` passes 760 C++ host
queues with clean XS syntax and one reused array. It is not a DE VM test.
Neither component is installed. The latest installed/share release remains
`db57ca1`, tagged `v0.0.2-dev-classic-ai.4`.

## Tactical-group state development checkpoint

`classic_group_state_oracle.py` executes original `createGroup` (`0x5ACE30`),
its group/path constructors, `addUnit` (`0x59ACB0`), `removeUnit` (`0x59AD00`),
delete-by-ID (`0x5ACEE0`), delete-by-type (`0x5ACF40`) and group membership.
Only allocation/free use fixtures; linked-list mutations and constructor-empty
path destruction execute original bytes. Snapshots validate forward/backward
links, allocation ownership and the modeled fields after each operation.

The source keeps 40 ordered members, accepts duplicates, removes only the first
matching member and updates last-added time only on a successful insertion.
Creating with `initID == 1` allocates a sequential ID and increments the counter;
other values leave ID -1 and do not increment. Deletion still decrements the
counter, including that source edge case. Allocation failure leaves state intact.
The caller supplies the next ID from its AI state; this does not infer startup
or save/load behavior from an isolated constructor.

`check_classic_group_state.py` compares 3,680 source mutations.
`classic_group_state.xs` provides five reused arrays, per-player ordered lists
and reusable group slots. `check_classic_group_state_xs.py` replays the verified
sequences interleaved across eight players and checks 4,291 complete transitions,
player isolation, links, field values and slot reuse. The XS is syntax checked
and executed in a C++ host, not the DE VM. This covers container state, not full
path memory, targeting, command scheduling, save/load or multiplayer execution.
No new mod build was generated for this development component.

## Combined ground/air dispatch development checkpoint

`classic_attack_dispatch_oracle.py` executes source `attackNow` (`0x5AE520`)
with its actual ground/air collectors, spatial grouping, group constructor,
member insertion and linked-list updates. Boats are explicitly disabled in this
checkpoint. World lookup, positions/zones, difficulty, allocator and stop-command
delivery remain fixtures. The original routine queues a stop for every selected
unit, initializes type 100/108 groups with action 1, clears targets, sets the
attack flag, records desired membership and sets the retreat count to half the
members on Easy/Easiest. Subsequent targeting is a different engine update.

`classic_attack_dispatch.xs` composes the existing admission queue, spatial
planner and per-player group store. It exposes an ordered stop-request queue,
not live orders. The planner now accepts a separate requested size so duplicate
input count behavior does not change the unique queue's clustering limit.
The existing standalone planner regression checks still pass all 4,059 cases.

The combined checks cover ground-only, air-only and mixed percentages, original
difficulty branches, preassigned units, allocation failure and sizes either side
of the original 40-candidate window. Each scenario runs dispatch twice to check
that existing groups exclude their members from subsequent selection. These
fixtures compare group fields and stop requests, not just selected unit counts.
Reports are `dispatch-validation.json` and `dispatch-xs-validation.json` under
`work/classic-engine`. Native DE observations, zone equivalence, stop delivery,
naval integration and the later targeting/order lifecycle remain unimplemented.
No installed files or share archives changed for this controller checkpoint.

## Naval dispatch follow-up

The combined oracle now executes all three source domains in their original
order: ground, boats, aircraft. Boat collection runs inline in `attackNow` and
only checks tactical membership. It counts duplicate input entries while
deduplicating the output, and retains nonexistent IDs. Spatial grouping cancels
if its first ID is missing; other missing IDs consume slots in its first-40
input window. The stop comparison still uses the entire unique input size.
These details differ from ground/air admission and are preserved explicitly.

The expanded suite compares 1,776 scenarios, each dispatched twice, for 3,552
original-executable calls. The composed XS host now checks the exact stop queue
and complete group snapshot after **each** call, including the first dispatch.
It covers all three domains together, shared preassigned IDs, naval duplicates,
missing-first/middle/window entries, Easy/Easiest, and allocation failures across
domain transitions. Standalone source planner (3,261), XS planner (4,059) and
XS pool (760) regressions pass after the shared helper changes.

World/zone queries and command delivery are still fixtures. Null-owner objects
are not covered. Source pool maintenance, live observations, targeting and native
orders still require integration. The installed and shared `.4` build is unchanged.

## DE dispatch observation/command bridge

`classic_dispatch_bridge.xs` connects the dispatch component to DE observation
calls. Its caller supplies the three source-ordered unit-ID arrays, scaled
percentages, game time and group state. For each owned unit, a bounded PER loop
reads `object-data-map-zone-id`; XS resolves the current copy ID through the
verified source-identity table and reads its position. Failed lookups cannot
reuse the preceding unit's zone. Naval missing IDs retain the verified behavior.

The second PER loop drains stop requests one unit at a time. XS checks existence
and ownership; PER independently reads `object-data-player` immediately before
`up-target-point ... action-stop`. Missing, converted or unresolvable units are
skipped. Goals 112–118 are checked against the original source goal graph and do
not collide. A busy guard prevents another pass from overwriting the shared
scratch state. Both backwards jumps lead to advancing queue callbacks.

`check_classic_dispatch_bridge.py` compiles the actual XS plus generated identity
table with explicit builtin adapters. It compares all eligible dispatch fixtures
and injected lookup/death/conversion/callback failures against expected groups
and delivered requests: 724 scenarios / 1,448 calls, alternating eight players
and both factions. It verifies reusable arrays, bounded iteration, first and
repeated dispatch, duplicate callbacks, foreign callbacks, empty input and
failure to begin while busy. The composed XS and ten PER rules pass their
standalone checkers without findings.

This is a development interface, not an enabled replacement for `attack-now`.
Source-ordered pool maintenance is still the caller's responsibility; target
selection after the initial stops remains to be connected. Native DE map-zone
equivalence, actual command delivery, native army interference and save/load
need further work or game verification. The whole bridge pass must complete
synchronously before another player/group uses its scratch arrays. No installed
mod, publication, or release archive changed for this step.

## Source scoring connected to target ranking

`classic_target_scorer.xs` implements the scoring stage at `0x592980` and calls
the existing seven-pass ranker. The caller supplies admitted source-identified
targets, kill/survival time estimates, distance, zone and victory countdown data.
Priority overrides retain their source order and unreachable-time guard. Absent
targets score zero. The original survival term intentionally reuses the kill-time
formula while checking the survival range; equal kill times with unequal survival
times produce an explicit unordered flag rather than dividing by zero in XS.

Intermediate arithmetic needs care: source x87 registers retain extra precision
between float32 stores. The scorer carries arithmetic residuals through division,
multiplication and summation, and rounds tiny residuals at the source significand
boundary near complete cancellation. This prevents both one-ULP score errors and
false nonzero scores for unreachable targets found by the expanded fixtures.
The component retains kill/survival/proximity/zone terms for inspection.

`check_classic_target_scorer.py` executes the composed XS in a strict-float C++ host
and independently runs the original scorer/sorter for each fixture. All four
stored components, final float32 bit patterns and ordered unit IDs match in 836
scenarios; repeated evaluations produce 1,672 host checks with reusable arrays.
Coverage includes original priority/difficulty-related fixtures, fractional
metrics, combat-time magnitudes through FLOAT_MAX, zero/epsilon ranges, near
cancellation and source x87 rounding boundaries. The composed XS has no checker
findings. The oracle now exposes its actual stored component values, avoiding
validation based only on an aggregate score that could hide arithmetic differences.

This is not a proof of exhaustive IEEE arithmetic equivalence or execution in
DE's XS VM. Source input collection, combat estimates, EF's special-type2 hook,
native target-order delivery and the source marker-array tail above 128 remain
outside this comparison. It is a development component, not an installed AI
update; the latest playable/share release remains Classic AI `.4`.

## Combat estimates connected to scoring and ranking

`classic_combat_estimator.xs` ports the aggregation in `addUnit` (`0x592430`).
It keeps the source's ordered 40-member group, per-member incoming damage totals
and overall outgoing damage. Each accumulation preserves the residual of a
division or multiplication until the source float32 store. The conversion
fallback uses the original float32 0.1 coefficient when damage is at or below
the source epsilon and UnitAI `canConvert` succeeds. The threshold is explicitly
stored as float32, preserving the equality branch at `1e-7`.

Missing own units contribute nothing. Missing enemies and enemies without a
UnitAI object are skipped. No enemies, or an existing member receiving less
than epsilon damage, produce the original FLOAT_MAX survival estimate. Explicit
nonfinite DPS states preserve the zero-reload branches: positive damage produces
infinite DPS and zero estimated time; zero damage without conversion produces
an unordered total and the source unreachable-time result. No XS divide-by-zero
operation is used to manufacture these values.

After finishing an estimate, `classicCombatScoreTarget` feeds it directly to the
source scorer. `check_classic_combat_estimator.py` compares 925 estimates with the
original executable, including the existing 427 fixtures, zero-reload/conversion
combinations and sixty eight-target army batches. All exact float32 estimates
match. The 505 batches also match original scoring and target order through 1,010
repeated rank evaluations. The original 2,562 combat comparisons still pass.
The composed XS is syntax checked and its seventeen arrays are reused.

Damage capability, conversion eligibility, existence, UnitAI presence, distances
and zones are still caller-supplied observations. This strict-float C++ host is
not the DE XS VM. Overflowing finite accumulations, signed-zero reloads and
nonfinite output times are not covered. Original per-class damage calculations,
live observations and attack-order delivery remain to be connected. No installed
files, data build, publication or share archive changed in this checkpoint.

## Armor damage connected to the combat pipeline

`classic_damage_calculator.xs` reproduces the ordered class calculation at
`0x4449C0`: start each weapon with base armor, use the last matching armor entry,
apply clamped defense terrain and attack modifiers, discard nonpositive
contributions, sum repeated weapon entries, and apply minimum one damage only
when weapons exist. It retains arithmetic residuals until the final float32
result, matching the source's extended intermediate accumulation. Armor storage
grows and is reused rather than silently truncating at its initial capacity.

The source attack-modifier chain (`0x55BBC0`/`0x557BA0`) includes higher-ground
precedence, lower-height penalty, the mode-3/action-133 multiplier, and building
relic/special-relic adjustments. Source float32 constants and priority between
ordinary and special relic counts are preserved. The modifier scratch state is
separate from the accumulated damage.

`check_classic_damage_calculator.py` compares 2,192 armor cases and 1,536 modifier
cases against original x86 execution, including duplicate classes, negative
strengths/armor, zero weapons, signed-int16 extremes and arrays through 1,024
entries. The oracle now permits up to 1,024 entries in each separate 4 KiB fixture
region. The existing 3,716 source/reference comparisons also pass.

`classic_combat_pipeline.xs` passes a completed armor result to the combat
estimator, keeping damage eligibility and conversion capability separate.
`check_classic_combat_pipeline.py` composes the actual XS damage, combat, scoring
and ranking modules. Forty army batches use 2,338 source-derived armor-pair
definitions, with exact agreement for 160 combat estimates and 80 repeated
ranking evaluations. Environmental modifiers, zero reload, missing objects,
UnitAI absence, damage-ineligible targets and conversion alternatives appear in
these fixtures. The nineteen arrays are reused and the combined XS is clean.

These are strict-float C++ host checks, not native DE gameplay. Live attack/armor
queries, task eligibility, conversion permission, visibility and order delivery
remain to be connected. Inspection of `RGE_Combat_Object::damageCapability`
(`0x445F60`) identifies another required wrapper behavior: if the target is null
or the attacker has no UnitAI, it sums positive raw weapon strengths instead of
running the target's armor formula; otherwise it calls UnitAI `canAttackUnit`
(`vtable + 0x4C`), returns zero on failure and delegates to the target's virtual
damage routine on success. That wrapper and its class-specific predicates are
the next integration step. The current pipeline's eligibility boolean only
represents the target-present/UnitAI-present branch, so it is not a completed
live `damageCapability` replacement. No installed files or archives changed.

### Damage capability wrapper follow-up

`classicDamageCapability` now implements the wrapper described above. The
positive raw-strength sum is kept as an integer until its final float32 store,
avoiding early rounding for long weapon lists. The combat pipeline accepts
target/UnitAI presence and applies the wrapper before aggregation. Existing
incoming-enemy UnitAI exclusion in the estimator remains a separate source rule.

The oracle executes `0x445F60` and binds its target virtual call to the actual
`0x4449C0` armor routine. UnitAI presence, its attack predicate and the already
computed modifier remain fixture boundaries. All 1,616 source wrapper cases
match the reference and compiled XS, including empty/large weapon lists and
all combinations of target presence, UnitAI presence and attack permission.
The 3,728 damage/modifier checks, 3,716 reference comparisons and the combined
160 combat / 80 rank evaluations still pass. This closes the wrapper gap, but
not its class-specific eligibility or native observation dependencies.

## Base and defensive-building attack eligibility

`classic_attack_eligibility.xs` ports base UnitAI `canAttackUnit` (`0x41C530`),
the tower wrapper (`0x5B7CD0`) and the direct building delegate (`0x5B8A90`).
The base predicate checks target invisibility to the attacking player, source
class/ID exclusions, ground-to-air overrides, the resource-31 ID exception and
the original ground/air class matrix. Source IDs and classes are required;
remapped DE classes cannot substitute for them.

The installed executable has a static jump to `0x7B2170`, whose membership
loop reads `Data/ground-to-air.txt`. The catalog generator reads and hashes this
installed file rather than freezing its 17 entries in the controller. The
oracle supplies the file loader's resulting table and executes the original
membership loop. It does not simulate OS file loading or injected DLL hooks.

Tower restrictions retain target presence, player/Gaia checks, target building
flag `+0x235`, source ID 50, and the attacker's construction state. The source
class-5 target shortcut precedes the base call and therefore bypasses its
invisibility/ID checks; tests preserve that ordering instead of adding an
apparently reasonable restriction. Ordinary building UnitAI delegates directly
to the base function, without the tower-specific conditions.

`check_classic_attack_eligibility.py` matches 17,846 base, 11,592 tower and 3,570
building cases against original executable calls and the compiled XS. Cases
cover the class matrix, signed-short boundaries, all catalog entries and their
neighbors, each earlier denial, resource thresholds, unordered resource values,
target owners and construction states. Generated catalog provenance and code
hashes are recorded in `work/classic-engine/attack-eligibility-validation.json`.

These predicates are development-only. Actual invisibility, native state and
player-resource observations remain caller inputs. Soldier/priest/siege/civilian
wrappers and damage-capability virtual dispatch selection still need integration.
The checks do not execute the DE XS VM, change the installed `.4` release or
establish full AI parity.

## Soldier and priest attack gates

`classic_soldier_eligibility.xs` adds source soldier (`0x5B6E70`) and priest
(`0x5B4B60`) wrappers. Both preserve Gaia-target restrictions, target building
flag exclusions, and the original stance/order/patrol logic. Soldiers reject
class 34 and block actions 124/125 for class 36 or source ID 109. Priests instead
reject held attribute 57; this is their attack predicate, not conversion.

Stance 3 checks **last** action 600. Stance 2 limits the distance from the saved
stance position to weapon range plus 0.5, or plus 2 for Gaia, unless current
order is 701. Stance 1 chooses the source highest-level-path distance for
orders 711/733 when on patrol, otherwise the saved patrol-path distance when
available, otherwise the stance-position distance; its buffer is 5. Comparisons
preserve the original treatment of unordered values. A compensated sum avoids
rounding a range boundary early in XS.

XS permits at most twelve function parameters, so the caller supplies motion
through `classicAttackSoldierSetMotion` immediately before each soldier/priest
query in the same synchronous pass. The scratch result is not retained unit or
player state. `check_classic_soldier_eligibility.py` alternates both predicates
and verifies 7,826 soldier and 8,690 priest cases against actual original calls.
The source calls the real base predicate and static EF membership patch; range,
geometry, action/patrol and invisibility queries are explicit fixture boundaries.
Tests include early-gate precedence, near-boundary float32 distances, unordered
values, non-boolean patrol return values and randomized geometry.

The composed XS passes syntax checking and a strict-float C++ host. It has not
run in DE or been installed. Conversion, specialized siege/civilian predicates,
native observations and commands remain open; these tests are not an exhaustive
floating-point or full-behavior proof.

## Priest conversion eligibility

`classic_conversion_eligibility.xs` ports `canConvert` (`0x5B48E0`), separately
from priest damage eligibility. It rejects Padawans and class 51, requires 100
Force unless the caller explicitly ignores Force, rejects a missing/Gaia target,
and requires positive player resource 67. Original class/ID exclusions and the
type-70/type-80 unconvertible flag are retained. Source classes 50/64 require
Master status and resource 27; the original mechanical-target class set requires
Master status and resource 87. No extra diplomacy, visibility or attack-stance
condition is inserted into this routine.

`classicConvertSetPermissions` supplies the attacker's Master/research state
immediately before each `classicCanConvert` call, staying within XS's parameter
limit. The oracle executes the original routine with only Padawan/Master virtual
traits and world lookup stubbed. Force, resource, class, ID and target-flag fields
are read by the actual executable instructions.

`check_classic_conversion_eligibility.py` matches 7,920 source/XS cases: the full
class matrix across research/Master combinations, blocked IDs and their neighbors,
target types/immunity flags, Gaia/missing targets, Force values on both sides of
100, explicit ignore-Force, unordered values and permission changes between calls.
This is a development gate only. Actual conversion timing/chance, native state
queries and commands are not implemented by this component. No installed or
shared files changed and no native DE gameplay was run.

## Eligibility through target ranking

`check_classic_combat_pipeline.py --eligibility` now composes all five implemented
attack predicates plus priest conversion with the actual XS armor, combat,
scoring and ranking modules. The host supplies typed observation records,
refreshes motion/research scratch state before every query, invokes the matching
XS predicate and passes its result into the existing damage/combat pipeline.
The test-only adapter is `classic_combat_eligibility_fixture.py`.

Every gate is checked against the corresponding original executable call before
its result enters combat aggregation. The complete chain matches 2,338 pair
definitions, 160 combat estimates and 80 repeated ranking evaluations. All five
attack kinds have both allowed and denied outcomes. Priest cases include damage
only, conversion only, both and neither. The original boolean-fixture pipeline
also still passes, and the composed XS is syntax checked.

`work/classic-engine/combat-eligibility-pipeline-validation.json` records the
source executable, generated catalog and implementation hashes, gate counts and
outcomes. This is an integration check in the compiled strict-float host, not a
native DE observation adapter. The caller still supplies UnitAI kind, world state,
stats, geometry, trait and research observations. Missing-object and no-UnitAI
wrapper branches retain their separate checks. Native attack/conversion orders,
the remaining UnitAI subclasses and gameplay validation are still outstanding.
Installed and shared files remain Classic AI `.4`.

## Remaining UnitAI combat gates and factory selection

The source table audit (`classic_unit_ai_catalog.py`) reads constructor vtable
stores from the pinned executable. Its fifteen tables, including the base class,
reference nine attack routines, five neutrality routines and two conversion
routines. All nine attack routines now have development XS counterparts. This
is coverage of these virtual slots, not every behavior in those AI classes.

Siege eligibility (`0x5B8180`) uses the shared stance/path decisions but adds
construction-state, computer-player and active-action checks. Class 35 accepts
only its original building-class set and bypasses the base check; classes 34/36
use their restricted target set before calling the base. Gaia-target handling
differs from the soldier wrapper and is preserved. The mobile checker now
matches 14,386 siege cases in addition to the soldier and priest cases.

Civilian and lion wrappers guard missing targets before base eligibility; the
medic's virtual slot always returns false. Neutrality checks preserve each
subclass's different exclusions, including the class-45/class-59 distinction.
The base checker covers 54,943 cases across base/building/tower/civilian/lion/
medic/neutrality. The composed combat pipeline now exercises all nine attack
routines and the shared non-priest conversion refusal, with the original
2,338 pair definitions, 160 estimates and 80 rank evaluations still matching.

`classic_unit_ai_factory.xs` ports the type selection in `initUnitAI`
(`0x55D430`). Some source classes intentionally have no UnitAI; other classes
choose animal, worker, medic, priest, ship, soldier, artifact or siege behavior.
Building classes use tower behavior when source `volley_missile_id` is
nonnegative; classes 9/10 always use tower behavior. Unknown source classes
fall back to soldier behavior. Combat/neutrality/conversion kind mappings are
checked against the actual vtable pointers, rather than guessed from names.

`check_classic_unit_ai_factory.py` compares 67,264 original factory calls and
65,896 compiled XS selections. Every signed-short class is covered. Additional
cases vary the volley ID, an existing AI and allocation failure. The source
destroys the old instance first, stores the new constructor result or null,
and uses a five-order queue for artifacts versus ten for other types. The
oracle executes that control flow with allocation/constructor/destructor
boundaries; it does not execute the new AI's complete constructor or destructor.
XS selects a behavior kind and does not create native DE UnitAI instances.

Reports remain development evidence. Live source-identity/volley observations,
dynamic state, target memory, commands and native DE execution still need
integration. No installed mod, release archive or publication changed.

## UnitAI type connected to source identity

The read-only DAT identity export now appends `source_volley_missile`, preserving
all eighteen previous columns across all 21,744 records. The generator derives
the expected original UnitAI type for source types 70/80 from the verified
factory selector. Other object types retain no combat UnitAI type. Four spare
bits in the existing packed identity field carry this value, so the adapter
still uses two arrays and preserves its class/type/trait/fog/line getters.

`classicSourceUnitAIType` resolves the expected source type using the supplied
unit's current owner, civilization and copy ID. `classic_unit_ai_identity.xs`
connects it to attack, neutrality and conversion kind queries. These functions
describe the original template behavior; they do not report that an equivalent
native DE UnitAI object exists or has already been installed.

The identity checker now compares the derived types and their dispatch kinds
with original factory calls and source vtable entries. All 43,941 adapter cases
pass across 21,744 records and eighty distinct source class/volley combinations.
Invalid/missing units and unsupported civilizations remain covered. The previous
eighteen columns were compared field-for-field with the pre-change export, and
the existing bridge still passes 724 scenarios / 1,448 dispatch calls with the
extended generated identity data. Packaged/current/source DAT hashes remain
unchanged; only the development exporter and metadata adapter changed.

Dynamic attribute changes, original UnitAI state maintenance, native copy-ID
semantics after upgrades/conversions, and actual command delivery remain open.
No new mod archive was created and no installed release changed.

## Factory-driven combat dispatch and actor binding

`classic_combat_gate.xs` now dispatches through the expected original UnitAI
type. The caller can initialize an actor from source class/volley/type metadata
or the already resolved source identity. Shared attack, conversion and motion
scratch state is cleared when selecting an actor; callers then supply the fresh
motion/research observations required by that actor's predicates. The wrapper
exposes UnitAI presence separately from attack permission so the original raw
damage fallback remains distinguishable from an attack denial.

`classic_combat_identity.xs` binds a supplied existing unit to this context using
its owner, civilization and copy ID. Missing units and unknown identities clear
the previous actor. Known source templates with no UnitAI remain distinct from
unknown identities. The composed identity checker verifies these resets after
deliberately seeding old motion/research permissions; all 43,941 cases pass.
Dynamic construction state, held attributes and player-control state are still
explicit caller inputs, not inferred by this binding.

`check_classic_combat_pipeline.py --source-types` uses original factory calls
for 81 class/volley combinations rather than assigning UnitAI kinds manually.
The actual XS dispatcher then feeds the damage wrapper, combat estimator,
target scorer and ranker. All 2,338 pair definitions, 160 combat estimates and
80 ranking evaluations match the original routines. All nine attack kinds are
exercised, including 109 no-UnitAI attacker-pair definitions on the incoming
side, where the source estimator skips them. The earlier explicit-kind pipeline
also still passes.

An integration probe exposed a source evaluator precondition: an existing own
attacker whose damage reaches the conversion-fallback branch must have UnitAI.
The original `addUnit` dereferences it without a null check at `0x5925FB`.
`check_classic_combat_precondition.py` records four isolated probes: no UnitAI
with zero damage faults there; positive damage or an existing UnitAI does not.
This fault was observed inside the emulator only. The combined combat fixtures
respect that own-attacker precondition and retain no-AI enemies/targets. Separate
damage-capability checks still cover raw-strength fallback, including empty
weapons. No runtime crash is added to the XS implementation, and no equivalence
is claimed for the invalid source-evaluator input.

These are compiled-host integration checks. They do not supply live motion,
invisibility, conversion resources, path observations or attack/conversion
commands, and they do not establish full native AI parity. No installed or
shared release changed.

## Combat data and ordered attribute changes

The read-only `classic-combat-report` exporter compares the current Classic
dataset with the original Gaia/Empire/Rebels definitions. Run
`classic_combat_data.py` followed by `check_classic_combat_data.py` after building
`portdat` with the canonical `main.cpp` and `classic_combat_report.h`. Reports
are under `work/classic-engine/combat-data`; source/current/package hashes are
verified before and after export. Neither DAT is modified.

All 12,536 combat records preserve ordered attack/armor tables, HP, base armor,
reload, maximum/minimum range and defense terrain. Float values use round-trip
precision and table entries preserve signed shorts. There are 54 records with
duplicate attack classes and three with duplicate armor classes; these are real
data, not only synthetic edge cases. Ten deliberate mutations verify that the
audit catches attribute drift, reordered entries and collapsed duplicates.

For set/add/multiply commands affecting HP, armor, attack, reload, range, base
armor, projectile, defense terrain, minimum range and blast width, expansion of
unit/class selectors produces 136,087 ordered applications on each side with
no differences. One unchanged command (effect 48, ordinal 3; HP multiply 1.1,
unit/class both -1) has unresolved selector semantics and is explicitly excluded
from that expansion claim. These counts include effects that may never be
reachable for a playable faction. Input parity is not native execution parity.

`classic_combat_attribute.xs` ports the original ordered table update methods:

- Set (`0x4899B0`) uses the encoded high byte as a **table index**, not a class.
- Add (`0x489B10`) and multiply (`0x489D20`) change the **first** matching class.
- Absent classes and out-of-range set indices are no-ops; tables do not grow.
- Encoded low bytes are unsigned, stored amounts are signed shorts, and
  addition wraps at 16 bits. Negative encodings retain their low 16 bits.
- Multiply uses float32(0.01), adds 0.5 in x87, then truncates and stores a
  short. XS retains the fractional residual before truncation, including
  negative and integer-boundary cases.

The functions operate on explicit caller-owned arrays. They do not mutate DE
units or intercept research. `check_classic_combat_attribute.py` compares actual
source methods with the Python model and compiled XS for 8,240 cases. These
include 2,280 unique cases drawn from 80,222 potential source-DAT applications,
both armor/weapon tables, duplicate ordering, byte selectors, signed overflow,
and percent boundaries. Guard bytes and the other table verify no collateral
writes; source counts/pointers remain unchanged. The XS checker reports no
errors or warnings. Refreshed identity validation still passes 43,941 cases.

The audit's absent-selector reports use those verified source semantics. They
must not be interpreted as evidence that DE adds or ignores absent classes.
Likewise, [the official XS API documentation](https://www.forgottenempires.net/age-of-empires-ii-definitive-edition/xs-scripting-in-age-of-empires-ii-definitive-edition)
documents per-unit class-specific attribute getters, but does not establish how
they expose absent or duplicate entries. Native getter semantics, source state
tracking through upgrades and live combat observations remain unfinished.
This development checkpoint creates no mod archive and changes no installed
or shared release.

## Native combat observation adapter (development)

`classic_combat_catalog.py` generates `combat-data/classic_combat_catalog.xs`
from the verified source/current tables. It stores table layouts, not static
attack/armor amounts: 392 profiles use 5,410 integers, with a 23,880-integer
map for the three supported civilizations. All 12,536 combat records have an
exact ordered layout; unknown or noncombat templates return -1. Layout flags
separately identify duplicate/negative weapon classes and armor classes.

`classic_combat_observation.xs` consumes this catalog and the damage calculator.
Given an already admitted attacker/target pair, it queries current per-unit
attack and armor by class, base armor, reload, current HP and maximum HP using
DE XS getters. Armor is loaded before weapons. A missing target retains the
source raw-strength fallback; a missing attacker invalidates the observation.
No unit enumeration, visibility admission, eligibility or orders are added.

The caller must check the returned boolean and `classicCombatObservationReady`
before consuming damage scratch state. Status values are:

| Status | Meaning |
| --- | --- |
| 0 | Getter-contract observation completed |
| 1 | Attacker no longer exists |
| 2 | Unknown or noncombat source template |
| 3 | Relevant table contains duplicate or negative classes |
| 4 | Getter returned a fractional/out-of-short-range amount, invalid HP/reload, or nonfinite value |

Every failure clears partial damage, HP, reload and readiness. A duplicate in
an irrelevant table does not reject the pair: only attacker weapons and target
armor are used. The remaining ambiguous layouts need further source/native
handling; they are not collapsed or represented by stale base values.

`check_classic_combat_observation.py` checks every generated profile and 37,624
queries in a compiled XS host. Mocks deliberately change live strengths, armor,
HP and reload between calls without changing the catalog. They reject calls
for missing units or absent classes, count getter calls, check both factions
and Gaia, and inject invalid attributes. All 10,597 distinct accepted damage
queries match the actual original damage-capability routine. The adapter and
catalog retain four arrays across repeated calls; XS lint is clean.

This validates the implementation against an explicit getter contract, not
native DE runtime behavior. In particular, whether DE's class getters return
the expected amount after every upgrade remains unverified. Dynamic source
modifiers, eligibility inputs, complete unsupported-layout handling, estimator
orchestration and actual commands remain open. No development controller is
enabled in the playable release.

At the user's request, Classic AI `.4` (`db57ca1`) was reinstalled/verified from
its SHA-256-pinned full release ZIP. All 4,892 payload files already matched;
the two mod metadata files were refreshed. The 4,894-file installed set and
base-game DAT preservation were checked. No game was launched, no subscription
was changed, and no new release archive was created. Verification is recorded
in `work/classic4-reinstall-verification.json`; this does not claim a gameplay
test or guaranteed crash-free operation.

## Live-query combat controller (development)

`classic_combat_live.xs` joins the native observation adapter, generated source
identity, damage calculator, combat estimator and scorer. The caller supplies
already admitted army, candidate and enemy IDs, then the original eligibility
and modifier results for each pair. No discovery, visibility permission,
eligibility approximation, commands or native AI takeover are introduced.

The API is an ordered synchronous pass:

1. `classicLiveCombatBegin` copies the enemy-ID list and snapshots army HP,
   reload and existence. The original one-to-forty own-member bound is retained;
   enemy storage grows to the supplied count rather than assuming forty.
2. `classicLiveCombatOutgoing` accepts each member in source order, requires its
   expected runtime ID and observes fresh damage/reload. A missing member keeps
   its slot without contributing. Expected source UnitAI comes from source
   metadata; the low-damage/missing-own-UnitAI precondition aborts explicitly.
3. `classicLiveCombatIncoming` accepts enemy IDs in order for each member.
   Missing enemies and known source templates with no UnitAI are skipped.
   Unknown metadata is distinguished from known absence of UnitAI.
4. `classicLiveCombatFinish` exposes an estimate only after every required pair
   has been submitted. Wrong-order/duplicate calls reject without replacing the
   current pass. Observation failures abort and clear its partial state.
5. `classicLiveCombatScore` submits a completed candidate once, resolving its
   source class/ID. The caller opens/evaluates batches with `classicScoreReset`
   and `classicScoreEvaluate`. A failed or unfinished candidate cannot enter
   the ranking, and a full batch is rejected explicitly.

Begin, pair submission, finish and score must be driven synchronously in one
caller pass. This API does not claim snapshot consistency across game updates.
Outgoing and incoming accumulators are independent; each retains the original
member/enemy order. A duplicate begin cannot overwrite an in-progress pass.
Abort errors distinguish bad input (1), vanished target (2), invalid/unsupported
native observation (3), missing-own-UnitAI precondition (5) and unknown identity
(6). Callers may retry an ordering rejection or explicitly abort the pass.

`check_classic_combat_live.py` passes 50 candidate evaluations. Forty-one valid
candidates match the actual source combat estimator using 8,895 distinct source
damage-capability queries, then their scores and ranked IDs match two host
ranking passes against the source scorer. Cases include 40 own members, up to
128 enemies, missing army members, missing/no-AI enemies, source-priest
conversion estimates, raw-strength fallback, zero reload and changed live
attributes. Nine failing candidates cover vanished units, invalid HP/attributes,
unsupported duplicate layouts, unknown civilizations and the source precondition;
none enters scoring. Busy, premature, wrong-ID and duplicate submissions are
checked, along with caller enemy-array mutation after Begin. The composition
retains 26 arrays including caller lists and scorer/ranker storage; XS lint is
clean.

These are native-getter **contract mocks**, not DE gameplay tests. Eligibility,
terrain/height modifiers and conversion permission are still explicit caller
inputs. Native getter verification, ambiguous layouts, remaining source state
and command delivery remain unfinished. The controller is not installed; no
new mod release or Dropbox archive was created, and playable `.4` is unchanged.

## Force ranks, research permissions and retained upgrade identity (development)

`classic_force_rank.py/.xs` reproduces the original Padawan (`0x54B170`) and
Master (`0x54B1D0`) predicates. Each tests both the original master ID at +0x18
and the upgraded copy ID at +0x1A, with different ID sets. The native observer
reads these separately, rejects unknown templates and clears scratch permission
state before every observation. Source research resources 27/67 remain in their
native slots; 31/87 map to 2031/2087. Twelve initial values and four ordered
resource-effect commands agree between the source and current data exports.
Actor binding clears permissions, so callers must bind the actor before reading
its rank/research permissions.

`check_classic_force_rank.py` verifies 132,440 ID pairs through 264,880 calls to
the original rank functions and the XS host. Both routines return an unsigned
byte in AL; upper EAX bytes are not part of the result. Another 2,088 contracts
cover native getters, faction/owner lookup, differing raw/copy IDs, unsupported
units and state reset. Four probes execute the original master `copy_obj`
(`0x48D390`) with empty dynamic data and only empty-name copying stubbed. They
show that the destination retains its original ID/base ID/class while taking
the source's copy ID; the source template's base ID also changes. This does not
prove native DE getter behavior, live UnitAI persistence or every transform.

`classic_upgrade_identity.py` audits 2,514 mapped direct upgrade applications
(2,508 unique civilization/ID edges). Class, factory selection and Force-rank
results do not differ between retained and copied identity on these edges.
Raw-ID tests do differ: 81 conversion-exclusion, 57 soldier-action-exception,
141 economic-target-category, 15 temple-priority and three ground-to-air tests.
These are potential predicate differences, not a count of reachable gameplay
bugs: additional class/action/research guards can suppress them. Nine unmapped
applications are the same three (-1,-1) placeholder commands across three civs.
Upgrade chains, actual reachability and player notifications remain open.

The live combat scorer now uses the retained object ID for source target
classification. Its 70 candidate checks include actual temple/economic upgrades
and synthetic reversed raw/copy pairs; 61 estimates, 8,900 distinct damage
queries and two full ranking passes match original routines. The target oracle
now groups countdown fixtures into at most four valid synthetic player IDs,
allowing larger candidate lists without overflowing the source's nine-player
countdown arrays. All 836 standalone scoring scenarios / 1,672 host evaluations
and 3,633 target comparisons still pass.

Rank/research observation does not yet supply the original held Force amount,
conversion execution/chance, immunity state or attack orders. Native charge is
not assumed equivalent to source Force. All native observations remain contract
mocks; no game was launched and no development controller or release was
installed. Playable `.4` remains in place.

## Conversion observation composition (development)

`classic_conversion_observation.xs` resolves a supplied actor/target pair through
the source identity and Force-rank adapters. Research comes from the actor's
current owner. Actor/target classes and target exclusion IDs use retained raw
identity; upgraded target type and expected actor UnitAI use copy identity.
Known non-converters and absent targets yield complete denied decisions;
unknown required identity yields an incomplete result. Readiness and allowance
reset on every call. This does not enumerate or discover targets.

The caller must still supply original Force amount, ignore-Force mode and
target immunity. No mapping from DE special-ability charge to original Force
is assumed. Expected source UnitAI comes from the audited templates; runtime
UnitAI persistence and native raw/copy getters remain unverified.

`check_classic_conversion_observation.py` passes 22,165 cases over the entire
21,744-record identity domain plus focused upgraded-ID, research, missing-unit,
unknown-faction, non-converter and floating-point cases. There are 2,204 allowed
decisions and 23 incomplete observations. For 22,137 cases the source conversion
routine executes the actual original Padawan/Master functions through its
vtable, replacing the older trait stubs for this composition. Lookup/world state,
Force amount and immunity remain fixtures. Reusing the same two identity arrays
does not allocate additional arrays. XS lint is clean; all 7,920 earlier
conversion-gate checks still pass. Reports record component hashes and the
uninstalled status; native execution/timing/chance and command delivery remain
unfinished.

## Force-user conversion target choice (development)

`classic_conversion_target.py/.xs` ports `bestUnitToConvert` (`0x5B4E80`). The
original first requests a source LOS search, then walks its result buffer in
order. Each candidate must pass the actor owner's enemy test against the
buffer's owner byte, a live lookup, object state below three, and conversion
eligibility with ignore-Force false. These are distinct gates; the scan owner's
relation must not be replaced by an unrelated live-owner or visibility guess.

Accepted candidates use source master maximum HP divided by the scan's byte
distance, clamped to at least one. Class 47 adds four to the divisor. The
returned distance remains the clamped scan distance without that penalty.
The first accepted candidate wins initially, including nonpositive HP; a later
candidate replaces it only when its extended-precision ratio exceeds the saved
float32 best score. Identical rational scores can therefore replace one another
when the saved value rounded down. The XS comparison preserves the residual of
best-score times divisor instead of comparing two prematurely rounded ratios.
If no candidate qualifies, the caller's initial distance remains unchanged;
null output pointers are valid in the source.

`check_classic_conversion_target.py` passes 3,217 original-routine/XS selections,
33 null-output-pointer checks and 1,294 repeated-ratio replacement cases. Cases
span every byte distance, signed-HP boundaries, both divisor modes, gate/state
combinations, duplicate IDs and ordered lists up to 1,024 entries. The oracle
also verifies the source scan/enemy/lookup/conversion call order. Selection uses
no XS arrays. LOS search, diplomacy, lookup and conversion decisions remain
fixtures; the pure selector expects already normalized source byte/short fields.
Source search uses a shared cached scan and is not yet reproduced by native
observations. No target discovery or conversion orders are installed.

## Original visibility filtering (development)

`classic_visible_scan.py/.xs` reproduces `Visible_Unit_Manager::GetVisibleUnits`
(`0x614A00`) over supplied category lists. Desired-category order precedes stored
record order; repeated categories can repeat records. Five relation buckets each
retain the first 256 qualifying records. LOS is capped at 15 and the preliminary
bounding rectangle extends another seven tiles. An integer distance table uses
absolute byte-coordinate deltas masked to five bits. A record's radius reduces
distance only when its unadjusted distance exceeds LOS; adjusted nonpositive
distances become one. A center-tile record can retain distance zero. Empty desired
categories or player beyond the player count return zero while preserving old
buffers; a valid search of an empty category clears them.

The original `Build_Distance_Table` (`0x614720`) executes in the oracle with only
allocation replaced. It fills distances from 21 ordered static span lists and
uses rounded square-root distance only for uncovered cells. The Python builder
matches all 1,024 bytes (SHA-256
`666523e019b063e7204e020aba8adceec045b097770276c92bb266b61eeefd9c`);
15 entries differ from ordinary rounded Euclidean distance. The generated XS
table is written to `work/classic-engine/visible-scan-host/classic_visible_distance.xs`.

`check_classic_visible_scan.py` compares original and XS outputs for 370 scans,
including 61 early returns, 150 full buckets and 42,140 returned records. It
checks coordinates near map/byte boundaries, radius adjustment, zero distance,
negative and capped LOS, duplicate categories, varying relation maps and exact
buffer retention. Native output records retain owner/position bytes while
replacing radius with distance; XS stores those fields without signed packing
overflow. Repeated calls retain five arrays including the distance table. XS
lint is clean. Category membership/order and relation maps are still fixtures;
this does not enumerate native hidden units or install discovery behavior.

## Visibility-list membership and ordering (development)

`classic_visible_membership.py/.xs` reproduces `Update_Unit_Info` (`0x614840`).
The original constructor (`0x614590`) creates one more category than its category
argument and starts every per-player/category list at capacity 64. The updater
considers the low 16 bits of the old/new visibility-mask difference, bounded by
the number of players. Newly visible records append at the tail. Disappearing
records are removed by moving the last entry into their slot, repairing the
moved object's reference, then clearing the removed object's reference.

When a list fills, capacity doubles, active records retain their order, and all
resolvable object references are repaired. Unchanged visibility bits do not
rewrite owner, position or radius bytes even when different values are supplied.
Those field changes therefore need the original surrounding update lifecycle;
calling the membership function alone is not a movement update.

`check_classic_visible_membership.py` compares the model against 3,960 original
updates across four constructor configurations (zero, one, three and nine
players). It exercises 26 expansions, non-tail removals, byte narrowing,
unchanged/high mask bits, multiple categories and final empty lists. Allocation
and free are fixtures; the source constructor, copies, moves and pointer-repair
loops run directly. Every update checks active records, capacities and all
known object references, including null references after removal.

`check_classic_visible_membership_xs.py` replays the hash-verified traces through
XS and matches all 3,960 updates. The controller reuses eight arrays, stores
records in growing segments and uses abstract array positions as references.
It requires supplied object-lookup presence and visibility/category events;
these are not native discovery observations. Invalid removals reject rather
than dereference invalid source memory, and callers must discard such a pass.
Null global-lookup repair branches, movement/owner field updates, native
visibility events and the higher-level UnitAI scan cache remain open. No
development controller or new release was installed.

## Membership connected to visibility queries (development)

`classic_visible_pipeline.xs` connects the maintained category lists directly to
the source visibility filter. `classicVisibilityReset` initializes membership
and clears the five return buffers, matching the original manager constructor.
`classicVisibilityScan` walks the requested categories in order and decodes each
stored record into the original radius/owner/position fields. It preserves
duplicate-category behavior, per-bucket limits and stale buffers after the
original early returns. It requires valid source category/relation arrays and
does not itself discover native objects.

`check_classic_visible_pipeline.py` executes the original constructor and each
original membership update, then calls the actual `GetVisibleUnits` over those
maintained source lists. Its 3,960 update-then-scan cases match the composed XS
pipeline, including 2,024 retained-buffer returns and 15,543 returned records.
Fixtures vary active querying player, desired category order/duplicates/empty
lists, diplomacy-group maps, coordinates and LOS while lists grow and shrink.
The composition retains 15 arrays including the two caller input arrays; XS
lint is clean. Membership pointer checks were refreshed after extending the
oracle. Native visibility events, movement/owner field updates and higher-level
UnitAI scan-cache gating remain unfinished. Installed/share `.4` is unchanged.

## UnitAI search cache and update entry (development)

`classic_search_cache.py/.xs` ports `UnitAIModule::search` (`0x419EE0`) on top of
the maintained visibility pipeline. The source shared flag at `0x6A3398` skips
search only when exactly one. A new search sets it before checking the desired
category pointer, so a null pointer also consumes the search opportunity.
Cached/null-desired returns preserve earlier result buffers, sighting state,
timer and cached total. A nonnull pointer with zero/negative count still calls
the query; its retained old buffers can therefore affect sighting notifications.

The normal query truncates caller coordinates and uses the greater of the
truncated virtual search radius and truncated master LOS plus one. The actual
source action/static radius getters (`0x409B70`, `0x552E10`) execute in the oracle.
Order 701 can instead query the follow target's truncated coordinates, LOS and
owner if its ID, world lookup and action are available; it retains the actor's
relation map. That branch skips normal sighting/timer updates. A missing follow
lookup/action or world falls back to the normal query.

Normal queries update the actor's sighting byte from return bucket four. With
that bucket nonempty and the notification argument's byte exactly one, a timer
strictly greater than ten emits event 528 with the actor as both sender and
recipient; the timer resets to zero even below that threshold. Other cases
preserve the timer. XS records a notification intent rather than delivering a
reentrant engine callback.

Every search, including skipped calls, executes original `rand` (`0x632BDD`) and
then `srand` (`0x632BD3`) with the saved returned draw. This is not restoration
of the old 32-bit seed. XS represents the source seed as two 16-bit halves so
the multiply/add intermediates fit signed int32; it does not read or replace
DE's native RNG. The oracle also changes the seed inside its notification stub
and checks that the original search subsequently reseeds from its saved draw.

Source-code references identify the shared flag reset in the prefix of the
base `UnitAIModule::update` (`0x419250`). Before its first virtual early-exit test,
that prefix clears the search flag/cached total and adds world elapsed time to
the actor's sighting timer. `classicSearchStartUpdate` reproduces these search
fields. Callers must load the actor's state before that entry step; they must
preserve actual UnitAI update and callback order, not assume a frame-wide reset.
The prefix also resets other UnitAI fields that remain outside this component.

`check_classic_search_cache.py` validates 644 source searches: 302 actual visible
queries, 342 cached/null-pointer skips, 61 follow-target queries and 47 recorded
notifications. It additionally runs 126 original update entries through the
early-exit branch. `check_classic_search_cache_xs.py` matches all search buffers,
query arguments, cache/sighting/timer fields, notification intents and resulting
seeds, then all 126 update-entry states. The composition retains 15 arrays;
XS lint is clean. Reports bind source/component hashes and explicitly mark the
code uninstalled. Native observations, notification delivery, source RNG
synchronization, complete UnitAI update state and multiplayer remain unfinished.

## Visible-record movement, ownership and transformation (development)

`classic_visible_records.xs` adds three source event boundaries to the maintained
visibility lists. `RGE_Combat_Object::teleport` (`0x4461E0`) compares truncated
old coordinates with the coordinates resolved by the base movement call. When
either tile changes and the object ID is nonnegative, it rewrites the two
coordinate bytes through every nonnull visible-record pointer. Movement within
one tile preserves earlier record bytes. Passing the requested destination
instead of the resolved position would be incorrect. Native movement, collision
resolution and event scheduling are not implemented by this component.

The prefix of `TRIBE_Combat_Object::change_ownership` (`0x55B820` through
`0x55B853`) rewrites the owner byte in those records before subsequent ownership
processing. It preserves list order, coordinates and radius. The oracle stops
at that prefix boundary; it does not claim to execute complete conversion.

`RGE_Combat_Object::transform` (`0x443E20`) removes records using the old class
and visibility mask, calls the base transform, then appends records using the
new class/mask/owner/coordinates/radius. This changes list order even for a
transformation within the same class. The two XS phases retain that observable
boundary. The oracle executes the original wrapper and original membership
updates, with the base transform supplied as a fixture state mutation. It
compares the intermediate removed state as well as the final reinserted state.

`check_classic_visible_records.py` compares 3,208 original/reference/XS states
across zero, one, three and nine players: 1,120 mask updates, 524 movement calls,
524 owner-prefix calls and 520 transformations. Coverage includes 165 same-tile
moves, 173 same-category transformations, 13 capacity expansions, byte wrapping,
negative object-ID guards and references repaired after moves/removals/growth.
Actual source queries run after each event and match the composed XS scans:
33,877 returned records and 1,320 retained-buffer early returns. All 15 arrays
are reused; XS lint passes. The source oracle deliberately supplies a requested
movement destination different from its resolved position. Neither the oracle
nor the host runs a native DE match, and installed/share `.4` remains unchanged.
