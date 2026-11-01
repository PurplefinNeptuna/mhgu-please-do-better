//! Portable reward, preference, publication and install logic. Native calls stay in the plugin.
#![no_std]
pub mod attribution;
pub mod frame;
pub mod highlight;
pub mod hooks;
pub mod mailbox;
pub mod mode;
pub mod platform;
pub mod preferences;
pub mod quantity;
pub mod signatures;

use core::sync::atomic::{AtomicU32, Ordering};

/// Each fixed reason is reported at most once for this process. Never reset.
pub struct Once(AtomicU32);
impl Once {
    pub const fn new() -> Self {
        Self(AtomicU32::new(0))
    }
    pub fn claim(&self, reason: u32) -> bool {
        if reason >= 32 {
            return false;
        }
        let bit = 1u32 << reason;
        self.0.fetch_or(bit, Ordering::Relaxed) & bit == 0
    }
}
impl Default for Once {
    fn default() -> Self {
        Self::new()
    }
}

/// Copy a padding-free value into atomic-sized words; `T` must be exactly `WORDS` words.
pub(crate) fn to_words<T: Copy, const WORDS: usize>(value: &T) -> [u32; WORDS] {
    const { assert!(core::mem::size_of::<T>() == WORDS * 4) };
    // SAFETY: the sizes match and every published type is repr(C) without padding.
    unsafe { core::mem::transmute_copy(value) }
}
pub(crate) fn from_words<T: Copy, const WORDS: usize>(words: &[u32; WORDS]) -> T {
    const { assert!(core::mem::size_of::<T>() == WORDS * 4) };
    // SAFETY: the sizes match and these words were produced from a valid `T`.
    unsafe { core::mem::transmute_copy(words) }
}
