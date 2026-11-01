//! One producer per native TLS context and one render consumer. Every payload word is atomic, so an
//! overwrite during a read cannot create a data race, and sequential consistency makes the two
//! ticket checks detect a torn snapshot. No wait, lock or retry in publish/read; overflow discards
//! the oldest entry.
use crate::{from_words, to_words};
use core::marker::PhantomData;
use core::sync::atomic::{AtomicU32, Ordering::{Relaxed, SeqCst}};

#[repr(C)]
struct Slot<const WORDS: usize> {
    ticket: AtomicU32,
    data: [AtomicU32; WORDS],
}

#[repr(C)]
pub struct Mailbox<T, const CAPACITY: usize, const WORDS: usize> {
    slots: [Slot<WORDS>; CAPACITY],
    sequence: AtomicU32,
    published: AtomicU32,
    cursor: AtomicU32,
    /// Consumer-owned count of lost entries.
    pub overwritten: AtomicU32,
    _value: PhantomData<T>,
}
impl<T: Copy, const CAPACITY: usize, const WORDS: usize> Mailbox<T, CAPACITY, WORDS> {
    const VALID: () = assert!(CAPACITY.is_power_of_two() && size_of::<T>() == WORDS * 4);
    pub const fn new() -> Self {
        let () = Self::VALID;
        Self {
            slots: [const { Slot { ticket: AtomicU32::new(0), data: [const { AtomicU32::new(0) }; WORDS] } }; CAPACITY],
            sequence: AtomicU32::new(0),
            published: AtomicU32::new(0),
            cursor: AtomicU32::new(0),
            overwritten: AtomicU32::new(0),
            _value: PhantomData,
        }
    }
    pub fn publish(&self, value: &T) {
        let next = self.sequence.load(Relaxed).wrapping_add(1);
        let bits = to_words::<T, WORDS>(value);
        let slot = &self.slots[(next.wrapping_sub(1) as usize) % CAPACITY];
        slot.ticket.store(next << 1 | 1, SeqCst);
        for (word, bit) in slot.data.iter().zip(bits) {
            word.store(bit, SeqCst);
        }
        slot.ticket.store(next << 1, SeqCst);
        self.sequence.store(next, Relaxed);
        self.published.store(next, SeqCst);
    }
    pub fn read(&self) -> Option<T> {
        let head = self.published.load(SeqCst);
        let mut cursor = self.cursor.load(Relaxed);
        if head == cursor {
            return None;
        }
        let behind = head.wrapping_sub(cursor);
        if behind as usize > CAPACITY {
            self.overwritten.fetch_add(behind - CAPACITY as u32, Relaxed);
            cursor = head.wrapping_sub(CAPACITY as u32);
        }
        let next = cursor.wrapping_add(1);
        let expected = next << 1;
        let slot = &self.slots[(next.wrapping_sub(1) as usize) % CAPACITY];
        let ticket = slot.ticket.load(SeqCst);
        self.cursor.store(next, Relaxed);
        if ticket != expected {
            self.overwritten.fetch_add(1, Relaxed);
            return None;
        }
        let bits = core::array::from_fn(|i| slot.data[i].load(SeqCst));
        if slot.ticket.load(SeqCst) != expected {
            self.overwritten.fetch_add(1, Relaxed);
            return None;
        }
        Some(from_words::<T, WORDS>(&bits))
    }
}
impl<T: Copy, const CAPACITY: usize, const WORDS: usize> Default for Mailbox<T, CAPACITY, WORDS> {
    fn default() -> Self {
        Self::new()
    }
}
