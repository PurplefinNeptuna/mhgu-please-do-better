#include "log_policy.h"
#include <forge/log.h>
#include "settings.h"
#include "preferences.h"
#include "sdk_fs.h"
#include <forge/fs.h>
namespace pdb {
static constexpr const char* path = "savedata:/please_do_better.ini";
struct Files {
    FsAbortGuard abort;
    bool mount() { return forge_fs_mountSaveData(); }
    void unmount() { forge_fs_unmountSaveData(); }
    bool read(unsigned slot, PreferencesText& text) {
        uint32_t handle = 0;
        if (slot != 0 || pdb_fs_open(&handle, path, 1)) return false;
        int64_t size = 0;
        bool ok = !pdb_fs_size(&size, handle) && size > 0 && size < int64_t(sizeof(text.bytes));
        if (ok) { text.size = unsigned(size); ok = !pdb_fs_read(handle, 0, text.bytes, text.size); }
        pdb_fs_close(handle); return ok;
    }
    bool write(unsigned slot, const PreferencesText& text) {
        if (slot != 0 || !text.size || text.size >= sizeof(text.bytes)) return false;
        uint32_t handle = 0;
        if (pdb_fs_open(&handle, path, 2) &&
            (pdb_fs_create(path, text.size) || pdb_fs_open(&handle, path, 2))) return false;
        const uint32_t flush = 1;
        const bool wrote = !pdb_fs_resize(handle, text.size) &&
            !pdb_fs_write(handle, 0, text.bytes, text.size, &flush) && !pdb_fs_flush(handle);
        pdb_fs_close(handle);
        PreferencesText check{};
        if (!wrote || !read(slot, check) || check.size != text.size) return false;
        for (unsigned i = 0; i < text.size; ++i) if (text.bytes[i] != check.bytes[i]) return false;
        return true;
    }
    bool commit() { return pdb_fs_commit("savedata") == 0; }
};
static PreferenceStore<Files> store;
bool load_preferences(Preferences& out) { Files files; return store.load(files, out); }
bool save_preferences(Preferences value) {
    Files files;static mod_log::Once failures;
    static bool have_saved, saved;
    if (!store.save(files,value)) {
        const unsigned reason=store.save_failure;
        if(failures.claim(reason)) forge_log_warn("[please-do-better] %s Load a player save and retry Save settings.",store.status);
        return false;
    }
    if(!have_saved || saved!=value.force) forge_log_info("[please-do-better] Preference saved: forcing %s",value.force?"enabled":"disabled");
    saved=value.force;have_saved=true;return true;
}
void preferences_changed() { store.changed(); }
bool preferences_pending() { return store.pending; }
const char* preferences_status() { return store.status; }
}
