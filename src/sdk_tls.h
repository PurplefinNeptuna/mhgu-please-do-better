#pragma once
#include <cstdint>

// Verified against the fingerprinted MHGU 1.4.0 SDK, not Forge's Result-return
// declaration for SetTlsValue. The C wrapper resolves to the void native setter
// at SDK + 0x9d80c; r0 remains a computed TLS address, not a Result.
using TlsSlot = int;
extern "C" uint32_t nnosAllocateTlsSlot(TlsSlot*, void (*)(void*));
extern "C" void* nnosGetTlsValue(TlsSlot);
extern "C" void nnosSetTlsValue(TlsSlot, void*);
// Immutable thread identity lets an already-entered paired scope return safely
// if its reserved TLS value is lost. Pinned SDK body: MRC, LDR +0x1fc, BX LR.
extern "C" void* pdb_current_thread() asm("_ZN2nn2os16GetCurrentThreadEv");
