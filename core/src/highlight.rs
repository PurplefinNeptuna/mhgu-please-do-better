//! Bounded immutable copies and the reward-slot geometry they carry.
use crate::attribution::Reward;
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

#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Binding {
    pub fence: u32,
    pub ui: u32,
    pub batch: u32,
    pub list: u32,
    pub group: u32,
    pub index: u32,
    pub node: u32,
    pub icon: u32,
    pub id: u32,
    pub item: Reward,
}
pub const BINDING_WORDS: usize = 10;

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct Geometry {
    pub binding: Binding,
    pub cycle: u32,
    pub frame: u32,
    pub owner: u32,
    pub serial: u32,
    pub width: f32,
    pub height: f32,
    pub points: [f32; 8],
    pub clip: [f32; 4],
    pub surface: u32,
    /// Zero denotes the default sentinel.
    pub texture: u32,
}
pub const GEOMETRY_WORDS: usize = BINDING_WORDS + 6 + 8 + 4 + 2;

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct Presentation {
    pub cycle: u32,
    pub frame: u32,
    pub owner: u32,
    pub queue: u32,
    pub window: u32,
    pub index: u32,
    pub serial: u32,
    pub texture: u32,
    pub default_texture: u32,
}
pub const PRESENTATION_WORDS: usize = 9;

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

/// Exact XY path of the pinned FGUICalcPosition2D vertex programs. z is retained in the model
/// transform; their depth projection has no influence on XY/W=1.
pub fn screen_quad(vertices: &[f32; 24], model: &[f32; 16], global: &[f32; 4], width: f32, height: f32) -> Option<[f32; 8]> {
    if !width.is_finite() || !height.is_finite() || width <= 0.0 || height <= 0.0 || width > 16384.0 || height > 16384.0 {
        return None;
    }
    if !model.iter().chain(global).all(|v| v.is_finite()) {
        return None;
    }
    let mut out = [0.0; 8];
    for i in 0..4 {
        let (x, y, z) = (vertices[i * 6], vertices[i * 6 + 1], vertices[i * 6 + 2]);
        if !x.is_finite() || !y.is_finite() || !z.is_finite() {
            return None;
        }
        let cx = (model[0] * x + model[4] * y + model[8] * z + model[12]) * global[0] + global[2];
        let cy = (model[1] * x + model[5] * y + model[9] * z + model[13]) * global[1] + global[3];
        out[i * 2] = (cx + 1.0) * width * 0.5;
        out[i * 2 + 1] = (1.0 - cy) * height * 0.5;
        if !out[i * 2].is_finite() || !out[i * 2 + 1].is_finite() || out[i * 2].abs() > 65536.0 || out[i * 2 + 1].abs() > 65536.0 {
            return None;
        }
    }
    let area = (out[2] - out[0]) * (out[5] - out[1]) - (out[3] - out[1]) * (out[4] - out[0]);
    (area.is_finite() && area.abs() > 1.0).then_some(out)
}
