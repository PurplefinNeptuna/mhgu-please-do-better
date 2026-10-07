# Handoff: Forge menu corruption while damage numbers are alive

Recorded 2026-10-05. Workspace: `/mnt/storage2/Programs/MHGU_Modding`.
This is a documentation handoff; no renderer fix or deployment has been made.

## User report and current finding

The user reports that, with damage numbers enabled and Forge's ImGui menu open,
spawned numbers look corrupted and the menu's visuals also corrupt temporarily.
The corruption ends when the numbers despawn. They asked whether this is an
expected limitation of Wilds style. It is a bug, not intended behavior.

Source inspection found a definite multi-draw-list offset defect in Forge's NVN
renderer. It is the leading explanation for this report. A corrected build has
not yet been tested in-game, so do not claim the report's cause is fully proven
or that this is necessarily the only renderer defect.

The renderer copies all draw lists into one contiguous vertex buffer and one
contiguous index buffer, advancing the copy destinations after each list.
During drawing, however, it uses only each command's list-local `IdxOffset` and
`VtxOffset`. It never adds the cumulative sizes of preceding draw lists.
Commands from later lists consequently address the wrong geometry, potentially
with a different texture binding.

Damage numbers use ImGui's background draw list. Opening Forge adds a separate
window draw list. The appearance and disappearance of that extra background
geometry fits the reported lifetime-dependent corruption. This defect is not
specific to the open font, star glow or Wilds palette; Classic uses the same
background-list path and may also expose it. That last point is an inference,
not a user-confirmed Classic reproduction.

## Relevant files

| File | Starting point |
| --- | --- |
| [NVN renderer](../tools/forge-local/source/forge/graphics/imgui_impl_nvn.cpp) | `ImGui_ImplNVN_RenderDrawData`; lines 869–875 concatenate lists, 885 onward draws them, 916–921 omit cumulative offsets |
| [Forge menu](../tools/forge-local/source/forge/graphics.cpp) | `Graphics::render`: menu window ends before `forge_plugin_onImGuiFreeRender()` |
| [Damage renderer](../mods/damage-numbers/src/capture.cpp) | `capture_render`, near line 464: background draw list with balanced clip push/pop |
| [Damage callbacks](../mods/damage-numbers/src/plugin.cpp) | `forge_onImGuiFreeRender` invokes damage rendering; `forge_onImGuiRender` handles settings |
| [Damage cosmetics](../mods/damage-numbers/src/cosmetics.cpp) | Registered open font and procedural texture, measured glyphs and draw calls |

The backend also advertises `ImGuiBackendFlags_RendererHasVtxOffset`, so both
the per-command vertex offset and the cumulative list vertex offset matter.
Line numbers describe the inspected checkout and may move after edits.

Renderer source SHA-256:
`4d403d2b72768689e5899a28d696f87a49c01c8cd1982f6c866cea4049010808`.

## Proposed fix

Keep this as a Forge backend correction. Preserve the accepted damage-number
appearance, animation, source filtering, capture hooks and settings. Hiding
damage while the menu is open would mask the defect rather than fix it.

Track cumulative index and vertex counts through the **drawing** loop, not
just through the copying loop. Conceptually:

```cpp
size_t global_idx_offset = 0;
int global_vtx_offset = 0;
for (const auto drawList : drawData->CmdLists) {
    for (const auto& cmd : drawList->CmdBuffer) {
        // Existing callbacks, clipping and texture binding remain here.
        // For a normal visible command, use:
        index_address = idx_buffer_address
            + (global_idx_offset + cmd.IdxOffset) * sizeof(ImDrawIdx);
        base_vertex = global_vtx_offset + cmd.VtxOffset;
        // Pass these to DrawElementsBaseVertex.
    }
    global_idx_offset += drawList->IdxBuffer.Size;
    global_vtx_offset += drawList->VtxBuffer.Size;
}
```

This is an implementation sketch, not a complete compilable patch. Match NVN's
actual argument types. Advance cumulative counts once per list even if commands
are clipped or handled by callbacks. Keep existing command-local offsets and
texture selection; do not replace them with just the global values.

## Preserve the tested baseline

