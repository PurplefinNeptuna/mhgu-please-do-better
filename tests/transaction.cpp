#include "transaction.h"
#include <assert.h>
#include <stdio.h>
#include <map>
#include <vector>

using namespace pdb;
constexpr uint32_t base = 0x100000;
struct Fake {
    std::map<uint32_t, uint32_t> memory;
    uint64_t title = program_id;
    bool program_ok = true, mapping_ok = true;
    unsigned programs = 0, writes = 0, syncs = 0, reads = 0;
    unsigned fail_write = 0, fail_after_store = 0, fail_sync = 0, fail_rollback_sync = 0;
    unsigned reject_external = 0;
    uint32_t external_on_sync = 0, external_value = 0xe1a00000;
    bool signature_after_first = false, fail_final_once = false, fail_rollback_read = false;
    bool change_restored_on_sync = false;
    std::vector<uint32_t> writes_at, flush_at;
    Fake() {
        for (const auto& s : sites) for (unsigned j = 0; j < 8; ++j)
            memory[base+s.window+4*j] = s.words[j];
    }
    bool program(uint64_t& out) { ++programs; out = title; return program_ok; }
    bool executable(uint32_t a, unsigned n) {
        return mapping_ok && memory.count(a) && memory.count(a+n-4);
    }
    bool read(uint32_t a, uint32_t& out) {
        ++reads;
        if (fail_final_once && syncs == 2 && a == base+site_offset(0)) {
            fail_final_once = false; return false;
        }
        if (fail_rollback_read && syncs && a == base+site_offset(0)) return false;
        if (!memory.count(a)) return false;
        out = memory[a]; return true;
    }
    bool write(uint32_t a, uint32_t expected, uint32_t v, bool& stored) {
        ++writes; writes_at.push_back(a); stored = false;
        if (reject_external == writes) { memory[a] = replacement; return false; }
        if (fail_write == writes || memory[a] != expected) return false;
        memory[a] = v; stored = true;
        return fail_after_store != writes;
    }
    uint32_t sync(uint32_t a, unsigned n) {
        assert(n == 4); ++syncs; flush_at.push_back(a);
        if (external_on_sync && syncs == 1) memory[external_on_sync] = external_value;
        if (change_restored_on_sync && syncs == 2) memory[base+site_offset(0)] = 0xe1a00000;
        if (signature_after_first && syncs == 1) memory[base+sites[1].window] ^= 1;
        return (syncs == fail_sync || syncs == fail_rollback_sync) ? 0x1234 : 0;
    }
    void original(unsigned i) const { assert(memory.at(base+site_offset(i)) == sites[i].words[3]); }
    void patched(unsigned i) const { assert(memory.at(base+site_offset(i)) == replacement); }
};

