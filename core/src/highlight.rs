//! Bounded immutable copies and the reward-slot frame layout.
use crate::{from_words, to_words};
use core::marker::PhantomData;
use core::sync::atomic::{AtomicU32, Ordering::SeqCst};

/// Payload words are atomic, including during a rejected concurrent publication; no producer waits
/// for another game thread.
#[repr(C)]
pub struct Snapshot<T, const WORDS: usize> {
    ticket: AtomicU32,
    data: [AtomicU32; WORDS],
    _value: PhantomData<T>,
}
impl<T: Copy, const WORDS: usize> Snapshot<T, WORDS> {
    const VALID: () = assert!(size_of::<T>() == WORDS * 4);
    pub const fn new() -> Self {
        let () = Self::VALID;
        Self { ticket: AtomicU32::new(0), data: [const { AtomicU32::new(0) }; WORDS], _value: PhantomData }
    }
    pub fn publish(&self, value: &T) -> bool {
        let prior = self.ticket.load(SeqCst);
        if prior & 1 != 0 || self.ticket.compare_exchange(prior, prior.wrapping_add(1), SeqCst, SeqCst).is_err() {
            return false;
        }
        for (word, bit) in self.data.iter().zip(to_words::<T, WORDS>(value)) {
            word.store(bit, SeqCst);
        }
        self.ticket.store(prior.wrapping_add(2), SeqCst);
        true
    }
    pub fn read(&self) -> Option<T> {
        let before = self.ticket.load(SeqCst);
        if before == 0 || before & 1 != 0 {
            return None;
        }
        let bits = core::array::from_fn(|i| self.data[i].load(SeqCst));
        if before != self.ticket.load(SeqCst) {
            return None;
        }
        Some(from_words::<T, WORDS>(&bits))
    }
}
impl<T: Copy, const WORDS: usize> Default for Snapshot<T, WORDS> {
    fn default() -> Self {
        Self::new()
    }
}

/// The GUI background frame for a reward icon: `(frame_index, frame_id)`.
pub const fn frame_layout(group: u32, icon_root: u32, background_root: u32, index: u32, icon_index: u32) -> Option<(u32, u32)> {
    if index >= 48 {
        return None;
    }
    let row = index / 8;
    let column = index % 8;
    if icon_index != 2 + 9 * row + column {
        return None;
    }
    if (group == 1 || group == 7) && icon_root == 19 && background_root == 12 {
        return Some((4 + 9 * row + column, 8 + 9 * row + column));
    }
    if group == 2 && icon_root == 43 && background_root == 44 && index < 32 {
        let base = match row {
            0 => 64,
            1 => 17,
            2 => 35,
            _ => 44,
        };
        return Some((6 + 9 * row + column, base + column));
    }
    if (group == 5 || group == 6) && icon_root == 66 && background_root == 65 && index < 16 {
        return Some((4 + 9 * row + column, if row != 0 { 17 } else { 64 } + column));
    }
    None
}
