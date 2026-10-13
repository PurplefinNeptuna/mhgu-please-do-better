#pragma once
#include <stdint.h>

namespace pdb {
struct Preferences { bool force = false; uint8_t multiplier = 1; };
// One atomic request. Reward scopes latch it; a UI edit never edits instructions.
class Mode {
    uint32_t requested = 0;
public:
    // Bit 0 is Luck; bits 1..3 encode multiplier-1. One publication prevents
    // generation from observing half a settings load. Zero means natural 1x.
    Preferences preferences() const {
        const auto bits=__atomic_load_n(&requested,__ATOMIC_ACQUIRE);
        return {bool(bits&1),uint8_t((bits>>1)+1)};
    }
    bool get() const { return preferences().force; }
    void set(bool value) {
        if(value)__atomic_fetch_or(&requested,1u,__ATOMIC_RELEASE);
        else __atomic_fetch_and(&requested,~1u,__ATOMIC_RELEASE);
    }
    void set(Preferences p) {
        if(p.multiplier<1 || p.multiplier>5)return;
        __atomic_store_n(&requested,uint32_t(p.force)|(uint32_t(p.multiplier-1)<<1),__ATOMIC_RELEASE);
    }
};
struct PreferencesText { char bytes[64]{}; unsigned size = 0; };
inline PreferencesText encode_preferences(Preferences p) {
    PreferencesText out{};
    if(p.multiplier<1 || p.multiplier>5)return out;
    const char* text = "force_miraculous=0\nreward_multiplier=1\n";
    while (text[out.size]) { out.bytes[out.size] = text[out.size]; ++out.size; }
    // Derive value positions from literal prefixes; '=' remains part of each key.
    out.bytes[sizeof("force_miraculous=")-1]=p.force?'1':'0';
    out.bytes[sizeof("force_miraculous=0\nreward_multiplier=")-1]=char('0'+p.multiplier);
    return out;
}
inline bool decode_preferences(const char* text, unsigned size, Preferences& out) {
    if (!size || size >= sizeof(PreferencesText::bytes)) return false;
    // Accept only the new bounded canonical format. Older configs use defaults;
    // the user explicitly chose no migration. Only Save rewrites the primary.
    for (unsigned force=0;force<2;++force) {
        for(unsigned multiplier=1;multiplier<=5;++multiplier) {
            const Preferences p{bool(force),uint8_t(multiplier)};
            const auto expected=encode_preferences(p);
            bool same=size==expected.size;
            if(same)for(unsigned i=0;i<size;++i)same=same && text[i]==expected.bytes[i];
            if(same) {out=p;return true;}
        }
    }
    return false;
}
}
