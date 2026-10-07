# R14 independent gold overlay

The matching r13 screenshot and latest Eden master-10bcd2d849 log show eight
generated rewards, four extras and zero visible markers. Installed r13 SHA-256
matches the candidate: 026e0af2bcfd1b5d04170ebac454e830e38f8887e79c43f55567834a8f178932.
All startup groups passed. The final bounded trace has 6,720 geometry publications,
zero clip/identity/mapping faults, zero downsample gateway hits and 6,716 image
gate rejections. Copies of the log/screenshot and 140 prior candidate fingerprints
are in work/please-do-better/r14-report/. These are user-run CPU observations;
no r14 visible success is claimed.

## Draw our own primitives through Forge

Damage Numbers uses forge_onImGuiFreeRender, igGetBackgroundDrawList_Nil and
its own cosmetic primitives after projecting native positions. It does not
require the game's intermediate texture to equal the acquired image. Please do
Better already owns its border/sparkle primitives; its texture gate unnecessarily
prevented drawing. A new raster sprite would have been blocked by that same gate.

Forge's customQueuePresentTexture in source/forge/graphics.cpp selects the actual
queue, creates an ImGui frame, calls the plugins' free-render callbacks, submits
ImGui draw data to the cached texture at the native presentation index, and then
calls original presentation. That loader path owns our primitive's destination.
R14 draws into it using the native slot geometry. No game sprite/texture is reused
or changed. The procedural gold shape needs no external asset or texture upload.

## Placement and retained checks

Original texture vertex construction and the pinned Maxwell GUI position shaders
provide model/global transforms. The supported XY/W=1 shader math projects the
exact slot-frame perimeter into the selected full, zero-origin framebuffer
viewport. Runtime reads that geometry and resolved native clip; it has no fixed
slot coordinates. The r13 trace's four separate duplicate-capable slot bindings
project to x=1596/1662/1728/1794, y=207, width/height=54 on the reported 1920x1080
viewport. Compiled fixtures replay those transforms, draw all four perimeters
and sparkles with a different UI source texture, and retain index/node identity.
Those pixels are fixture evidence, never runtime position constants.

Retain exact batch/array/index/node/content provenance, owner, native executed
frame/serial (direct and one-frame parallel), presentation callback authorization,
viewport dimensions, successful submission, known shader, full surface/view,
clipping, screen fence, immutable publications and overflow suppression. Unknown
shaders, reduced/offset viewports, nondefault views, stale frames and empty/changed
slots remain unmarked. No additional RNG, collection tracking or item matching.

Remove r13's two unused downsample hooks and transfer snapshots. The rendering
group again contains only the guarded geometry/presentation pair; forcing and
reward observation remain independently available on safe rendering failure.
The existing full-state gateways and NZCVQ-only restore are unchanged. One pooled
4KiB arena, one TLS slot and fixed capture limits remain. No APSR_g dependency.

Verbose diagnostics go to Eden's log with the existing bounded sampling policy.
The plugin panel remains compact and closed by default. Local compiled draw calls
validate CPU eligibility and coordinates; visible borders, cursor/animation
alignment, natural positive luck/no luck, repeated grids, collection/transitions,
mode/settings behavior, Eden multicore/translation and Ryujinx still need gameplay
coverage. Successful cache calls do not establish CPU translation freshness.
No installation, activation, launch, existing save/settings edits, push or
publication is included. DEVELOPMENT continues.
