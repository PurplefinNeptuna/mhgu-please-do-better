# Mod distribution standard

`mods/<mod>/DISTRIBUTION.json` is the authoritative distribution record for every
directory under `mods/`. All current mods are registered. A new directory without
this record fails the workspace check.

## Status meanings

| Status | Meaning |
| --- | --- |
| `DEVELOPMENT` | Research or a candidate; distribution is not approved. |
| `LOCAL_ONLY` | Local tooling, a dependency or an integration; no standalone distribution release is approved. |
| `RETIRED` | Standalone output is superseded; tracked originals stay in Git history and current workspace trees are removed. |
| `READY_TO_DISTRIBUTE` | Approved local delivery exists and passes the complete package check. |
| `PUBLISHED` | The same delivery checks pass and an actual HTTPS download URL and publication date are recorded. |

Test coverage is separate from distribution status. Record static evidence,
manual evidence and remaining limits accurately. User approval to distribute
does not turn an unperformed gameplay test into a passing result. Packaging
never installs, activates, launches, pushes or publishes.

## Required layout

```text
mods/<mod>/DISTRIBUTION.json
build/<mod>/releases/<version>/
    <mod>-<version>[-variant].zip
    <package-name>/
        romfs/...
        exefs/...
        cheats/...
    README.md
    NOTICES.txt
    release-manifest.json
    SHA256SUMS
```

Only the applicable runtime directories are present. The ZIP contains exactly
one named emulator package folder, with only declared runtime files. No extra
title-ID/dump nesting, readmes, notices, manifests or tests go inside that folder.
Its unpacked bytes must match the ZIP and pinned payload hashes. Existing
package names may be preserved for update compatibility.

README, combined notices, manifest and checksums always sit beside the ZIP.
Every ready or published release's `README.md` must be strictly user-facing.
Cover what the mod does, requirements, installation/update/removal, controls or
settings, compatibility and actionable known issues. State testing limits briefly
when they affect compatibility; keep build commands, research, offsets, ABI/hook
details, test counts, internal evidence, approval history and workspace paths in
developer documents or the manifest. Use a dedicated release README source when
the source repository's README also covers development. Review the release
README for this audience before claiming readiness; a checksum check alone does
not establish that its prose is user-facing.
Additional support files, such as `COMPATIBILITY.md`, must be declared. Share
the ZIP with its notices. `SHA256SUMS` covers every file in the delivery except
itself. The manifest records identity, target, approval, publication, exact
runtime inventory, support hashes, evidence hashes and coverage limits.

Runtime bytes and ZIP bytes are immutable within a version. A changed runtime
requires a new version. Documentation, evidence references and publication
metadata can be refreshed with `--refresh-support` only after the runtime and
archive match; the packager first copies and verifies the old delivery under
`backups/<mod>/distribution-support/`. Unknown files and symlinks are rejected.

Keep only the current registered version under `releases/`. Archive superseded
deliveries with hashes under `backups/`; never delete rollback inputs. Candidate
ZIPs belong under `build/<mod>/candidates/` and do not establish readiness.
The full checker rejects ZIPs elsewhere under `build/`. Existing controls and
loader candidate ZIPs were relocated byte for byte; obsolete combined-loader
and cheat bundles were archived. Their relocation hashes are retained in
`backups/distribution-standard-20261006/legacy-candidate-paths/`.

## Commands and enforcement

```bash
# Register a future mod before development.
python3 scripts/mod_distribution.py init new-mod --kind plugin

# Run that mod's own build/static checks first, then package approved pinned inputs.
python3 scripts/mod_distribution.py package new-mod

# Refresh support files while preserving this version's runtime and ZIP bytes.
python3 scripts/mod_distribution.py package new-mod --refresh-support

# Required before claiming readiness, committing distribution work or sharing.
python3 scripts/mod_distribution.py check

# For a source checkout without the ignored build inputs; proves no ZIP readiness.
python3 scripts/mod_distribution.py check --source-only

# Install the tracked commit gate in a clone with no custom hook path.
git config --local core.hooksPath .githooks
```

The full check discovers every mod, rejects absent/contradictory records,
rebuilds the expected deterministic ZIP in memory, checks CRC/inventory/member
bytes, requires exact on-disk support/manifest/checksums, and checks that only
the registered current version remains under `releases/`. It does not run a
game. `--source-only` is for source review; it cannot establish readiness.

The tracked `.githooks/pre-commit` checks the actual staged source records and
support files, then runs the full package and staged whitespace checks. A new
mod whose distribution record was left out of the commit is rejected. The hook
is installed in this workspace. Git does not automatically transfer
hook configuration to another clone; install it there using the command above.
Preserve and integrate existing custom hooks rather than replacing them.

The three active release recipes delegate delivery to this shared packager
after their own validation gates. Other local/candidate recipes can continue
staging development files, but must use the same record, packager and full
check before becoming a distribution. Mod-specific `RELEASE.json` and runtime
release flags must agree with `DISTRIBUTION.json`.

The three current ready records provide concrete examples of the required
fields: version, package/archive names, approval, target, limitations, readme,
notice sources, pinned runtime source paths/hashes, and static/manual evidence.
Fill these fields when promoting a future mod. The `init` command starts it at
`DEVELOPMENT`; creating a candidate ZIP alone does not promote it.

## Current migration

Modern weapon controls r10, Key Quest Markers r1 and Damage Numbers r17 are
ready to distribute. Other mod records explain their development, local-only
or retirement status. This does not promote dependencies/prototypes to releases.

The 2026-10-06 migration preserves all runtime payloads. Quest Markers r1 gains
the standard `key-quest-markers/` package wrapper, so its ZIP hash changes; its
NRO does not. Controls and damage-number ZIP bytes remain unchanged. Previous
delivery metadata, the flat quest marker ZIP and superseded r16 delivery are
preserved with hashes in `backups/distribution-standard-20261006/`.

Retirement removes the component from the current workspace after its tracked
state is committed. Required shared code, tests and build inputs first move to
maintained locations. Remove obsolete recipes, staging, working files and backup
copies; Git history retains tracked originals. Current catalogs list remaining
mods only. Installation directories are outside workspace cleanup scope.

## Default source layout

Every future plugin, resource mod, cheat and tool is a self-contained source
folder under `mods/<name>/`. `init --kind` scaffolds its layout and DEVELOPMENT
record without replacing an existing directory. Each mod owns its source,
recipes, tests, dependency pins, notices and mod-local `build.sh`.
Root scripts coordinate the workspace; they are not required by an exported
source repo. [Standalone workflow](STANDALONE_MODS.md) covers local inputs and
allowlisted source export. Source publication readiness and runtime delivery
readiness remain separate. Settings-only UI and quiet logs are release rules
for gameplay plugins.
