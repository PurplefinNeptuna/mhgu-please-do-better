# R13 native full-texture downsample observation

The matching r12 log and installed hash confirm the clipping fix: 15,360 exact
slot captures published geometry, with zero clip rejection, while drawing was
suppressed by a texture mismatch. The reward source texture was 0x4E93D350;
acquired presentation images alternated independently. See the preserved log,
screenshot and 129 candidate hashes in work/please-do-better/r13-report/.

Original main+0xBBFB08 and main+0xBBFB44 are the same-size native whole-texture
downsample branches for equal and differing surface formats.
Its displaced MOV r1,r11 / MOV r2,r10 are replayed exactly; the callback load,
MOV r0,r8 and BLX remain original. The NVN initializer at 0x865408 loads the
string nvnCommandBufferDownsample and stores its callback through GOT entry
0x18418F8, also loaded by the executor. Original instructions and the initializer
receipt establish the mapping; no emulator address is hardcoded.

R13 adds two guarded fixed gateways and two fixed immutable transfer snapshots,
indexed by native execution frame. It accepts only non-subresource surfaces with
matching full extents and the original branch's format relationship, the native sample encoding for this branch, exact
command-buffer/callback identities and destination equal to the acquired image.
The executor frame is producer frame XOR parallel mode; serial is producer
serial minus parallel mode. Each route retains owner, screen fence, source,
destination and extent. A draw requires all these to match its exact geometry
and presentation. Direct-to-image draws remain supported. Unobserved offscreen
sources and unsupported copy/composition routes stay unmarked. No inferred
screen positions or general texture bypass is introduced.

The observer publishes before the untouched void NVN command callback. These
are CPU enqueue-path observations; GPU completion and visible alignment still
require gameplay confirmation. Native queue/presentation ordering and original
frame selection are checked separately. Snapshot contention suppresses the
affected frame. An installation failure rolls back the rendering group while
retaining safe working forcing and reward observation. These gateways need no
additional arena, TLS slot, context or heap allocation.

R12 scissor handling and bounded telemetry remain; transfer details go only to
Eden's log through Forge. The normal panel stays compact. Natural luck, no luck,
forced mode/live toggles, repeated grids, collection/transitions, cursor/animation
alignment, Eden multicore/translation and Ryujinx remain pending. No installation,
activation, launch, existing save/settings edits, push or publication is included.
