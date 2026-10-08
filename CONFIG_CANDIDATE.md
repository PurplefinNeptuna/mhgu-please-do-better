# Primary config candidate

R17-config1 saves only `savedata:/please_do_better.ini`. Existing backup files are ignored and left untouched. Saved values, defaults and the explicit Save settings control are unchanged. Write, readback or commit failures retain the session choice and report failure; they do not promise recovery of previous disk contents.

Host and compiled evidence are recorded beside the candidate. No new gameplay run is claimed. Accepted r16 remains the current distribution.

## Release promotion, 2026-10-08

r17-config1 is now READY_TO_DISTRIBUTE following the user's tested-Eden
confirmation. The preceding candidate-stage notes describe preparation before
that report. The candidate NRO is preserved unchanged; the immutable release
lives under `build/please-do-better/releases/r17-config1/`. Forge remains LOCAL_ONLY.

## Version marker removed, 2026-10-08

r18-config2 writes only actual preference fields. Existing `version=2` configs
remain readable; the next explicit save drops the marker. Primary-only storage
and backup non-access remain in place. The previous delivery is preserved under
`backups/config-no-version-20261008/`. Validation is recorded in
[CONFIG_WITHOUT_VERSION.json](docs/CONFIG_WITHOUT_VERSION.json); no fresh game run
is claimed for this revision.

## Standalone save hints, 2026-10-08

r19-savehint replaces the Better Input location reference in save feedback
with this plugin's INI filename and MHGU's save folder. Only the success
string and public instructions change; storage and config behavior are retained.
[Validation](docs/SAVE_HINT_VALIDATION.json) records the checks and runtime scope.
