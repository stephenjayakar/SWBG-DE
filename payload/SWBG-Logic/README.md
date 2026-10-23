# Experimental faction draft

This is an experimental development build, not a tested release.
Stable 0.0.1 is unchanged. This dataset exposes Empire and Rebels in its own
three-entry civilization roster (including Gaia); it does not add slots to
the normal DE roster. Use only the matching SWGB Factions maps and SWGB Land AI.

Includes source unit/technology data, both sprite resolutions, source sounds/music,
icons, English text, technology panels and original map object rules.
Static conversion and reference checks pass. Engine loading, UI, audio playback,
AI and full gameplay have not been verified. Aircraft, shields,
garrisoned power droids and other executable-specific mechanics remain unfinished.
Power uses an experimental native aura with unverified stacking/placement behavior.
Core upgrades retain their aura at every tech level; enable Building and Aura
Range Indicator in DE options to see the configured power radius.
Music includes shared SWGB/EF streams and Empire/Rebel opening themes. Use
Standard soundtrack playlist for faction themes and source stream order.
Nursery food is implemented by an experimental XS script; engine compilation and income are unverified.
Four missing optional fishing overlays are omitted; seven sprite files use fixed
paint for invalid player-color pixels; one flying animation repeats static poses.

Use toolkit/install_factions.py to install separate data and checkbox media mods.
Do not treat this combined assembly folder as the final local-mod layout.
The draft is for local use with the user's installed source games. It has not
been published. See ../FACTION-PORT.md and ../FACTION-STATUS.md for details.
