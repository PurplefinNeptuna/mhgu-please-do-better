#pragma once
#include <stdint.h>

namespace pdb {
// One atomic request. Reward scopes latch it; a UI edit never edits instructions.
class Mode {
    uint32_t requested = 0;
public:
    bool get() const { return __atomic_load_n(&requested, __ATOMIC_ACQUIRE) != 0; }
    void set(bool value) { __atomic_store_n(&requested, uint32_t(value), __ATOMIC_RELEASE); }
};
struct Preferences { bool force = false; };
struct PreferencesText { char bytes[64]{}; unsigned size = 0; };
inline PreferencesText encode_preferences(Preferences p) {
    PreferencesText out{};
    const char* text = p.force ? "force_miraculous=1\n" : "force_miraculous=0\n";
    while (text[out.size]) { out.bytes[out.size] = text[out.size]; ++out.size; }
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
    for (unsigned value = 0; value != 2; ++value) {
        const auto expected = encode_preferences({value != 0});
        if (size != expected.size) continue;
        bool same = true;
        for (unsigned i = 0; i < size; ++i) same = same && text[i] == expected.bytes[i];
        if (same) { out.force = value != 0; return true; }
    }
    return false;
}
}
