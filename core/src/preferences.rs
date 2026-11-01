//! One primary INI on Forge's counted save mount. Never creates, reads or recovers a backup file.
use crate::mode::{Preferences, PreferencesText, decode_preferences, encode_preferences};
use core::ffi::CStr;

pub const PATH: &CStr = c"savedata:/please_do_better.ini";
pub const MOUNT: &CStr = c"savedata";

/// The pinned ARM32 SDK file calls and Forge's save mount. A nonzero result is a failure.
pub trait RawFs {
    /// Open the abort-disabling scope; `leave_scope` restores its token.
    fn enter_scope(&mut self) -> u32;
    fn leave_scope(&mut self, token: u32);
    fn mount(&mut self) -> bool;
    fn unmount(&mut self);
    fn open(&mut self, handle: &mut u32, path: &CStr, mode: i32) -> u32;
    fn close(&mut self, handle: u32);
    fn size(&mut self, out: &mut i64, handle: u32) -> u32;
    fn read(&mut self, handle: u32, offset: i64, out: *mut u8, bytes: u32) -> u32;
    fn write(&mut self, handle: u32, offset: i64, data: *const u8, bytes: u32, flush: &u32) -> u32;
    fn flush(&mut self, handle: u32) -> u32;
    fn resize(&mut self, handle: u32, bytes: i64) -> u32;
    fn create(&mut self, path: &CStr, bytes: i64) -> u32;
    fn commit(&mut self, mount: &CStr) -> u32;
}

fn read_primary<F: RawFs>(fs: &mut F, text: &mut PreferencesText) -> bool {
    let mut handle = 0;
    if fs.open(&mut handle, PATH, 1) != 0 {
        return false;
    }
    let mut size = 0;
    let mut ok = fs.size(&mut size, handle) == 0 && size > 0 && size < text.bytes.len() as i64;
    if ok {
        text.size = size as u32;
        ok = fs.read(handle, 0, text.bytes.as_mut_ptr(), text.size) == 0;
    }
    fs.close(handle);
    ok
}

fn write_primary<F: RawFs>(fs: &mut F, text: &PreferencesText) -> bool {
    if text.size == 0 || text.size as usize >= text.bytes.len() {
        return false;
    }
    let mut handle = 0;
    if fs.open(&mut handle, PATH, 2) != 0
        && (fs.create(PATH, text.size as i64) != 0 || fs.open(&mut handle, PATH, 2) != 0)
    {
        return false;
    }
    let flush = 1;
    let wrote = fs.resize(handle, text.size as i64) == 0
        && fs.write(handle, 0, text.bytes.as_ptr(), text.size, &flush) == 0
        && fs.flush(handle) == 0;
    fs.close(handle);
    let mut check = PreferencesText::EMPTY;
    wrote && read_primary(fs, &mut check) && check.as_slice() == text.as_slice()
}

pub struct PreferenceStore {
    pub pending: bool,
    pub save_failure: u32,
    pub status: &'static CStr,
}
impl PreferenceStore {
    pub const fn new() -> Self {
        Self { pending: true, save_failure: 0, status: c"Default: visual only; not saved." }
    }
    pub fn changed(&mut self) {
        self.pending = false;
        self.status = c"Changed for this session; Save settings remembers the choice.";
    }
    pub fn load<F: RawFs>(&mut self, fs: &mut F) -> Option<Preferences> {
        if !self.pending {
            return None;
        }
        let token = fs.enter_scope();
        let result = self.load_scoped(fs);
        fs.leave_scope(token);
        result
    }
    fn load_scoped<F: RawFs>(&mut self, fs: &mut F) -> Option<Preferences> {
        if !fs.mount() {
            self.status = c"Waiting for player preference storage; visual-only default.";
            return None;
        }
        self.pending = false;
        let mut text = PreferencesText::EMPTY;
        let value = if read_primary(fs, &mut text) { decode_preferences(text.as_slice()) } else { None };
        fs.unmount();
        self.status = if value.is_some() { c"Saved plugin preference loaded." } else { c"No valid saved preference; visual-only default." };
        value
    }
    pub fn save<F: RawFs>(&mut self, fs: &mut F, value: Preferences) -> bool {
        let token = fs.enter_scope();
        let result = self.save_scoped(fs, value);
        fs.leave_scope(token);
        result
    }
    fn save_scoped<F: RawFs>(&mut self, fs: &mut F, value: Preferences) -> bool {
        let text = encode_preferences(value);
        if decode_preferences(text.as_slice()).is_none() {
            return false;
        }
        self.pending = false;
        self.save_failure = 0;
        if !fs.mount() {
            self.save_failure = 1;
            self.status = c"Storage unavailable; session choice retained.";
            return false;
        }
        let saved = write_primary(fs, &text) && fs.commit(MOUNT) == 0;
        fs.unmount();
        if !saved {
            self.save_failure = 2;
            self.status = c"Save failed; session choice retained.";
            return false;
        }
        self.status = c"Saved please_do_better.ini in MHGU's save folder.";
        true
    }
}
impl Default for PreferenceStore {
    fn default() -> Self {
        Self::new()
    }
}
