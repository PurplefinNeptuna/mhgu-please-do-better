# Please do Better

Marks verified extra luck reward slots with a pulsing gold border and sparkle.
Natural luck is the default; optional Force Miraculous Luck reproduces the
wiki's two-site cheat without changing equipped skills.

Current local release: **r23-reward-pages**, READY_TO_DISTRIBUTE and unpublished.
[Installation and settings](DISTRIBUTION_README.md); [status and payload hashes](DISTRIBUTION.json).
The 1x to 5x integer slider scales player reward pages and leaves the Palico page
unchanged. The primary INI requires `[PleaseDoBetter]`; old formats use defaults.

The user approved distribution of the unchanged r23 candidate. Its installed
hash and fresh Eden log confirm loading; [the release receipt](docs/R23_RELEASE_APPROVAL.json)
records the approval and remaining manual/platform limits. The original r23
candidate stays preserved, and r19's delivery and source guides are retained in
the verified rollback archive recorded there.

Earlier r20/r21/r22 reports keep their original payload and coverage scope:
[r20](docs/R20_RUNTIME_RESULTS.json), [r21](docs/R21_RUNTIME_RESULTS.json),
[r22](docs/R22_RUNTIME_RESULTS.json).

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
