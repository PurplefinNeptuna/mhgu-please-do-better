#include "settings.h"
#include "preferences.h"
#include "sdk_fs.h"
#include <forge/fs.h>
namespace pdb {
static constexpr const char* paths[] = {"savedata:/please_do_better.ini", "savedata:/please_do_better_backup.ini"};
struct Files {
    FsAbortGuard abort;
    bool mount() { return forge_fs_mountSaveData(); }
    void unmount() { forge_fs_unmountSaveData(); }
    bool read(unsigned slot, PreferencesText& text) {
        uint32_t handle = 0;
        if (slot > 1 || pdb_fs_open(&handle, paths[slot], 1)) return false;
        int64_t size = 0;
        bool ok = !pdb_fs_size(&size, handle) && size > 0 && size < int64_t(sizeof(text.bytes));
        if (ok) { text.size = unsigned(size); ok = !pdb_fs_read(handle, 0, text.bytes, text.size); }
        pdb_fs_close(handle); return ok;
    }
    bool write(unsigned slot, const PreferencesText& text) {
        if (slot > 1 || !text.size || text.size >= sizeof(text.bytes)) return false;
        uint32_t handle = 0;
        if (pdb_fs_open(&handle, paths[slot], 2) &&
            (pdb_fs_create(paths[slot], text.size) || pdb_fs_open(&handle, paths[slot], 2))) return false;
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
bool save_preferences(Preferences value) { Files files; return store.save(files, value); }
void preferences_changed() { store.changed(); }
bool preferences_pending() { return store.pending; }
const char* preferences_status() { return store.status; }
}
