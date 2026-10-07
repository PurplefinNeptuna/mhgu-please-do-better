# R10 acquired texture identity and stable diagnostics

## Confirmed R9 failure

The supplied untouched reward grid reports sixteen generated slots, four extras,
four bound slots, zero highlights and zero capture/mapping faults. The latest
Eden master-10bcd2d849 log records safe r9 startup, followed by rejection class 3:
raw surface `4E97E140`, default sentinel `4E2D2090`, sampled resolved surface
`4E97E090`. The user reports this last value alternating rapidly. The exact
installed r9 NRO is `eb26371244a7cc74e1f7f3144983993a340a8e0f2029f37890eebba9dd1eb265`.
The shader `D7376B18` has verified reflected bindings
`2D7 2D6 16F 2DB 2DE 3CA`; shader support is not the reported rejection.
Copied log, screenshot and 96-file preservation receipt are under
`work/please-do-better/r10-report/`.

## Original executable evidence

Offsets below are main-relative, checked against the pinned offline executable.
At `BC0E98`, the render-target binder resolves the default sentinel through
`sRender+389CC -> object+204 -> surface`. The original `BC1148..BC11BC`
fragment loads `surface+10 -> GPU wrapper+3C` as the NVN texture and
`surface+14` as the texture view for CommandBufferSetRenderTargets. Descriptor
address equality is therefore stricter than image equality. The fragment fixtures
execute these original bytes for sentinel, resolved and alias descriptors,
multiple image identities and default/nondefault views.

`86A28C` acquires a window image. The original `86A2E8..86A304` fragment
loads the resource pointer at `owner+4740+180+index*4`, records it at `48CC`,
and records the index at `48D0`. The native window constructor `869ECC`
creates three resources, stores them at window+180/184/188, and supplies
each resource+3C in its separate NVN WindowBuilderSetTextures array.
Constructor fragments execute each of these three conversions. The native
surface constructor `B07B18` selects a null view for level zero without a parent
(the window route); other levels or incompatible parents create explicit views.
Original-instruction fixtures verify this distinction. The pinned NVN header defines Window as
384 bytes, putting the three-entry resource pointer table at `48C0/48C4/48C8` in the
game owner, beyond the opaque Window. `86A30C` passes queue, window and exact
index to presentation. Forge's customQueuePresentTexture renders to its cached
swap-chain texture at that same index before calling original presentation.
Read-only Ghidra traces: `highlight-research/r10-surfaces/` and
`highlight-research/r10-surface-bind/`, `r10-window-init/`,
`r10-texture-create/`, and `r10-surface-view/`, under `work/please-do-better/`.
Existing frame index, native parallel serial, epoch and clipping guards remain.

## Implementation and limits

Capture the draw texture in the bounded geometry snapshot; compare it with the
validated acquired-image snapshot at presentation. Sentinel geometry resolves
through the native current default image at that boundary. Validate cached index,
table entry and nonzero cached image. Reject unrelated images, unreadable fields
and nondefault texture views. The overlapping fields are explicit: owner+48CC equals sRender+389CC, and
owner+48C0 equals sRender+389C0. They are resource pointers, not NVN textures.
No new gateway, arena or TLS allocation is needed.
Only immutable identities are used when rendering; no live node is dereferenced
from a deferred rejection. Keep the first rejection for each live screen fence
readable, while retaining all rejection counts internally. New screen fences
permit new details. The diagnostics accurately say "first suppressed draw".

Compiled fixtures demonstrate drawing for equal texture identity, including
alias descriptors and alternating acquired images, and suppression for mismatched
images. These CPU fixtures do not prove GPU compositing or that the user's raw
target texture equals the acquired image. If it belongs to a separate composite
pass, the guard must still suppress it until that route is traced. No guessed
coordinates or dimension-only target acceptance is used. Actual gold visibility,
alignment, natural luck, repeated screens, Eden parallel/multicore behavior and
Ryujinx compatibility remain pending. Cache success does not prove translation
freshness. No installation, activation, launch or real save/settings edits occur.
