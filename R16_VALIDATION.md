# Please do Better r16 validation

NRO SHA-256: `b4f27d001d5bb1444f055622b8eede36e0d9b462b0793e4f5f5eb32afda3bcb7`.
Candidate ZIP SHA-256: `edb187ab3e708722c9cb791f158df06954c74819fd9c98220a3ff15b4de8f8de`.

R16 removes runtime summaries and diagnostics from the settings panel. The forcing control, preference save feedback, background reward attribution and gold marker rendering remain. Startup logging has one concise summary, readable startup failures and distinct process-lifetime suppression reasons. Default builds omit geometry/presentation detail snapshots and emit no periodic gameplay logs. Developer captures require build --diagnostics and have no diagnostic UI.

Fresh compiled fixtures cover ARM32 GPR/stack/NZCVQ/GE/VFP/FPSCR, transactional startup/failure/rollback, skill and reward count algorithms, copy/relocation ownership, preference defaults/persistence, layout/clipping/shader/resource/presentation gates, settings trees, silent repeated frames and deferred lifetime failure reporting. Log format bounds and ARM32 variadic string/integer arguments are checked.

No new gameplay test was run. The user confirmed the visible r14 marker on Eden; r15 logging cleanup was statically verified without a separate gameplay run. Those confirmations retain their original scope. R16 has its own compiled/static evidence and does not inherit a new manual acceptance claim. Ryujinx gameplay remains untested. Forge's menu/background renderer issue remains disclosed and unchanged.