int main() {
    unsigned scenarios = 0;
    {
        Fake f; const auto before = f.memory; Transaction<Fake> t(f);
        const auto r = t.install(base); assert(r.state == State::Applied && r.owned == 3);
        assert(f.writes == 2 && f.syncs == 2); f.patched(0); f.patched(1);
        for (const auto& e : before) if (e.first != base+site_offset(0) && e.first != base+site_offset(1))
            assert(f.memory.at(e.first) == e.second);
        assert(t.install(base+4).state == State::Applied && f.writes == 2 && f.syncs == 2 && f.programs == 1);
        f.memory[base+site_offset(1)] = 0xe1a00000;
        assert(t.install(base).state == State::Unsafe && f.writes == 2); ++scenarios;
    }
    for (bool failed_query : {false, true}) {
        Fake f; f.title ^= 1; f.program_ok = !failed_query; Transaction<Fake> t(f);
        assert(t.install(base).failure == Failure::Program && f.writes == 0);
        assert(t.install(base).state == State::Rejected && f.programs == 1); ++scenarios;
    }
    for (uint32_t address : {0u, base+1, 0xffffff00u}) {
        Fake f; Transaction<Fake> t(f); assert(t.install(address).failure == Failure::Address);
        assert(f.writes == 0); ++scenarios;
    }
    {
        Fake f; f.mapping_ok = false; Transaction<Fake> t(f);
        assert(t.install(base).failure == Failure::Address && f.reads == 0 && f.writes == 0); ++scenarios;
    }
    // Every byte window word, including either original BL, is a preflight guard.
    for (unsigned i = 0; i < 2; ++i) for (unsigned j = 0; j < 8; ++j) {
        Fake f; f.memory[base+sites[i].window+4*j] ^= 1; Transaction<Fake> t(f);
        const auto r = t.install(base); assert(r.state == State::Rejected && r.site == i+1 && f.writes == 0);
        ++scenarios;
    }
    for (unsigned mask = 1; mask <= 3; ++mask) {
        Fake f; for (unsigned i = 0; i < 2; ++i) if (mask & (1u<<i)) f.memory[base+site_offset(i)] = replacement;
        const auto before = f.memory; Transaction<Fake> t(f);
        assert(t.install(base).state == State::Rejected && f.memory == before && f.writes == 0); ++scenarios;
    }
    for (unsigned i = 1; i <= 2; ++i) {
        for (bool after : {false, true}) {
            Fake f; if (after) f.fail_after_store = i; else f.fail_write = i;
            Transaction<Fake> t(f); const auto r = t.install(base);
            assert(r.state == State::RolledBack && r.failure == Failure::Write && r.owned == 0);
            f.original(0); f.original(1);
            const auto w = f.writes; assert(t.install(base).state == State::RolledBack && f.writes == w);
            ++scenarios;
        }
        Fake f; f.fail_sync = i; Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::RolledBack && r.failure == Failure::Cache && r.cache_result == 0x1234);
        f.original(0); f.original(1); assert(f.syncs == 2*i);
        if (i == 2) assert(f.flush_at[2] == base+site_offset(1) && f.flush_at[3] == base+site_offset(0));
        ++scenarios;
    }
    {
        Fake f; f.fail_final_once = true; Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::RolledBack && r.failure == Failure::Readback && r.owned == 0);
        f.original(0); f.original(1); ++scenarios;
    }
    {
        Fake f; f.signature_after_first = true; Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::RolledBack && r.failure == Failure::Signature && r.site == 2);
        f.original(0); f.original(1); assert(f.writes == 2); ++scenarios;
    }
    // A failed expected-word check must not claim/restore somebody else's MOV.
    for (unsigned i = 1; i <= 2; ++i) {
        Fake f; f.reject_external = i; Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::RolledBack && r.owned == 0); f.patched(i-1);
        if (i == 2) f.original(0);
        assert(f.writes == 2*i-1); ++scenarios;
    }
    {
        Fake f; f.fail_sync = 1; f.external_on_sync = base+site_offset(0);
        Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::Unsafe && r.rollback_failed == 1 && f.writes == 1);
        assert(f.memory[base+site_offset(0)] == f.external_value); f.original(1); ++scenarios;
    }
    {
        Fake f; f.fail_sync = 1; f.external_on_sync = base+site_offset(0);
        f.external_value = sites[0].words[3]; Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::RolledBack && r.owned == 0 && f.writes == 1 && f.syncs == 2);
        f.original(0); f.original(1); ++scenarios;
    }
    {
        Fake f; f.fail_sync = 1; f.fail_rollback_sync = 2; f.external_on_sync = base+site_offset(0);
        f.external_value = sites[0].words[3]; Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::Unsafe && r.owned == 0 && r.rollback_failed == 1 && f.writes == 1);
        assert(r.rollback_cache_result == 0x1234); f.original(0); f.original(1); ++scenarios;
    }
    {
        Fake f; f.fail_sync = 1; f.external_on_sync = base+site_offset(0);
        f.external_value = sites[0].words[3]; f.change_restored_on_sync = true;
        Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::Unsafe && r.rollback_failed == 1 && f.writes == 1);
        assert(f.memory[base+site_offset(0)] == 0xe1a00000); ++scenarios;
    }
    {
        Fake f; f.fail_sync = 2; f.fail_write = 3; Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::Unsafe && r.owned == 2 && r.rollback_failed == 2);
        f.original(0); f.patched(1); ++scenarios;
    }
    {
        Fake f; f.fail_sync = 2; f.fail_rollback_sync = 3; Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::Unsafe && r.owned == 0 && r.rollback_failed == 2);
        assert(r.rollback_cache_result == 0x1234);
        f.original(0); f.original(1); ++scenarios;
    }
    {
        Fake f; f.fail_sync = 1; f.fail_rollback_read = true; Transaction<Fake> t(f); const auto r = t.install(base);
        assert(r.state == State::Unsafe && r.owned == 1 && f.writes == 1); f.patched(0); ++scenarios;
    }
    printf("PASS: %u transaction scenarios (production transaction, failure injection)\n", scenarios);
}
