#pragma once
#include "transaction.h"
namespace pdb {
constexpr unsigned max_hooks = 24, trampoline_bytes = 32;
struct Hook {
    uint32_t site, window, detour;
    uint32_t words[8];
    bool paired;
};
struct HookReport {
    State state = State::Fresh;
    Failure failure = Failure::None;
    uint64_t owned = 0, unsafe = 0;
    unsigned site = 0;
    uint32_t cache = 0;
};
// Every word is journaled separately. An intervening external edit is never
// restored over, even if the other word in that detour still belongs to us.
template<class Platform> class Hooks {
    Platform& p;
    Hook recipe[max_hooks]{};
    uint32_t base = 0;
    unsigned count = 0;
    HookReport report_{};
    bool arena = false;
    bool signature(unsigned i, bool installed = false) {
        const auto& h = recipe[i];
        for (unsigned j = 0; j < 8; ++j) {
            const uint32_t offset = h.window + j*4;
            uint32_t expected = h.words[j], actual = 0;
            if (installed && offset == h.site) expected = 0xe51ff004;
            if (installed && offset == h.site+4) expected = h.detour;
            if (!p.read(base+offset, actual) || actual != expected) return false;
        }
        return true;
    }
    uint32_t original_word(unsigned i, unsigned j) const {
        return recipe[i].words[(recipe[i].site-recipe[i].window)/4+j];
    }
    void restore() {
        for (unsigned n = count*2; n; --n) {
            const unsigned k = n-1, i = k/2, j = k%2;
            const uint64_t bit = uint64_t(1)<<k;
            if (!(report_.owned & bit)) continue;
            const uint32_t a = base+recipe[i].site+j*4;
            const uint32_t installed = j ? recipe[i].detour : 0xe51ff004;
            uint32_t v = 0; bool stored = false;
            if (!p.read(a,v)) { report_.unsafe |= bit; continue; }
            if (v != original_word(i,j) && (v != installed ||
                !p.write(a,installed,original_word(i,j),stored))) {
                report_.unsafe |= bit; continue;
            }
            const auto rc = p.sync(a,4);
            if (rc) report_.cache = rc;
            if (rc || !p.read(a,v) || v != original_word(i,j)) report_.unsafe |= bit;
            else report_.owned &= ~bit;
        }
        if (report_.unsafe || report_.owned) report_.state = State::Unsafe;
        else {
            report_.state = State::RolledBack;
            if (arena && !p.close()) { report_.state = State::Unsafe; report_.unsafe = ~uint64_t(0); }
            else arena = false;
        }
    }
    HookReport fail(Failure f, unsigned i) {
        report_.failure = f; report_.site = i;
        if (report_.owned) restore();
        else {
            report_.state = State::Rejected;
            if (arena && !p.close()) { report_.state = State::Unsafe; report_.unsafe = ~uint64_t(0); }
            else arena = false;
        }
        return report_;
    }
public:
    constexpr explicit Hooks(Platform& platform): p(platform) {}
    HookReport report() const { return report_; }
    uint32_t original(unsigned i) const {
        return arena && i < count && recipe[i].paired ? p.rx_base()+i*trampoline_bytes : 0;
    }
    HookReport install(uint32_t main, const Hook* hooks, unsigned n) {
        if (report_.state != State::Fresh) {
            if (report_.state == State::Applied) for (unsigned i=0;i<count;++i)
                if (!signature(i,true)) { report_.state=State::Unsafe; report_.failure=Failure::Changed;
                    report_.site=i+1;report_.unsafe|=uint64_t(3)<<(2*i);break; }
            return report_;
        }
        uint64_t title=0;
        if (!p.program(title) || title!=program_id) return fail(Failure::Program,0);
        if (!main || (main&3) || !hooks || !n || n>max_hooks) return fail(Failure::Address,0);
        base=main; count=n;
        bool need_arena=false;
        for (unsigned i=0;i<n;++i) {
            recipe[i]=hooks[i]; const auto& h=recipe[i];
            if ((h.site|h.window|h.detour)&3 || !h.detour || h.site<h.window || uint64_t(h.site)+8>uint64_t(h.window)+32 ||
                uint64_t(main)+h.window+32>0x100000000ull || !p.executable(main+h.window,32) ||
                uint64_t(h.detour)+4>0x100000000ull || !p.executable(h.detour,4)) return fail(Failure::Address,i+1);
            if(uint64_t(h.detour)<uint64_t(main)+h.window+32 &&
               uint64_t(main)+h.window<uint64_t(h.detour)+4) return fail(Failure::Address,i+1);
            for (unsigned j=0;j<i;++j) if (uint64_t(h.site)<uint64_t(recipe[j].site)+8 &&
                uint64_t(recipe[j].site)<uint64_t(h.site)+8) return fail(Failure::Address,i+1);
            if (!signature(i)) return fail(Failure::Signature,i+1);
            need_arena=need_arena || h.paired;
        }
        if (need_arena) {
            if (!p.create(4096)) { arena=p.owns_arena(); return fail(Failure::Address,0); }
            arena=true;
            for (unsigned i=0;i<n;++i) if (recipe[i].paired) {
                if (!p.prepare(i*trampoline_bytes,base+recipe[i].site,
                               original_word(i,0),original_word(i,1))) return fail(Failure::Address,i+1);
            }
            if (!p.make_executable()) return fail(Failure::Cache,0);
        }
        for (unsigned i=0;i<n;++i) {
            if (!signature(i)) return fail(Failure::Signature,i+1);
            // Literal first, instruction last. This is startup-only publication.
            for (unsigned x=0;x<2;++x) {
                const unsigned j=1-x; bool stored=false;
                const bool ok=p.write(base+recipe[i].site+4*j,original_word(i,j),
                                      j?recipe[i].detour:0xe51ff004,stored);
                if (stored) report_.owned |= uint64_t(1)<<(2*i+j);
                if (!ok || !stored) return fail(Failure::Write,i+1);
            }
            report_.cache=p.sync(base+recipe[i].site,8);
            if (report_.cache) return fail(Failure::Cache,i+1);
        }
        for (unsigned i=0;i<n;++i) if (!signature(i,true)) return fail(Failure::Readback,i+1);
        report_.state=State::Applied; return report_;
    }
};
}
