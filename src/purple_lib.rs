//! Optional: Please do Better's settings in Purple-lib's Mod Options and a help topic per setting on that
//! page's own help. Purple-lib calls the plugin's `purplelib_on_register` with its table of
//! functions at start-up; without Purple-lib nothing calls it, this module does nothing and the
//! Plugin UI panel stays the only way to change the settings.
//!
//! Purple-lib calls `get` and `set` inside the game's update, so they only use the lock-free
//! preference request; preference state and the INI stay on the ImGui callbacks, which pick up
//! `EDITED` and `SAVE` in `forge_onImGuiFreeRender`.
use crate::runtime;
use core::ffi::{c_char, c_void};
use core::sync::atomic::{AtomicBool, Ordering};
use core::cell::UnsafeCell;
use please_do_better_core::purple_lib::{self as api, Api, Help, Options, ROW_TEXT, OptionRow, LANGUAGES};

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

// A topic's context is its row index.
extern "C" fn help_title(context: *mut c_void, language: u32) -> *const c_char {
    api::ROW_TEXT[context as usize].name[api::language_index(language)].as_ptr()
}
extern "C" fn help_page(context: *mut c_void, language: u32, index: u32) -> *const c_char {
    api::HELP_TEXT[context as usize][api::language_index(language)].get(index as usize).map_or(core::ptr::null(), |p| p.as_ptr())
}

/// Read-only records of static data; no context is ever dereferenced.
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
const fn topic(row: u32) -> Help {
    Help {
        size: core::mem::size_of::<Help>() as u32,
        context: row as usize as *mut c_void,
        category: api::HELP_CATEGORY,
        page_count: api::HELP_PAGES as u32,
        title: Some(help_title),
        page: Some(help_page),
        open: None,
    }
}
static HELP: Shared<[Help; api::ROWS as usize]> = Shared([topic(api::ROW_FORCE), topic(api::ROW_MULTIPLIER)]);

pub enum Registered {
    /// Purple-lib is older than `API_VERSION`; nothing was registered.
    OlderVersion(u32),
    Refused { options: bool, help: bool },
    Done,
    /// A second call: the first one's registration stands.
    Repeated,
}

/// Register through Purple-lib's table, from `purplelib_on_register`: the one time Purple-lib
/// accepts records, during its first update.
pub fn register(purple: &Api) -> Registered {
    static CALLED: AtomicBool = AtomicBool::new(false);
    // A later Purple-lib still reads these records, by their `size`; an older one lacks the API.
    if purple.version < api::API_VERSION {
        return Registered::OlderVersion(purple.version);
    }
    // Purple-lib keeps the label pointers after the first call, so the table is filled only once.
    if CALLED.swap(true, Ordering::AcqRel) {
        return Registered::Repeated;
    }
    // SAFETY: nothing reads the table before the registration below, and this runs once.
    let table = unsafe { &mut *LABELS.0.get() };
    for (language, rows) in table.iter_mut().enumerate() {
        for (row, slots) in rows.iter_mut().enumerate() {
            for (slot, label) in slots.iter_mut().zip(api::labels(row as u32, language)) {
                *slot = label.as_ptr();
            }
        }
    }
    // The page's help names the page, so it goes in after the page; topics show in this order.
    let options = (purple.add_options)(&OPTIONS.0);
    let help = options && HELP.0.iter().all(|topic| (purple.add_set_help)(&OPTIONS.0, topic));
    if options && help { Registered::Done } else { Registered::Refused { options, help } }
}
