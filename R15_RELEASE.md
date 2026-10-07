# R15 release changes

The user accepted r14's visible gold highlighting on Eden and approved local
distribution on 2026-10-07. R15 removes the repeated render-trace bundles:
geometry/shader/viewport addresses, matrices, clip/perimeter dumps, bindings,
presentation metadata and periodic sampling. Normal rendering emits no logs.
Three startup safety records and a short unsupported-path message, bounded to
once per rejection class per reward screen, remain. No render gateway formats
logs. Existing capture counters and immutable safety evidence stay internal.

Rendering, reward attribution, Force Miraculous Luck, preferences, native hooks,
register/flag preservation and allocation limits retain the accepted r14 behavior.
The r14 candidate and source commit 1888454 remain unchanged. The logging cleanup
creates a different NRO and therefore a new release version, r15.

Known external limitation: Forge's menu can display corrupt geometry while a
background overlay is drawing, as reported with Damage Numbers and now this
plugin. The existing handoff is
../../docs/FORGE_IMGUI_DAMAGE_CORRUPTION_HANDOFF.md. Forge is unchanged; this
release does not fix that renderer defect. Close Forge while viewing marked
rewards and adjust plugin settings outside active highlighting.

Concise unsupported-path codes: 1 alternate texture constructor; 2 unavailable
draw target; 4 unsupported viewport; 5 unknown GUI shader; 6 unavailable texture
or view; 7 inconsistent acquired-image metadata. Such markers are suppressed.
Code 3's old intermediate-texture gate is absent. Startup unsafe restoration
still reports through the existing status/logger and retains reachable storage.

R14 visible acceptance and r15 static validation are separate; broader gameplay
and Ryujinx remain pending in MANUAL_TESTS.md and RUNTIME.md. Publication is not
included. The distribution ZIP bundles only the plugin; Forge is a dependency.
