//! Reward page bounds for the multiplier.
use crate::attribution::Reward;

pub const FIRST_SCREEN_CAPACITY: usize = 48;
/// Verified uUIResult constructor (main+0x3839BC) allocates these capacities. Page 0 also has
/// 16-entry arena layouts. Page 3 belongs to companion Palicoes.
pub const PLAYER_PAGE_CAPACITIES: [u32; 3] = [48, 48, 8];
pub const PALICO_PAGE_CAPACITY: u32 = 32;

#[repr(u32)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum QuantityFault {
    None,
    Memory,
    Record,
    Overflow,
    Generation,
    Snapshot,
    Multiplier,
}

/// Collection/appraisal consumes amounts as signed shorts. Keep the multiplied value <= 32767 rather
/// than allowing an apparently valid u16 to become negative. Validate every record before writing
/// any, including empty item/amount pairs. `items` holds at least `count` entries once count fits.
pub fn quantity_preflight(items: &[Reward], count: u32, multiplier: u32) -> QuantityFault {
    if !(1..=5).contains(&multiplier) {
        return QuantityFault::Multiplier;
    }
    if count as usize > FIRST_SCREEN_CAPACITY {
        return QuantityFault::Memory;
    }
    for item in &items[..count as usize] {
        if (item.item != 0) != (item.amount != 0) {
            return QuantityFault::Record;
        }
        if item.amount as u32 * multiplier > 32767 {
            return QuantityFault::Overflow;
        }
    }
    QuantityFault::None
}
