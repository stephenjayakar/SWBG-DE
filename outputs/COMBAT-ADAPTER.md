# Combat conversion checkpoint

The full-faction draft now explicitly sets DE's splash-damage multiplier to 1 for imported combat-capable records. The older SWGB format has no field for it; a direct schema conversion initialized it to zero. Native DE siege records use an explicit positive multiplier for normal proportional area damage.

The source area-attack routine at 0x55DCF0 compares target blast defense against the attack threshold, checks range/collision and accuracy, then calls the ordinary attack-modifier and damage routines at 0x55DF48–0x55DF7D. It does not apply a separate reduced splash multiplier. The conversion supplies that missing DE field while retaining the source attack and armor tables, radius and other existing fields.

Independent checks cover 12,536 combat-capable records across Gaia, Empire and Rebels, including 885 records with nonzero splash radius. These counts include unused, projectile and scenario records; they are not counts of playable unit types. Restoring only this field makes the entire new serialized DAT byte-identical to the previous draft. The new DAT also reads back byte-identically.

This is not a complete combat implementation or an in-engine damage test. Source blast levels and DE flags differ: for example, source troops commonly have level 4 with zero splash radius, while DE now uses bit 4 as a friendly-fire option. The source also filters allies and applies special pummel/aircraft logic in its executable. Those rules need their own adaptation and verification. No blanket renumbering of blast levels was applied here.

References: the pinned AGE source in `AGE_Frame/Units.cpp` documents the native multiplier field; the [official modding notes](https://support.ageofempires.com/hc/en-us/articles/15607286588948-Return-of-Rome-Mod-Updates) describe explicit blast damage; [DE update 87863](https://www.ageofempires.com/news/age-of-empires-ii-definitive-edition-update-87863/) documents the friendly-fire flag.

Validation artifacts: `faction-blast-validation.json` and `toolkit/check_faction_blast.py`. The `audit-faction-blast` tool command restores only the allowed field for the byte comparison. Stable 0.0.1 is unchanged; the updated full-faction package is installed as separate data/media mods but is not enabled or engine verified.
