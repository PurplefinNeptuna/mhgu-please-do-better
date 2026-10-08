#pragma once
#include "mode.h"
namespace pdb {
template<class Files> struct PreferenceStore {
    bool pending = true;
    unsigned save_failure = 0;
    const char* status = "Default: visual only; not saved.";
    void changed() { pending = false; status = "Changed for this session; Save settings remembers the choice."; }
    bool load(Files& files, Preferences& out) {
        if (!pending) return false;
        if (!files.mount()) { status = "Waiting for player preference storage; visual-only default."; return false; }
        struct Mount { Files& p; ~Mount() { p.unmount(); } } mount{files};
        pending = false;
        PreferencesText text{}; Preferences value{};
        if (files.read(0, text) && decode_preferences(text.bytes, text.size, value)) {
            out = value; status = "Saved plugin preference loaded."; return true;
        }
        status = "No valid saved preference; visual-only default."; return false;
    }
    bool save(Files& files, Preferences value) {
        const auto text = encode_preferences(value);
        Preferences verified{};
        if (!decode_preferences(text.bytes, text.size, verified)) return false;
        pending = false;save_failure=0;
        if (!files.mount()) { save_failure=1;status = "Storage unavailable; session choice retained."; return false; }
        struct Mount { Files& p; ~Mount() { p.unmount(); } } mount{files};
        if (!files.write(0, text) || !files.commit()) {
            save_failure=2;status = "Save failed; session choice retained.";
            return false;
        }
        status = "Plugin preference saved beside Better Input."; return true;
    }
};
}
