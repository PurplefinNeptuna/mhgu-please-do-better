# Notices

The two-site `[Great Luck]` cheat is credited to 花花花花花椰菜 in the offline
MHGU-Modding wiki snapshot. Source:
[Cheat Codes](https://github.com/RTHKKona/MHGU-Modding/wiki/Cheat-Codes).
Skill-name research uses [Skill IDs](https://github.com/RTHKKona/MHGU-Modding/wiki/Skill-IDs).
Game-derived inputs/decompilation and external emulator snapshots are local
reference data and are not included in the candidate ZIP.

The plugin uses owned ARM32 scaffolding from Key Quest Markers and a narrow
adaptation of Modern Controls' native backend, also compiled by Damage Numbers.
R2 adapts owned Damage Numbers gateway, bounded mailbox and ARM32 SDK declaration
patterns. Its fixture-only SDK reader is reused from the owned
`scripts/damage_numbers_sdk_tls_probe.py`, fingerprinted in the manifest.
No game executable, shader program, texture or decompiled source is bundled.
Build headers/dependencies are the maintained Forge, pinned libnx and cimgui.
The runtime imports existing Forge/cimgui implementations; it bundles no loader.
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
