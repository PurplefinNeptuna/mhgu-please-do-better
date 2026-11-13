//! Optional settings rows and a help topic in Purple-lib (its `API.md`). Purple-lib is looked up
//! by symbol at start-up; without it nothing here runs. The records mirror Purple-lib's API
//! version 1; the row texts and the mapping between rows and `Preferences` are here so the host
//! tests can check them.
use crate::mode::Preferences;
use core::ffi::{CStr, c_char, c_void};

pub const API_VERSION: u32 = 1;
pub const EXPORT_VERSION: &[u8] = b"purplelib_api_version";
pub const EXPORT_ADD_OPTIONS: &[u8] = b"purplelib_add_options";
pub const EXPORT_ADD_HELP: &[u8] = b"purplelib_add_help";

#[repr(C)]
pub struct Row {
    pub name: *const c_char,
    pub help: *const c_char,
    pub labels: *const *const c_char,
    pub label_count: u32,
}

#[repr(C)]
pub struct Options {
    pub size: u32,
    pub context: *mut c_void,
    pub title: Option<extern "C" fn(*mut c_void, u32) -> *const c_char>,
    pub row_count: u32,
    pub row: Option<extern "C" fn(*mut c_void, u32, u32, *mut Row) -> bool>,
    pub get: Option<extern "C" fn(*mut c_void, u32) -> u32>,
    pub set: Option<extern "C" fn(*mut c_void, u32, u32)>,
    pub closed: Option<extern "C" fn(*mut c_void)>,
}

#[repr(C)]
pub struct Help {
    pub size: u32,
    pub context: *mut c_void,
    pub category: u32,
    pub page_count: u32,
    pub title: Option<extern "C" fn(*mut c_void, u32) -> *const c_char>,
    pub page: Option<extern "C" fn(*mut c_void, u32, u32) -> *const c_char>,
    pub open: Option<extern "C" fn(*mut c_void)>,
}

#[cfg(target_pointer_width = "32")]
const _: () = assert!(core::mem::size_of::<Options>() == 32 && core::mem::size_of::<Help>() == 28);

pub const TITLE: &CStr = c"Please do Better";
pub const ROW_FORCE: u32 = 0;
pub const ROW_MULTIPLIER: u32 = 1;
pub const ROWS: u32 = 2;

pub struct RowText {
    pub name: &'static CStr,
    pub help: &'static CStr,
    pub labels: &'static [&'static CStr],
}
/// Purple-lib keeps every pointer it is given, so the rows are static.
pub static ROW_TEXT: [RowText; ROWS as usize] = [
    RowText {
        name: c"Force Miraculous Luck",
        help: c"Use Miraculous Luck the next time rewards are generated.",
        labels: &[c"Off", c"On"],
    },
    RowText {
        name: c"Reward multiplier",
        help: c"Multiply every occupied slot on the player reward pages.",
        labels: &[c"1x", c"2x", c"3x", c"4x", c"5x"],
    },
];

/// The value Purple-lib shows: the label index.
pub fn value(p: Preferences, row: u32) -> u32 {
    match row {
        ROW_FORCE => p.force as u32,
        ROW_MULTIPLIER => p.multiplier.clamp(1, 5) as u32 - 1,
        _ => 0,
    }
}

/// The preferences with one row set to a label index; None for an index out of range.
pub fn with_value(mut p: Preferences, row: u32, value: u32) -> Option<Preferences> {
    match (row, value) {
        (ROW_FORCE, 0..=1) => p.force = value == 1,
        (ROW_MULTIPLIER, 0..=4) => p.multiplier = value as u8 + 1,
        _ => return None,
    }
    Some(p)
}

/// Help topic in Village/Hub (category 18): five lines at most, about 40 characters a line.
pub const HELP_CATEGORY: u32 = 18;
pub static HELP_PAGES: [&CStr; 3] = [
    c"Please do Better marks the extra reward\r\nslots that Luck skills give with a\r\nwhite frame on the reward screen.",
    c"Force Miraculous Luck gives Miraculous\r\nLuck the next time rewards are\r\ngenerated, without changing skills.",
    c"Reward multiplier multiplies every\r\noccupied slot on the player reward\r\npages; the Palico page is unchanged.\r\nBoth are in Options > Mod Options.",
];

/// Reads `out.len()` bytes at `address`, or returns false without touching unmapped memory.
pub trait Memory {
    fn read(&mut self, address: u32, out: &mut [u8]) -> bool;
    fn words<const N: usize>(&mut self, address: u32) -> Option<[u32; N]> {
        let mut raw = [0u8; 64];
        let bytes = &mut raw[..N * 4];
        self.read(address, bytes).then(|| core::array::from_fn(|i| u32::from_le_bytes(bytes[i * 4..i * 4 + 4].try_into().unwrap())))
    }
}

/// A defined symbol of the NRO mapped at `base`. Forge maps an NRO's segments at their file
/// offsets, so the dynamic table (found through the header's MOD0 offset) and every symbol value
/// are offsets from `base`. Imports have value 0 and are never returned. The same reader as the
/// WishFinder bridge for My Weapon Tree.
pub fn nro_symbol(m: &mut impl Memory, base: u32, name: &[u8]) -> Option<u32> {
    if name.is_empty() || name.len() > 40 || m.words::<1>(base + 0x10)?[0] != u32::from_le_bytes(*b"NRO0") {
        return None;
    }
    let mod0 = m.words::<1>(base + 4)?[0];
    let [magic, dynamic] = m.words::<2>(base + mod0)?;
    if magic != u32::from_le_bytes(*b"MOD0") {
        return None;
    }
    let dynamic = mod0.wrapping_add((dynamic as i32) as u32);
    let (mut hash, mut strtab, mut symtab, mut strsz) = (None, None, None, None);
    for i in 0..32u32 {
        let [tag, value] = m.words::<2>(base + dynamic + i * 8)?;
        if tag == 0 {
            break;
        }
        match tag {
            4 => hash = Some(value),
            5 => strtab = Some(value),
            6 => symtab = Some(value),
            10 => strsz = Some(value),
            11 if value != 16 => return None,
            _ => {}
        }
    }
    let (hash, strtab, symtab, strsz) = (hash?, strtab?, symtab?, strsz?);
    let [_, count] = m.words::<2>(base + hash)?;
    if !(2..=4096).contains(&count) || strsz > 0x10_0000 {
        return None;
    }
    let mut needle = [0u8; 41];
    needle[..name.len()].copy_from_slice(name);
    for i in 1..count {
        let [st_name, st_value, _, _] = m.words::<4>(base + symtab + i * 16)?;
        if st_value == 0 || st_name >= strsz {
            continue;
        }
        let mut found = [0u8; 41];
        if !m.read(base + strtab + st_name, &mut found[..name.len() + 1]) {
            return None;
        }
        if found[..=name.len()] == needle[..=name.len()] {
            return Some(base + st_value);
        }
    }
    None
}
