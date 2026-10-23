# Astromech Repairs: experimental XS adapter

Source technology 663 (Rebels) applies effect 682. Its first command enables resource 212; its second restores Nova mining productivity resource 214 to 1. The second command is already translated and must remain intact when implementing the first.

Expanding Fronts cheatdll/processunit.cpp, regenFix at hook 0x55A974, permits regeneration for source classes 43 (bomber), 48 (fighter) and 59 (air transport) when resource 212 is positive. Do not broaden that selector to every aircraft class without further evidence.

The original regeneration routine at 0x55A97C reads owner resource 49 as the interval, adds elapsed world time to the unit accumulator, and adds one hit point for each elapsed interval while clamping to maximum HP. Both source factions initialize resource 49 to 2. The source editor label for that resource is misleading; the executable is the relevant evidence. The routine skips units below one HP and units already at maximum HP. Its stored accumulator persists rather than being reset at full health.

A future native regeneration-rate adapter should preserve the existing effect's Nova command, use the exact source classes and account for already-regenerating heroes and unit upgrades. Thirty HP per minute is the average rate implied by this interval, but matching the average alone does not verify the source's discrete recovery behavior. The draft now includes an XS adapter for normal-roster aircraft, consuming isolated resource 2212 and recovering one HP per two accumulated seconds. It retains partial timer progress at full health, ignores units below one HP, and preserves the existing Nova command. Source eligibility, resource/class mappings and absence of innate hero regeneration are checked during generation. One-second sampling can shift phase; scenario-only aircraft, runtime compilation, save/load and performance remain unverified.

The combined installed XS script passes standalone XS Check 0.2.29 syntax/type checking, with identical staged/package/install hashes (faction-xs-validation.json). This does not replace DE engine compilation or runtime verification.
