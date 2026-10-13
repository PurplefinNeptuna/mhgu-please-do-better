#pragma once
#include <stdint.h>

namespace pdb {
struct Preferences { bool force = false, double_quantity = false; };
// One atomic request. Reward scopes latch it; a UI edit never edits instructions.
class Mode {
    uint32_t requested = 0;
public:
    // Bits 0/1 travel together so generation cannot observe half a settings load.
    Preferences preferences() const {
        const auto bits=__atomic_load_n(&requested,__ATOMIC_ACQUIRE);
        return {bool(bits&1),bool(bits&2)};
    }
    bool get() const { return preferences().force; }
    void set(bool value) {
        if(value)__atomic_fetch_or(&requested,1u,__ATOMIC_RELEASE);
        else __atomic_fetch_and(&requested,~1u,__ATOMIC_RELEASE);
    }
    void set(Preferences p) {
        __atomic_store_n(&requested,uint32_t(p.force)|(uint32_t(p.double_quantity)<<1),__ATOMIC_RELEASE);
    }
};
struct PreferencesText { char bytes[64]{}; unsigned size = 0; };
inline PreferencesText encode_preferences(Preferences p) {
    PreferencesText out{};
    const char* text = "force_miraculous=0\ndouble_quantity=0\n";
    while (text[out.size]) { out.bytes[out.size] = text[out.size]; ++out.size; }
    // Derive value positions from literal prefixes; '=' remains part of each key.
    out.bytes[sizeof("force_miraculous=")-1]=p.force?'1':'0';
    out.bytes[sizeof("force_miraculous=0\ndouble_quantity=")-1]=p.double_quantity?'1':'0';
    return out;
}
inline bool decode_preferences(const char* text, unsigned size, Preferences& out) {
    if (!size || size >= sizeof(PreferencesText::bytes)) return false;
    // Existing configs stay readable; new saves omit this obsolete marker.
    constexpr char legacy[] = "version=2\n";
    if (size >= sizeof(legacy)-1) {
        bool same = true;
        for (unsigned i = 0; i < sizeof(legacy)-1; ++i) same = same && text[i] == legacy[i];
        if (same) { text += sizeof(legacy)-1; size -= sizeof(legacy)-1; }
    }
    // Exact bounded format: damaged/unsupported files cannot opt into forcing.
    for (unsigned value = 0; value != 4; ++value) {
        const Preferences p{bool(value&1),bool(value&2)};
        const auto expected = encode_preferences(p);
        // A one-key r19 config preserves Luck and opts out of multiplication.
        const bool old=size==sizeof("force_miraculous=0\n")-1 && !p.double_quantity;
        if (size != expected.size && !old) continue;
        bool same = true;
        for (unsigned i = 0; i < size; ++i) same = same && text[i] == expected.bytes[i];
        if (same) { out=p; return true; }
    }
    return false;
}
}
