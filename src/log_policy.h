#pragma once
#include <stdint.h>
#ifndef MHGU_DIAGNOSTICS
#define MHGU_DIAGNOSTICS 0
#endif
namespace mod_log {
inline constexpr bool diagnostics = MHGU_DIAGNOSTICS != 0;
// Each fixed reason is reported at most once for this process. Never reset.
struct Once {
    uint32_t reasons = 0;
    bool claim(unsigned reason) {
        if (reason >= 32) return false;
        const uint32_t bit = 1u << reason;
        return !(__atomic_fetch_or(&reasons, bit, __ATOMIC_RELAXED) & bit);
    }
};
}
