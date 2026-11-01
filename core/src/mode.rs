//! The published preference word and the primary INI's canonical text.
use core::sync::atomic::{AtomicU32, Ordering};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Preferences {
    pub force: bool,
    pub multiplier: u8,
}
impl Default for Preferences {
    fn default() -> Self {
        Self { force: false, multiplier: 1 }
    }
}

/// One atomic request. Reward scopes latch it; a UI edit never edits instructions. Bit 0 is Luck;
/// bits 1..3 encode multiplier-1. One publication prevents generation from observing half a
/// settings load. Zero means natural 1x.
#[repr(C)]
pub struct Mode {
    requested: AtomicU32,
}
impl Mode {
    pub const fn new() -> Self {
        Self { requested: AtomicU32::new(0) }
    }
    pub fn preferences(&self) -> Preferences {
        let bits = self.requested.load(Ordering::Acquire);
        Preferences { force: bits & 1 != 0, multiplier: ((bits >> 1) + 1) as u8 }
    }
    pub fn force(&self) -> bool {
        self.preferences().force
    }
    pub fn set_force(&self, value: bool) {
        if value {
            self.requested.fetch_or(1, Ordering::Release);
        } else {
            self.requested.fetch_and(!1, Ordering::Release);
        }
    }
    pub fn set(&self, p: Preferences) {
        if !(1..=5).contains(&p.multiplier) {
            return;
        }
        self.requested.store(p.force as u32 | (p.multiplier as u32 - 1) << 1, Ordering::Release);
    }
}
impl Default for Mode {
    fn default() -> Self {
        Self::new()
    }
}

pub const TEXT_CAPACITY: usize = 64;
#[derive(Clone, Copy, Debug)]
pub struct PreferencesText {
    pub bytes: [u8; TEXT_CAPACITY],
    pub size: u32,
}
impl PreferencesText {
    pub const EMPTY: Self = Self { bytes: [0; TEXT_CAPACITY], size: 0 };
    pub fn as_slice(&self) -> &[u8] {
        &self.bytes[..self.size as usize]
    }
}
impl Default for PreferencesText {
    fn default() -> Self {
        Self::EMPTY
    }
}

const TEMPLATE: &[u8] = b"[PleaseDoBetter]\nforce_miraculous=0\nreward_multiplier=1\n";
const FORCE_AT: usize = b"[PleaseDoBetter]\nforce_miraculous=".len();
const MULTIPLIER_AT: usize = b"[PleaseDoBetter]\nforce_miraculous=0\nreward_multiplier=".len();

pub fn encode_preferences(p: Preferences) -> PreferencesText {
    let mut out = PreferencesText::EMPTY;
    if !(1..=5).contains(&p.multiplier) {
        return out;
    }
    out.bytes[..TEMPLATE.len()].copy_from_slice(TEMPLATE);
    out.size = TEMPLATE.len() as u32;
    out.bytes[FORCE_AT] = if p.force { b'1' } else { b'0' };
    out.bytes[MULTIPLIER_AT] = b'0' + p.multiplier;
    out
}

/// The section header is mandatory. Accept only this bounded canonical format. Headerless or older
/// configs use defaults: no migration was chosen, and only Save rewrites the primary.
pub fn decode_preferences(text: &[u8]) -> Option<Preferences> {
    if text.is_empty() || text.len() >= TEXT_CAPACITY {
        return None;
    }
    for force in [false, true] {
        for multiplier in 1..=5 {
            let p = Preferences { force, multiplier };
            if text == encode_preferences(p).as_slice() {
                return Some(p);
            }
        }
    }
    None
}
