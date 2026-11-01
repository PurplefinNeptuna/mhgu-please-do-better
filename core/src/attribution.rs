//! Which reward slots are extra luck slots, from the rolls the native count routines made.
pub const NORMAL_LUCK: u32 = 22;
pub const REWARD_CAP: u32 = 8;

/// Counterfactual SLOT count only, using the already-observed rolls. This does not predict the
/// item RNG sequence of a second, unmodified game execution.
#[derive(Clone, Copy, Debug)]
pub struct Attribution {
    pub threshold: u32,
    pub normal_stop: u32,
    pub known: bool,
    pub valid: bool,
    pub comparisons: u32,
    pub last_slots: u32,
    pub last_roll: u32,
    pub first_slots: u32,
}
impl Attribution {
    /// An unknown scope: `begin` supplies the threshold and stop when a comparison is observed.
    pub const INACTIVE: Self = Self {
        threshold: 0, normal_stop: 0, known: false, valid: false,
        comparisons: 0, last_slots: 0, last_roll: 0, first_slots: 0,
    };
    pub const fn new() -> Self {
        Self { normal_stop: REWARD_CAP, valid: true, ..Self::INACTIVE }
    }
    pub fn begin(&mut self, tier: u32, first: u32) {
        self.threshold = tier;
        self.normal_stop = REWARD_CAP;
        self.known = true;
        self.first_slots = first;
        self.comparisons = 0;
        self.last_slots = 0;
        self.last_roll = 0;
        self.valid = matches!(tier, 8 | 16 | 22 | 25 | 28 | 31);
    }
    pub fn compare(&mut self, slots: u32, roll: u32) {
        if !self.known || slots >= REWARD_CAP || roll > 31 {
            self.valid = false;
            return;
        }
        if self.comparisons == 0 && self.first_slots != u32::MAX && slots != self.first_slots {
            self.valid = false;
        }
        if self.comparisons != 0 && (self.last_roll >= self.threshold || slots != self.last_slots + 1) {
            self.valid = false;
        }
        self.comparisons += 1;
        self.last_slots = slots;
        self.last_roll = roll;
        if self.valid && self.threshold > NORMAL_LUCK && roll >= NORMAL_LUCK && roll < self.threshold && self.normal_stop == REWARD_CAP {
            self.normal_stop = if slots != 0 { slots } else { 1 };
        }
    }
    pub const fn complete(&self, actual_slots: u32) -> bool {
        if !self.known || !self.valid || actual_slots > REWARD_CAP {
            return false;
        }
        if self.comparisons == 0 {
            return self.first_slots >= REWARD_CAP && self.first_slots != u32::MAX && actual_slots == REWARD_CAP;
        }
        let expected = self.last_slots + if self.last_roll < self.threshold { 1 } else { 0 };
        actual_slots == if expected != 0 { expected } else { 1 } && (self.last_roll >= self.threshold || actual_slots == REWARD_CAP)
    }
    pub const fn mask(&self, actual_slots: u32) -> u32 {
        if !self.known || !self.valid || actual_slots > REWARD_CAP || self.normal_stop >= actual_slots {
            return 0;
        }
        ((1 << actual_slots) - 1) & !((1 << self.normal_stop) - 1)
    }
}
impl Default for Attribution {
    fn default() -> Self {
        Self::new()
    }
}

#[repr(C)]
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Reward {
    pub item: u16,
    pub amount: u16,
}
const _: () = assert!(core::mem::size_of::<Reward>() == 4);

/// Native collection (main+0x388EE8) may reduce quantity or clear both fields. A refresh is checked
/// by index, never by searching for an identical item ID.
pub const fn compatible_refresh(original: Reward, current: Reward) -> bool {
    (current.item == 0 && current.amount == 0)
        || (original.item != 0 && current.item == original.item && current.amount != 0 && current.amount <= original.amount)
}

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct Provenance {
    pub epoch: u32,
    pub array: u32,
    pub count: u32,
    pub mask: u32,
    pub items: [Reward; REWARD_CAP as usize],
}
impl Provenance {
    pub const EMPTY: Self = Self { epoch: 0, array: 0, count: 0, mask: 0, items: [Reward { item: 0, amount: 0 }; 8] };
    pub fn matches(&self, generation: u32, address: u32, index: u32, current: Reward) -> bool {
        self.epoch == generation && self.array == address && self.count <= REWARD_CAP && index < self.count
            && self.mask & (1 << index) != 0 && current.item != 0 && current.item == self.items[index as usize].item
            && current.amount != 0 && current.amount <= self.items[index as usize].amount
    }
}
