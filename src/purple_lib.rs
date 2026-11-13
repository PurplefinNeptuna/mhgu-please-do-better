//! Optional: Please do Better's settings in Purple-lib's Mod Options and a help topic on that
//! page's own help. Purple-lib is found by its exported symbols at start-up (Forge has no plugin
//! symbol lookup and `nn::ro::LookupSymbol` sees only the game's modules); without it this module
//! does nothing and the Plugin UI panel stays the only way to change the settings.
//!
//! Purple-lib calls `get` and `set` inside the game's update, so they only use the lock-free
//! preference request; preference state and the INI stay on the ImGui callbacks, which pick up
//! `EDITED` and `SAVE` in `forge_onImGuiFreeRender`.
use crate::native::SvcKernel;
use crate::runtime;
use core::ffi::{c_char, c_void};
use core::sync::atomic::{AtomicBool, Ordering};
use please_do_better_core::platform::Kernel;
use core::cell::UnsafeCell;
use please_do_better_core::purple_lib::{self as api, Help, Memory, Options, ROW_TEXT, OptionRow, LANGUAGES};

/// A value changed through Mod Options: the settings row must drop any pending load.
pub static EDITED: AtomicBool = AtomicBool::new(false);
/// Mod Options closed after a change: save the INI.
pub static SAVE: AtomicBool = AtomicBool::new(false);

extern "C" fn title(_: *mut c_void, _: u32) -> *const c_char {
    api::TITLE.as_ptr()
}

/// Label pointer arrays per language and row, filled once in `register` before Purple-lib can call
/// `row` (Purple-lib keeps the pointers).
struct Labels(UnsafeCell<[[[*const c_char; 5]; api::ROWS as usize]; LANGUAGES]>);
// SAFETY: written once before registration, read-only afterwards.
unsafe impl Sync for Labels {}
static LABELS: Labels = Labels(UnsafeCell::new([[[core::ptr::null(); 5]; api::ROWS as usize]; LANGUAGES]));

extern "C" fn row(_: *mut c_void, language: u32, index: u32, out: *mut OptionRow) -> bool {
    let Some(text) = ROW_TEXT.get(index as usize) else { return false };
    if out.is_null() {
        return false;
    }
    let language = api::language_index(language);
    // SAFETY: filled before registration and never written again.
    let labels = unsafe { &(*LABELS.0.get())[language][index as usize] };
    // SAFETY: Purple-lib passes a writable `OptionRow`.
    unsafe {
        (*out).name = text.name[language].as_ptr();
        (*out).help = text.help[language].as_ptr();
        (*out).labels = labels.as_ptr();
        (*out).label_count = api::labels(index, language).len() as u32;
    }
    true
}

extern "C" fn get(_: *mut c_void, index: u32) -> u32 {
    api::value(runtime::requested_preferences(), index)
}

/// Applied at once through the same request the settings row uses.
extern "C" fn set(_: *mut c_void, index: u32, value: u32) {
    if let Some(p) = api::with_value(runtime::requested_preferences(), index, value) {
        runtime::request_preferences(p);
        EDITED.store(true, Ordering::Release);
    }
}

extern "C" fn closed(_: *mut c_void) {
    SAVE.store(true, Ordering::Release);
}

extern "C" fn help_title(_: *mut c_void, _: u32) -> *const c_char {
    api::TITLE.as_ptr()
}
extern "C" fn help_page(_: *mut c_void, language: u32, index: u32) -> *const c_char {
    api::HELP_TEXT[api::language_index(language)].get(index as usize).map_or(core::ptr::null(), |p| p.as_ptr())
}

/// Read-only records of static data; the null context is never dereferenced.
struct Shared<T>(T);
// SAFETY: see above.
unsafe impl<T> Sync for Shared<T> {}
static OPTIONS: Shared<Options> = Shared(Options {
    size: core::mem::size_of::<Options>() as u32,
    context: core::ptr::null_mut(),
    title: Some(title),
    row_count: api::ROWS,
    row: Some(row),
    get: Some(get),
    set: Some(set),
    closed: Some(closed),
    value_text: None,
    action: None,
});
static HELP: Shared<Help> = Shared(Help {
    size: core::mem::size_of::<Help>() as u32,
    context: core::ptr::null_mut(),
    category: api::HELP_CATEGORY,
    page_count: api::HELP_PAGES as u32,
    title: Some(help_title),
    page: Some(help_page),
    open: None,
});

/// This process's memory, read only after the whole range is found in readable mappings.
struct Process;
impl Memory for Process {
    fn read(&mut self, address: u32, out: &mut [u8]) -> bool {
        if !crate::native::readable(address, out.len() as u32) {
            return false;
        }
        for (i, byte) in out.iter_mut().enumerate() {
            // SAFETY: the range was found mapped readable above.
            *byte = unsafe { core::ptr::read_volatile((address as usize + i) as *const u8) };
        }
        true
    }
}

/// Purple-lib's mapping: the readable and executable mapping that starts with an NRO header and
/// defines `purplelib_api_version`.
fn find() -> Option<u32> {
    let mut address = 0u64;
    for _ in 0..65536 {
        let info = SvcKernel.query(address).ok()?;
        if info.size == 0 || info.address + info.size >= 0x1_0000_0000 {
            return None;
        }
        if info.permissions & 5 == 5 && api::nro_symbol(&mut Process, info.address as u32, api::EXPORT_VERSION).is_some() {
            return Some(info.address as u32);
        }
        address = info.address + info.size;
    }
    None
}

pub enum Registered {
    Missing,
    /// Purple-lib is older than `API_VERSION`; nothing was registered.
    OlderVersion(u32),
    Refused { options: bool, help: bool },
    Done,
}

/// Register with Purple-lib, from `forge_onInit` (Purple-lib accepts registrations until its
/// first update, whatever order the plugins load in).
pub fn register() -> Registered {
    let Some(base) = find() else { return Registered::Missing };
    // SAFETY: nothing reads the table before the registration below.
    let table = unsafe { &mut *LABELS.0.get() };
    for (language, rows) in table.iter_mut().enumerate() {
        for (row, slots) in rows.iter_mut().enumerate() {
            for (slot, label) in slots.iter_mut().zip(api::labels(row as u32, language)) {
                *slot = label.as_ptr();
            }
        }
    }
    let lookup = |name| api::nro_symbol(&mut Process, base, name);
    let (Some(version), Some(add_options), Some(add_set_help)) =
        (lookup(api::EXPORT_VERSION), lookup(api::EXPORT_ADD_OPTIONS), lookup(api::EXPORT_ADD_SET_HELP))
    else {
        return Registered::Missing;
    };
    // SAFETY: Purple-lib's exports of these C signatures (its API.md), at their loaded addresses.
    let version = unsafe { core::mem::transmute::<usize, extern "C" fn() -> u32>(version as usize) }();
    // A later Purple-lib still reads these records, by their `size`; an older one lacks the API.
    if version < api::API_VERSION {
        return Registered::OlderVersion(version);
    }
    let add_options = unsafe { core::mem::transmute::<usize, extern "C" fn(*const Options) -> bool>(add_options as usize) };
    let add_set_help =
        unsafe { core::mem::transmute::<usize, extern "C" fn(*const Options, *const Help) -> bool>(add_set_help as usize) };
    // The page's help names the page, so it goes in after the page.
    let options = add_options(&OPTIONS.0);
    let help = options && add_set_help(&OPTIONS.0, &HELP.0);
    if options && help { Registered::Done } else { Registered::Refused { options, help } }
}
