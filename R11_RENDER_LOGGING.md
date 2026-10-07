# R11 bounded emulator-log rendering trace

The user explicitly authorized verbose logging in Eden's log and asked to keep
it out of Forge's ImGui diagnostic panel. Forge's exported logger already reaches
Eden OutputDebugString. This candidate uses that API; it neither edits the host
log directly nor changes emulator logging settings.

## R10 user-run evidence

The supplied reward-grid screenshot shows eight generated slots, four extras,
four bound slots, zero highlights and zero capture/mapping faults. The latest
log identifies Eden master-10bcd2d849, MHGU 1.4.0 / main build
FB08F1D20FD1204FE7070672777F869B and Forge 1.4.1-originalbi1. Loaded plugins include
Better Input, Damage Numbers, Key Quest Markers, Modern Controls and Please do
Better. All r10 patch groups report Applied with zero unsafe words. No draw
rejection follows. Installed r10 NRO matches the accepted candidate:
`9a415d34045f384754b4816ad8c16f005a9112b7834c3fcfc6c4138867dd57c8`.
Copied log/screenshot and 107-file preservation receipt are under
`work/please-do-better/r11-report/`. Package presence alone is not activation
proof; the loaded plugin names above come from this launch log.

The log cannot distinguish silent capture exits from geometry/frame/size/binding
mismatches. Zero capture faults establishes no draw success. R11 makes those
paths observable without relaxing any rendering guard or guessing placement.
It retains r10's native texture identity, exact provenance and frame checks.

## Reading the trace

All lines have `[please-do-better] r11` and are formatted only in Forge callbacks.
`render trace` supplies the live screen fence, callback cycle, binding/draw counts
and native singleton. `geometry gates`, `present gates` and `render gates` name
all cumulative stage counts. Counts are atomic best-effort observations under
contention; cross-field totals are not a synchronized game transaction.

Geometry labels: enter/bound/registers/unbound/matched, then list/item/identity,
uncached/tiled/renderer/frame/layout/submission/target/texture/shader/viewport,
buffer/inputs/quad/clip/epoch, published/conflict/overflow. Only matched nodes
publish `last-capture`; its numerical gate is the zero-based label position in
this list. The snapshot holds node/list/index, cache/layout flags, vertex buffer,
model/global bindings, native frame/serial/parallel mode and actual input floats.
Failed reads produce zero fields and a gate count; they do not adopt game bytes.

Present labels: enter/disabled/context/frame/metadata/image/published/conflict.
`native-present` compares actual and expected queue/index, cached resource/table
and its texture. `selected-present` supplies the immutable frame/serial/cycle and
image used by rendering, plus Forge display dimensions/framebuffer scale.

Render labels: enter/disabled/pending/snapshot/cycle/overflow/io/drawlist/time,
sample/frame/dimensions/binding/epoch/image/drawn. `geometry[n]` records up to eight
current-screen geometry snapshots with provenance, frame/serial, texture,
size, screen perimeter and clipping. The first bundle also records up to eight
exact bindings. This separates missing capture, wrong frame, wrong dimensions,
identity loss and texture mismatch. Existing explicit draw-rejection and startup
failure details also go to the log. The compact panel shows only a brief
suppression notice and actionable status, with no raw rendering addresses,
shader lists or viewport dump.

## Bounds and limitations

Twenty bounded trace formats fit the maintained Forge logger’s 520-byte buffer,
including maximum integer values, finite float extremes, infinities and NaN.
Long records are split and float inputs use bounded significant-digit formatting.
Forge itself is unchanged. The recipe allows an 80KiB static NRO for the added
code/format strings; its BSS ceiling remains 80KiB, and arena/TLS/heap limits are
unchanged. Two fixed telemetry snapshots and scalar atomic stage counters are added. Existing
eight contexts/four scopes, one TLS slot, one 4KiB arena and 64 binding/geometry
entries stay unchanged. No allocation, additional hook or game memory write is
introduced. Native helpers never format or log with live gateway state. The
free-render callback's scope emits telemetry even when rendering returns early.
A nonblocking claim serializes trace budgeting; contention drops a bundle.

Per screen: first eight callbacks, then every 120 callbacks, at most 24 bundles.
Per process: at most 128 bundles. Closing the Forge panel does not stop tracing.
Old-screen snapshots are never reported as current geometry. Logs describe CPU
capture/render decisions, not GPU execution or visible alignment. R11 is a
DEVELOPMENT diagnostic candidate; the screenshot's silent stopping point remains
unknown until runtime trace evidence arrives. No installation, activation,
launch, real save/settings edits, push or publication is included.
