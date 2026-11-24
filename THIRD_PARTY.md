# Notices

Project-owned code in this folder is copyright PurplefinNeptuna (2026), under the GNU General
Public License version 3 or (at your option) any later version; see `LICENSE`.

The two-site `[Great Luck]` cheat is credited to 花花花花花椰菜 in the offline
MHGU-Modding wiki snapshot. Source:
[Cheat Codes](https://github.com/RTHKKona/MHGU-Modding/wiki/Cheat-Codes).
Skill-name research uses [Skill IDs](https://github.com/RTHKKona/MHGU-Modding/wiki/Skill-IDs).
Game-derived inputs/decompilation and external emulator snapshots are local
reference data and are not included in the candidate ZIP.

The plugin is Rust, built from vendored forge-rs 1.5.0 (revision
`d1865b68e9b194eb3eacc8bd71bbf601a5fac63e`, MIT, Fexty) and the registry sources in
`vendor/crates`, pinned by `Cargo.lock` and `dependencies.lock.json`. The Rust runtime
is `core` and `alloc` built from source by `build-std`; see `licenses/`. The cargo-forge
1.4.1 converter and devkitARM binutils are host tools, not shipped.

The hook backend is a narrow adaptation of Modern Controls' earlier native backend.
R2 adapts owned Damage Numbers gateway, bounded mailbox and ARM32 SDK declaration
patterns. Its fixture-only SDK reader is reused from the owned
`scripts/damage_numbers_sdk_tls_probe.py`, fingerprinted in the manifest.
No game executable, shader program, texture or decompiled source is bundled.
The runtime imports existing Forge and ImGui implementations; it bundles no loader.
Input/source SHA-256 values are recorded in the adjacent candidate manifest.

`src/svc.S` adapts libnx `nx/source/kernel/svc32.s`, using its MIT terms:

Copyright (c) 2019 Hydrosphere Developers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## R6 offline rendering research

Pinned game GUI/SPK data is private local research input and is not bundled.
The Maxwell instruction encoding table in the pinned Eden reference is read as
research data to verify shader position dataflow. No Eden runtime implementation
or game shader bytes are compiled into the plugin or included in its ZIP.
Highlights use the game's own frame colour setter. The settings panel uses existing Forge/cimgui exports.
