#pragma once
#include <cstddef>
#include <cstdint>

namespace pdb {
// Stack image shared with gateway.S. Native AArch32 routines use VFP argument
// registers even though the plugin is compiled with softfp. Keep their bits.
struct RawFrame {
    uint32_t target, spare, cpsr, fpscr;
    uint64_t high_d[16], low_d[16];
    uint32_t r[14]; // r0-r12, lr
    uint32_t caller_sp() const { return uint32_t(uintptr_t(this) + sizeof(*this)); }
};
static_assert(sizeof(RawFrame) == 328);
static_assert(offsetof(RawFrame, cpsr) == 8 && offsetof(RawFrame, fpscr) == 12);
static_assert(offsetof(RawFrame, high_d) == 16 && offsetof(RawFrame, low_d) == 144);
static_assert(offsetof(RawFrame, r) == 272);
static_assert(offsetof(RawFrame, r) + 13 * sizeof(uint32_t) == 324);
} // namespace pdb
