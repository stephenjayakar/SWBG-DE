# Final-age crash investigation

Status: unresolved. No crash fix installed or released. Do not launch DE for this investigation while the user is playing.

## Recorded evidence

- The reported September 16 online matches used `SWGB-DE-Factions-Publish`, published checkpoint `f8e11f94bfa7574c5d90300ceeec8aec245d8b6a`, with two human players and no AI. They did not use the local Classic AI `.4` dataset.
- The 18:06 recording starts in Castle Age. Empire requests technology 3 (Tech Level 4) at 467008 game milliseconds. The recording ends at 505814: this establishes a request, not successful completion. The base research time is 200 seconds. Other building/research activity was in progress.
- The 18:15 resumed recording ends again. Both available dumps fail at executable RVA `0xBA4446`, reading address `0x18` through a null pointer. This is a different location from the previously investigated TIE movement crash.
- The 18:18 recording header explicitly says Imperial Age (`start_age=5`), two humans, Infinite resources, the same published dataset and Savannah map. It has no usable body metadata. This supports the user's report that a direct Imperial start failed.
- The following 18:21 recording starts in Castle Age (`start_age=4`), otherwise matching those settings, and contains about 30.7 game minutes before resignation.

The modern recording parser fails in later header fields and misreads some action formats. These settings come from the earlier parsed fields and embedded map description; do not trust its malformed selected-object IDs.

## Static checks and diagnostic candidate

Age-effect upgrade closures for both factions have valid referenced unit and graphic records. Three missing assets belong to an underwater dwelling family appearing in each age's closure; this does not isolate a final-age cause. These checks do not simulate all automatic research or native state transitions.

Imported buildings lack DE-only research/upgrade indicator graphics. `toolkit/faction_building_state_graphics.h` provides an **explicit diagnostic candidate**, not an automatic builder step. It fills three missing graphic fields with one valid invisible graphic. The exporter modes are:

```
portdat building-state-report CURRENT.raw REPORT.tsv
portdat repair-building-state-graphics CURRENT.raw CANDIDATE.raw NATIVE.raw
portdat audit-building-state-graphics CANDIDATE.raw RESTORED.raw CURRENT.raw
```

The generated candidate changes 9363 fields across 3121 building records and adds graphic 29109. Restoring just those fields and removing the added graphic produces bytes identical to the original input. Reports and scratch candidate are in `work/age-crash`.

**This does not establish the crash cause.** The fault reads a pointer at decoded object offset `0x838`, then a signed short at offset `0x18` of that pointer. The dump does not contain the relevant heap object, and these fields have not been identified. A unit reference is also plausible. Do not describe the candidate as a confirmed fix, integrate it into routine packaging, or publish it on the basis of a serialization check.

Next investigation should isolate final-age automatic effects and building transitions using the published dataset and the direct-start evidence. Native A/B validation remains necessary after a justified candidate is ready and the user can run it.
