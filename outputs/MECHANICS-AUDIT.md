# Reachable source-resource effects

These effects change isolated resource slots in the draft. Power and Astromech Repairs have experimental adapters; the remaining slots have no implemented behavior. Counts include automatic and prerequisite technologies; they are not all visible research buttons. This audit does not cover hardcoded unit IDs, task semantics, attributes, flags or artwork.

| Source resource | Commands across both factions | Affected technology IDs | Status |
|---|---:|---|---|
| 10 | 2 | 570 | stored only; behavior unresolved |
| 19 | 2 | 0 | experimental power adapter |
| 23 | 2 | 186 | stored only; behavior unresolved |
| 26 | 2 | 570 | stored only; behavior unresolved |
| 31 | 1 | 164 | stored only; behavior unresolved |
| 33 | 2 | 572 | stored only; behavior unresolved |
| 38 | 1 | 73 | stored only; behavior unresolved |
| 56 | 1 | 159 | stored only; behavior unresolved |
| 58 | 2 | 158 | stored only; behavior unresolved |
| 87 | 2 | 152 | stored only; behavior unresolved |
| 212 | 1 | 663 | experimental XS repair adapter |
| 215 | 6 | 1, 2, 3 | special map buildings; stored only |
| 216 | 6 | 1, 2, 3 | special map buildings; stored only |
| 217 | 6 | 1, 2, 3 | special map buildings; stored only |
| 218 | 6 | 1, 2, 3 | special map buildings; stored only |

Do not treat a technology as implemented merely because its costs, button, prerequisite and effect data are present. Resources 215–218 are consumed by eight buildings listed in the installed resgen.txt, none present in either production roster or the 20 current map object inventories; see RESOURCE-PRODUCERS.md. Their special-map behavior remains unimplemented. Other unresolved resources still need a source-behavior specification, engine adapter and runtime verification. See faction-mechanics-audit.json for command values and per-faction details.
