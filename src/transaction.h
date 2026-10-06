#pragma once
#include "patches.h"

namespace pdb {
enum class State : uint32_t { Fresh, Applied, Rejected, RolledBack, Unsafe };
enum class Failure : uint32_t { None, Program, Address, Signature, Write, Cache, Readback, Changed };
struct Report {
    State state = State::Fresh;
    Failure failure = Failure::None;
    unsigned site = 0; // 1 or 2, zero for program/address validation.
    uint32_t owned = 0, rollback_failed = 0, cache_result = 0, rollback_cache_result = 0;
};

// Platform methods return checked results. Storage/ownership is process-lived;
// retries, runtime uninstall and periodic patch enforcement are intentionally absent.
template<class Platform> class Transaction {
    Platform& p;
    uint32_t base = 0;
    Report r{};
    bool signature(unsigned i, bool patched = false) {
        for (unsigned j = 0; j < 8; ++j) {
            uint32_t word = 0;
            if (!p.read(base + sites[i].window + 4*j, word) ||
                word != ((patched && j == 3) ? replacement : sites[i].words[j])) return false;
        }
        return true;
    }
    void rollback() {
        // Inspect only attempted stores. Never adopt an external replacement as
        // an original or restore over a different owner's current instruction.
        for (unsigned n = 2; n; --n) {
            const unsigned i = n - 1;
            const uint32_t bit = 1u << i, address = base + site_offset(i);
            if (!(r.owned & bit)) continue;
            uint32_t word = 0;
            if (!p.read(address, word)) { r.rollback_failed |= bit; continue; }
            if (word == sites[i].words[3]) {
                // Someone already restored these bytes. Do not write, but still
                // synchronize before claiming a completed rollback.
                const uint32_t rc = p.sync(address, 4);
                const bool restored = p.read(address, word) && word == sites[i].words[3];
                if (restored) r.owned &= ~bit;
                if (rc) r.rollback_cache_result = rc;
                if (rc || !restored) r.rollback_failed |= bit;
                continue;
            }
            if (word != replacement) { r.rollback_failed |= bit; continue; }
            bool stored = false;
            const bool wrote = p.write(address, replacement, sites[i].words[3], stored);
            const uint32_t rc = p.sync(address, 4);
            if (rc) r.rollback_cache_result = rc;
            const bool restored = p.read(address, word) && word == sites[i].words[3];
            if (restored) r.owned &= ~bit;
            if (!wrote || rc || !restored) r.rollback_failed |= bit;
        }
        r.state = (r.rollback_failed || r.owned) ? State::Unsafe : State::RolledBack;
    }
    Report fail(Failure why, unsigned site, bool restore) {
        r.failure = why; r.site = site;
        if (restore) rollback(); else r.state = State::Rejected;
        return r;
    }
public:
    constexpr explicit Transaction(Platform& platform) : p(platform) {}
    Report report() const { return r; }
    Report install(uint32_t main_base) {
        if (r.state != State::Fresh) {
            if (r.state == State::Applied) {
                for (unsigned i = 0; i < 2; ++i) if (!signature(i, true)) {
                    r.state = State::Unsafe; r.failure = Failure::Changed; r.site = i+1;
                    break;
                }
            }
            return r; // Never write again, including after rejection/rollback.
        }
        uint64_t title = 0;
        if (!p.program(title) || title != program_id) return fail(Failure::Program, 0, false);
        if (!main_base || (main_base & 3) ||
            uint64_t(main_base) + sites[1].window + 32 > 0x100000000ull)
            return fail(Failure::Address, 0, false);
        base = main_base;
        // Both sites must pass before publishing either change.
        for (unsigned i = 0; i < 2; ++i) {
            if (!p.executable(base + sites[i].window, 32)) return fail(Failure::Address, i+1, false);
            if (!signature(i)) return fail(Failure::Signature, i+1, false);
        }
        for (unsigned i = 0; i < 2; ++i) {
            // Recheck the whole site immediately before its store.
            if (!signature(i)) return fail(Failure::Signature, i+1, true);
            const uint32_t address = base + site_offset(i);
            bool stored = false;
            const bool wrote = p.write(address, sites[i].words[3], replacement, stored);
            if (stored) r.owned |= 1u << i; // Readback can fail after an actual store.
            if (!wrote || !stored) return fail(Failure::Write, i+1, true);
            r.cache_result = p.sync(address, 4);
            if (r.cache_result) return fail(Failure::Cache, i+1, true);
        }
        // Check both full windows again after the last publication.
        for (unsigned i = 0; i < 2; ++i)
            if (!signature(i, true)) return fail(Failure::Readback, i+1, true);
        r.state = State::Applied;
        return r;
    }
};

inline const char* status(State s) {
    switch (s) {
    case State::Fresh: return "Startup patches not attempted.";
    case State::Applied: return "Both startup patches applied; readback and flush checked.";
    case State::Rejected: return "Startup rejected; this plugin wrote no instructions.";
    case State::RolledBack: return "Startup failed; owned writes rolled back and flushed.";
    case State::Unsafe: return "Startup/code conflict or rollback failure; full restart required.";
    }
    return "Unknown state; full restart required.";
}
inline const char* failure_status(Failure f) {
    switch (f) {
    case Failure::None: return "none";
    case Failure::Program: return "wrong title or program query failed";
    case Failure::Address: return "invalid base or executable mapping";
    case Failure::Signature: return "original code signature mismatch/conflict";
    case Failure::Write: return "instruction write/readback failed";
    case Failure::Cache: return "cache flush failed";
    case Failure::Readback: return "final patched signature/readback failed";
    case Failure::Changed: return "previously applied code changed externally";
    }
    return "unknown failure";
}
}
