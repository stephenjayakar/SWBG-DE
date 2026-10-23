# Map conversion coverage

Current installed pack: 20 layouts. Savannah remains included. Arena and Motherlode were added in this follow-up. Nova Lake and Nova Assault now retain their original special Nova placement blocks with native gold substituted; Arena retains its original barrier placement block with native stone walls substituted.

Source IDs are recorded in map-manifest.json and each RMS header. The source files are the installed Expanding Fronts gamedata_x2 DRS entries. These adaptations retain land/terrain/connection structure and substitute native DE terrain. Standard starting units and most resources remain the prototype distribution; fauna and environmental art are not ported. Engine generation, resource reachability and wall layout still require match tests. Presence of a source placement block does not prove its generated result in DE.

Remaining entries inspected:

| Source | Map | Remaining work |
|---|---|---|
| 54208 | Fortress | Preserve starting fortifications, farms, houses, defenses and training buildings rather than discard the map identity. |
| 54213 | Planets and Moons | Space terrain and air-transport starts require a supported travel model. |
| 54214 | Space Mass | Same space/travel dependency. |
| 54215 | Space Satellites | Same space/travel dependency. |
| 54216 | Forced Deployment | Preserve its deployment rules and source resource/start behavior. |
| 54227 | Raiders | Preserve commander/worker starts and map-specific gameplay. |
| 54228 | Team Space Satellites | Space/travel dependency plus team placement tests. |
| 54229 | Blind Random | Dispatches source map includes, including unsupported space maps; rebuild only after its constituent maps work. |

The source pack has no extracted entry 54224. No map is claimed engine-verified yet.
