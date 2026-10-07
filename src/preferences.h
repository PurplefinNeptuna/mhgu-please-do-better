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
        if (files.read(1, text) && decode_preferences(text.bytes, text.size, value)) {
            out = value; status = "Plugin preference recovered from backup."; return true;
        }
        status = "No valid saved preference; visual-only default."; return false;
    }
    bool save(Files& files, Preferences value) {
        pending = false;save_failure=0;
        if (!files.mount()) { save_failure=1;status = "Storage unavailable; session choice retained."; return false; }
        struct Mount { Files& p; ~Mount() { p.unmount(); } } mount{files};
        PreferencesText previous{}; Preferences decoded{};
        bool have_previous = files.read(0, previous) && decode_preferences(previous.bytes, previous.size, decoded);
        if(!have_previous)have_previous=files.read(1,previous) && decode_preferences(previous.bytes,previous.size,decoded);
        if(!have_previous)previous=encode_preferences({false}); // Fresh recovery stays natural.
        if (!files.write(1, previous) || !files.commit()) {
            save_failure=2;status = "Backup failed; primary unchanged; session choice retained."; return false;
        }
        const auto text = encode_preferences(value);
        if (!files.write(0, text) || !files.commit()) {
            const bool recovered = files.write(0, previous) && files.commit();
            save_failure=recovered?3:4;status = recovered ? "Save failed; previous preference restored; session choice retained." :
                                 "Save failed; recovery uncertain; session choice retained.";
            return false;
        }
        status = "Plugin preference saved beside Better Input."; return true;
    }
};
}