Read [AGENTS.md](../AGENTS.md), [Forge branch notes](FORGE_LOCAL_BRANCH.md),
[baseline metadata](FORGE_LOCAL_BRANCH.json),
[plugin guidelines](FORGE_PLUGIN_GUIDELINES.md) and
[prior acceptance evidence](FORGE_RUNTIME_EVIDENCE.md).

- Maintained Forge repo: `tools/forge-local`, branch `codex/forge-legacyctx14`.
- Inspected clean HEAD: `b8921fa3bbe35bbbafb11ccc489d5f1c6aa24a2d`.
- Base Forge 1.4.1: `0f1672e646146b39ff2941cc5b7bef581c8dac5a`.
- Installed Forge `forge-patched/exefs/subsdk9` SHA-256:
  `374684063adb939b389f0e4d1c8766c09e52339bfe9eaedadd4a8f44635252a7`.
- Installed Better Input NRO SHA-256:
  `84b1549aabda3cfd4228e02a9516d16d8d142787b4589191bb84c39cdbcba872`.
- Installed damage-number r15 NRO SHA-256:
  `7c112c6bf497207f8bdf475687bab3b0056c0726ac4db1707db8f8adc01e07da`.

These installed hashes were freshly read and matched on 2026-10-05. Recheck
before work; hashes identify bytes, not runtime activation. Eden's title load
root is `~/.local/share/eden/load/0100770008DD8000/`.

Use an isolated trial checkout/output directory for this renderer change,
retaining the accepted branch/artifacts and legacy-context compatibility patch.
No upstream upgrade is needed to address the identified defect. Preserve
`forge_hook_legacyCtx14`, its shared arena, ARM32 ABI and Better Input import.
Do not leave the only copy of a fix inside ignored `tools/`: retain a tracked
replay patch and reproducible trial recipe/provenance, then commit locally.

The discontinued combined-package builder was removed. The maintained loader
recipe is `scripts/forge_patched.py`; read its source pins and current baseline
gates before adapting an isolated renderer trial.
Use the recorded existing devkitPro/container setup and inspect ARM exports.
Several plugin builders pin the old Forge source revision and installed hash;
plan explicit baseline updates after validation rather than bypassing gates.

Keep rollback packages in workspace `backups/`, outside Eden. The handoff itself
does not authorize installation, activation, game launch, save edits or emulator
setting changes. Follow the user's instructions in the fixing session for those
steps. Recheck `git status`; unrelated modern-controls work was present.

## Focused verification

1. Add a meaningful multi-list regression fixture. Prefer actual ImGui output
   with a background number plus one or two UI windows and mixed font/sprite
   textures. Exercise the renderer's addressing logic and verify that the
   second/third lists address their own concatenated buffer regions. Cover
   nonzero command-local offsets and a skipped/clipped command; retain a
   single-list case. Ensure the old implementation fails this fixture.
2. Build the isolated ARM32 Forge trial, inspect exports/compatibility and
   record source, patch and binary hashes. Verify the damage-number NRO and
   Better Input payload remain unchanged. Preserve fresh Eden logs before
   any authorized restart. Keep the DTI dumper removed during normal play.
3. After authorized trial installation, ask for only a brief real-game check:
   land a few hits with Forge open; let the numbers expire and land a few more;
   close/reopen the overlay and confirm numbers, menu and Better Input controls
   remain normal. Briefly switching Wilds/Classic can check the shared path.
   No exhaustive weapon/ammo/crit suite is needed for this renderer-only fix.

The damage r15 host checks (919), compiled ARM32 checks (324) and real-ImGui
preview passed previously. They **did not exercise Forge's NVN GPU submission
with a menu window and damage background list together**. Those results do not
prove this case works. Keep host/compiled results separate from the user's
runtime confirmation. If corruption persists after correcting offsets, retain
the fresh evidence and investigate further rather than marking it resolved.

## Suggested prompt for the next session

> Read `docs/FORGE_IMGUI_DAMAGE_CORRUPTION_HANDOFF.md` and fix the identified
> Forge multi-draw-list buffer-offset defect in an isolated trial. Preserve
> Better Input compatibility and the accepted open-font damage appearance.
> Add the focused regression, build and stage a reviewable trial with rollback
> and recorded hashes. Keep unrelated changes and installed files intact
> unless I authorize deployment.
