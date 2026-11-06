//! Mapping, program-ID and cache queries through the private SVC wrappers. Forge 1.5.1 exports no
//! memory query, program ID or process cache flush; `src/svc.S` supplies those three calls.
use crate::hooks::PROGRAM_ID;

pub const PERM_RX: u32 = 5;
const MEMORY_UNMAPPED: u32 = 0;
const U32_END: u64 = 0x1_0000_0000;

/// Kernel query-memory output, including padding, as the SVC wrapper writes it.
#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct MemoryInfo {
    pub address: u64,
    pub size: u64,
    pub kind: u32,
    pub attributes: u32,
    pub permissions: u32,
    pub ipc: u32,
    pub device: u32,
    pub padding: u32,
}
const _: () = assert!(core::mem::size_of::<MemoryInfo>() == 40);

/// The private SVC wrappers and raw word reads. A nonzero result is the kernel's failure code.
pub trait Kernel {
    fn query(&self, address: u64) -> Result<MemoryInfo, u32>;
    fn get_info(&self, id: u32, sub_id: u64) -> Result<u64, u32>;
    fn flush(&self, address: u64, bytes: u64) -> u32;
    fn load(&self, address: u32) -> u32;
}

pub fn is_mhgu<K: Kernel>(k: &K) -> bool {
    k.get_info(18, 0) == Ok(PROGRAM_ID)
}
/// The whole span lies in one mapped region with read and execute permission.
pub fn executable<K: Kernel>(k: &K, address: u32, bytes: u32) -> bool {
    let end = address as u64 + bytes as u64;
    if address == 0 || address & 3 != 0 || bytes == 0 || end > U32_END {
        return false;
    }
    let Ok(info) = k.query(address as u64) else {
        return false;
    };
    info.kind != MEMORY_UNMAPPED && info.permissions & PERM_RX == PERM_RX && info.address <= address as u64
        && info.address <= U32_END && info.size <= U32_END - info.address && end <= info.address + info.size
}
/// Eight words from executable memory, or None.
pub fn window<K: Kernel>(k: &K, address: u32) -> Option<[u32; 8]> {
    executable(k, address, 32).then(|| core::array::from_fn(|i| k.load(address + i as u32 * 4)))
}
/// Barriers around the process data-cache flush. A zero result checks the SVC, not an emulator's
/// translation freshness.
pub fn sync<K: Kernel>(k: &K, address: u32, bytes: u32) -> bool {
    if !executable(k, address, bytes) {
        return false;
    }
    barrier();
    let result = k.flush(address as u64, bytes as u64);
    barrier_isb();
    result == 0
}
fn barrier() {
    #[cfg(target_arch = "arm")]
    // SAFETY: barriers change no memory contents.
    unsafe {
        core::arch::asm!("dsb sy", options(nostack, preserves_flags));
    }
}
fn barrier_isb() {
    #[cfg(target_arch = "arm")]
    // SAFETY: barriers change no memory contents.
    unsafe {
        core::arch::asm!("dsb sy", "isb", options(nostack, preserves_flags));
    }
}
