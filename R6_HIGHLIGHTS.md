# R6 gold highlight evidence

Prepared 2026-10-07. No game, GPU or emulator was launched. R4's user report
supports forced attribution (eight generated/four extra slots), not R6 alignment.
R1-r5 bytes remain preserved. This candidate implements gold drawing; natural
positive-luck and forced gameplay alignment require the manual checklist.

## Frame identity

The original English `result_eng.arc` SHA-256 is
`c2973af8653ec7bb9e60e79fe930c266f67eb799804837b7df34a60099f5ab12`.
The read-only extractor validates ARC 17, zlib bounds and every entry size.
`reward.gui` uses 24-byte animation records and 36-byte object records; scalar
property offsets are byte offsets. Its `bg`, `bg_2` and `bg_3` animations contain
actual 36x36 frame textures, separately from the 32x32 icon nodes. Texture 11's
frame atlas rectangle is (280,0,316,36), with a (280,0,318,38) variant.

Native list group stride is **0x28**, not 0x20. Fields +0x160/+0x164 select icon
and background roots; +0x16C points to the icon ordinal table. Holder 0x546F84
resolves roots across its two tables, then root+0xD8's exact node ordinal.
Resource object IDs and these ordinals differ; the renderer verifies both.

| Groups | Icon/background roots | Slots | Frame ordinal | Frame object ID |
|---|---|---|---|---|
| 1,7 | 19 / 12 | 48 | 4+9*row+column | 8+9*row+column |
| 2 | 43 / 44 | 32 | 6+9*row+column | row base 64,17,35,44 + column |
| 5,6 | 66 / 65 | 16 | 4+9*row+column | row base 64,17 + column |

Both icon and frame must be the pinned texture-node class, with the expected
frame ID. Unmapped categories remain unmarked. Exact epoch, destination list,
group and index connect attribution to these nodes; duplicate IDs are retained.

## Transform and clipping

0xA4FC9C joins 0xA4FE50 after successful vertex construction. The new fixed
capture gateway replays LDR r0,[r6] / AND r0,r0,#15 unchanged. Normal construction
0xA4FEB4 writes four vertices with six floats each into the native cached GUI
buffer at pool+0xB0 plus node+0xBC. The renderer verifies stride 24 and this
exact offset. Alternate constructor flags are unsupported. The native draw-packet helper
0x93EFF4 can skip enqueueing under renderer+0x54 flags; the capture checks that
condition too, so successful vertices alone cannot create a marker.

Model binding 0x2D7 is renderer+0x18BC; global 0x2D6 is +0x18B4. Read-only SPK
analysis decodes twelve position programs and verifies X/Y/W dataflow, constant
bindings and arithmetic modifiers. The perspective blend program 3620 is
rejected even though it shares the first three uniform IDs. Six exact uniform
sequences and the TGUI technique ID select supported runtime paths.

For local vertex (x,y,z): worldX=m0*x+m4*y+m8*z+m12;
worldY=m1*x+m5*y+m9*z+m13; clipX=worldX*g0+g2;
clipY=worldY*g1+g3; W=1. Native depth projection does not affect XY.
Forge pixel coordinates are ((clipX+1)*width/2,(1-clipY)*height/2).
This follows its NVN full viewport and ImGui projection, rather than guessing
screen coordinates. Native scissor is renderer+0xE4. Half-size/offset render
targets, other surfaces, unknown shaders, nonfinite/degenerate quads and empty
clips suppress markers. Geometry dimensions must match Forge's DisplaySize.

## Frame correspondence

The default native surface sentinel resolves through sFestaRender+0x389C0's
parameter field +0x204. Native 0xBC0E98 resolves that sentinel to the swapchain.
0xBC0688 begins a producer frame by incrementing serial +0x33F50, flipping
index +0x33F4C and latching parallel mode +0x1E into +0x1F. The native executor
0xBBE9C8 selects the command list at producer index XOR latched parallel mode.
0xBBE66C executes directly or waits for the render worker, then calls 0xBC0524
and the native present wrapper. Direct execution therefore consumes the current
producer serial/index; parallel execution consumes the previous serial and
opposite index. The 64-sample geometry pool retains both producer frames,
keyed by serial, index, owner and exact binding. If both frames exceed the pool,
the affected frame is suppressed and an incomplete capture is reported.

The second fixed gateway at 0x86A330 intercepts MOV r0,r12 / BX r3 in the native
present wrapper. It verifies queue at backend+0x46F8, window backend+0x4740 and
acquired image index backend+0x46FC, then tail-calls Forge's installed interceptor
without changing arguments or LR. Forge invokes free-render and submits ImGui
on that queue/index before native present. A single-use presentation cycle, executed producer serial/index,
backend owner and live UI fence correlate geometry with this presentation.
Unmatched/reordered/stale snapshots produce no drawing. No Forge edits,
additional trampoline arena, TLS slot or heap buffer are required.

## Reproduction and limitations

```bash
python3 scripts/please_do_better_highlight_research.py prepare
python3 scripts/please_do_better_research.py export
python3 scripts/please_do_better.py build
python3 scripts/please_do_better.py verify
python3 scripts/mod_distribution.py check
```

Research preparation copies the original reward ARC, extracts the GUI and
exports native functions with Ghidra -readOnly -noanalysis. Preparation also copies the pinned MFX and shader ARC and extracts its
58MB SPK using the full 30-bit expanded-size field; the small-resource ARC
helper's 24-bit mask cannot read that member. Receipts compare imported instruction bytes with the
original main and retain hashes; resource/GPU code remains ignored local input,
not shipped code. Successful flush/readback does not prove Eden CPU translation
freshness. Shader/dataflow and ARM draw-call fixtures are static evidence, not
GPU execution, animation/cursor acceptance or exhaustive gameplay coverage.

The historical eight village drops were consistent with old exact-equality
collection rejection; screenshots lack individual events to prove all eight.
R5's original native quantity/empty/copy fixtures reproduce that cause and
separate expected refreshes from genuine incompatible-copy faults. R6 retains
this repair and completed totals; no collection tracker is added.

The independent resource parser verifies 96 original frame ordinals; compiled
update fixtures cover their 162 group instances (shared groups 1/7 and 5/6).
Compiled original begin/executor fragments cover both execution modes and both
initial buffer indices. Rotated/mirrored animated matrices, duplicate item
frames, empty slots and the real 64-sample pool/overflow are exercised without
GPU or gameplay. Both active rendering gateways preserve all NZCVQ/GE values,
GPR, stack/LR and d0-d31/FPSCR. Closing either tree does not stop rendering.
