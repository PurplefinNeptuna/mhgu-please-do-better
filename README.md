# Please do Better

Marks verified extra luck reward slots with a pulsing gold border and sparkle.
Natural luck is the default; optional Force Miraculous Luck reproduces the
wiki's two-site cheat without changing equipped skills.

Current local release: **r19-savehint**, READY_TO_DISTRIBUTE and unpublished.
[Installation and settings](DISTRIBUTION_README.md); [status and payload hashes](DISTRIBUTION.json).

Switch development candidate: **r23-reward-pages**, with a 1x to 5x
integer slider for all player reward pages; the Palico page is excluded. [Candidate installation/settings](CANDIDATE_README.md) and
[implementation/manual checklist](docs/DOUBLE_QUANTITY.md). The user reported
r20 working well; its matching Eden log and installed hash are recorded in
[the r20 receipt](docs/R20_RUNTIME_RESULTS.json). The r19 release remains pinned.
The user also reported r21 working very well at the recorded 5x setting;
[the r21 receipt](docs/R21_RUNTIME_RESULTS.json) retains that scope.
The user confirmed r22 working; [the r22 receipt](docs/R22_RUNTIME_RESULTS.json)
records the tested 3x setting and its limits. r23 expands the page scope and
has no gameplay acceptance yet. The required INI header remains unchanged.

## Development and evidence

Use [DEVELOPMENT.md](DEVELOPMENT.md) for pinned inputs, build/test/package/export
commands. [Runtime evidence](RUNTIME.md) retains the version and limits of user
reports. [THIRD_PARTY.md](THIRD_PARTY.md) records development provenance;
[DISTRIBUTION_NOTICES.md](DISTRIBUTION_NOTICES.md) supplies release credits.


R19-savehint changes only the save-success string. Host persistence, 2,122
ARM32 and 100,511 runtime/gateway checks, plus native observation/display/
geometry/highlighting fixtures passed. No fresh game run was performed.
[SAVE_HINT_VALIDATION.json](docs/SAVE_HINT_VALIDATION.json) pins the payload.

Technical references: [implementation and state audit](IMPLEMENTATION.md),
[native research](RESEARCH.md) and [remaining gameplay coverage](MANUAL_TESTS.md).
Disable the legacy Great Luck cheat for an authorized test; startup rejects
prepatched/conflicting code. The second check's broader role remains incompletely
traced, and Ryujinx compatibility remains untested.
