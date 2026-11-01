//! The primary INI through Forge's counted save mount and the pinned ARM32 SDK file calls. These SDK
//! exports have one 32-bit FileHandle, the Result in r0, aligned 64-bit offsets and 32-bit byte
//! counts; forge-rs's own `fs` wraps the ARM64-shaped headers, so they are declared here.
use crate::runtime;
use core::cell::UnsafeCell;
use core::ffi::{CStr, c_char};
use forge::sys::fs::{forge_fs_mountSaveData, forge_fs_unmountSaveData};
use please_do_better_core::Once;
use please_do_better_core::mode::Preferences;
use please_do_better_core::preferences::{PreferenceStore, RawFs};

unsafe extern "C" {
    #[link_name = "_ZN2nn2fs23ScopedAutoAbortDisablerC1Ev"]
    fn sdk_disable_abort(out: *mut u32);
    #[link_name = "_ZN2nn2fs25SetCurrentThreadFsContextEPKNS0_9FsContextE"]
    fn sdk_restore_context(token: u32);
    #[link_name = "_ZN2nn2fs14CommitSaveDataEPKc"]
    fn sdk_commit(name: *const c_char) -> u32;
    #[link_name = "_ZN2nn2fs8OpenFileEPNS0_10FileHandleEPKci"]
    fn sdk_open(handle: *mut u32, path: *const c_char, mode: i32) -> u32;
    #[link_name = "_ZN2nn2fs9CloseFileENS0_10FileHandleE"]
    fn sdk_close(handle: u32);
    #[link_name = "_ZN2nn2fs11GetFileSizeEPxNS0_10FileHandleE"]
    fn sdk_size(out: *mut i64, handle: u32) -> u32;
    #[link_name = "_ZN2nn2fs8ReadFileENS0_10FileHandleExPvj"]
    fn sdk_read(handle: u32, offset: i64, out: *mut u8, bytes: u32) -> u32;
    #[link_name = "_ZN2nn2fs9WriteFileENS0_10FileHandleExPKvjRKNS0_11WriteOptionE"]
    fn sdk_write(handle: u32, offset: i64, data: *const u8, bytes: u32, option: *const u32) -> u32;
    #[link_name = "_ZN2nn2fs9FlushFileENS0_10FileHandleE"]
    fn sdk_flush(handle: u32) -> u32;
    #[link_name = "_ZN2nn2fs11SetFileSizeENS0_10FileHandleEx"]
    fn sdk_resize(handle: u32, bytes: i64) -> u32;
    #[link_name = "_ZN2nn2fs10CreateFileEPKcx"]
    fn sdk_create(path: *const c_char, bytes: i64) -> u32;
}

struct SdkFs;
// SAFETY for every call below: the fixed SDK exports above with pointers to live local buffers.
impl RawFs for SdkFs {
    fn enter_scope(&mut self) -> u32 {
        let mut token = 0;
        unsafe { sdk_disable_abort(&mut token) };
        token
    }
    fn leave_scope(&mut self, token: u32) {
        unsafe { sdk_restore_context(token) };
    }
    fn mount(&mut self) -> bool {
        unsafe { forge_fs_mountSaveData() }
    }
    fn unmount(&mut self) {
        unsafe { forge_fs_unmountSaveData() };
    }
    fn open(&mut self, handle: &mut u32, path: &CStr, mode: i32) -> u32 {
        unsafe { sdk_open(handle, path.as_ptr(), mode) }
    }
    fn close(&mut self, handle: u32) {
        unsafe { sdk_close(handle) };
    }
    fn size(&mut self, out: &mut i64, handle: u32) -> u32 {
        unsafe { sdk_size(out, handle) }
    }
    fn read(&mut self, handle: u32, offset: i64, out: *mut u8, bytes: u32) -> u32 {
        unsafe { sdk_read(handle, offset, out, bytes) }
    }
    fn write(&mut self, handle: u32, offset: i64, data: *const u8, bytes: u32, flush: &u32) -> u32 {
        unsafe { sdk_write(handle, offset, data, bytes, flush) }
    }
    fn flush(&mut self, handle: u32) -> u32 {
        unsafe { sdk_flush(handle) }
    }
    fn resize(&mut self, handle: u32, bytes: i64) -> u32 {
        unsafe { sdk_resize(handle, bytes) }
    }
    fn create(&mut self, path: &CStr, bytes: i64) -> u32 {
        unsafe { sdk_create(path.as_ptr(), bytes) }
    }
    fn commit(&mut self, mount: &CStr) -> u32 {
        unsafe { sdk_commit(mount.as_ptr()) }
    }
}

struct State {
    store: PreferenceStore,
    saved: Option<Preferences>,
    retry: u32,
}
struct Shared(UnsafeCell<State>);
// SAFETY: confined to the ImGui callbacks, which Forge runs on one thread.
unsafe impl Sync for Shared {}
static STATE: Shared = Shared(UnsafeCell::new(State { store: PreferenceStore::new(), saved: None, retry: 59 }));
static FAILURES: Once = Once::new();

#[allow(clippy::mut_from_ref)]
fn state() -> &'static mut State {
    // SAFETY: see `Shared`; each use below ends before the next begins.
    unsafe { &mut *STATE.0.get() }
}

pub fn changed() {
    state().store.changed();
}
pub fn status() -> &'static CStr {
    state().store.status
}
pub fn save(value: Preferences) {
    let s = state();
    if !s.store.save(&mut SdkFs, value) {
        if FAILURES.claim(s.store.save_failure) {
            let status = s.store.status.to_str().unwrap_or("");
            log::warn!("[please-do-better] {status} Load a player save and retry Save settings.");
        }
        return;
    }
    if s.saved != Some(value) {
        let luck = if value.force { "on" } else { "off" };
        log::info!("[please-do-better] Saved: luck {luck}, quantities {}x", value.multiplier);
    }
    s.saved = Some(value);
}
/// Retry about once a second until a save is loaded, since storage appears only with a player save.
pub fn retry_load() {
    let s = state();
    if !s.store.pending {
        return;
    }
    s.retry += 1;
    if s.retry >= 60 {
        s.retry = 0;
        if let Some(p) = s.store.load(&mut SdkFs) {
            runtime::request_preferences(p);
        }
    }
}
