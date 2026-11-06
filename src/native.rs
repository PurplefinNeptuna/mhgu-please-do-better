//! Private kernel wrappers and checked reads. Forge 1.5.1 exports no mapping query, program-ID
//! query or process cache flush; `svc.S` covers those three gaps.
use please_do_better_core::platform::{Kernel, MemoryInfo};

// Horizon's pseudo-handle for this process; nothing owns or closes it.
const CURRENT_PROCESS: u32 = 0xffff8001;

unsafe extern "C" {
    fn pdb_svc_query(info: *mut MemoryInfo, page: *mut u32, address: u64) -> u32;
    fn pdb_svc_get_info(out: *mut u64, id: u32, handle: u32, sub_id: u64) -> u32;
    fn pdb_svc_flush(handle: u32, address: u64, bytes: u64) -> u32;
}
core::arch::global_asm!(include_str!("svc.S"), options(raw));
core::arch::global_asm!(".hidden pdb_svc_query\n.hidden pdb_svc_get_info\n.hidden pdb_svc_flush");

pub struct SvcKernel;
// SAFETY for every call below: outputs are live, correctly sized locals and the handle is the
// current-process pseudo-handle, matching the pinned SVC ABI.
impl Kernel for SvcKernel {
    fn query(&self, address: u64) -> Result<MemoryInfo, u32> {
        let mut info = MemoryInfo::default();
        let mut page = 0;
        match unsafe { pdb_svc_query(&mut info, &mut page, address) } {
            0 => Ok(info),
            rc => Err(rc),
        }
    }
    fn get_info(&self, id: u32, sub_id: u64) -> Result<u64, u32> {
        let mut out = 0;
        match unsafe { pdb_svc_get_info(&mut out, id, CURRENT_PROCESS, sub_id) } {
            0 => Ok(out),
            rc => Err(rc),
        }
    }
    fn flush(&self, address: u64, bytes: u64) -> u32 {
        unsafe { pdb_svc_flush(CURRENT_PROCESS, address, bytes) }
    }
    fn load(&self, address: u32) -> u32 {
        // SAFETY: callers check the mapping first.
        unsafe { core::ptr::read_volatile(address as *const u32) }
    }
}

pub fn word(address: u32) -> u32 {
    // SAFETY: every caller checks the mapping first, or reads a field of a live native object.
    unsafe { core::ptr::read_volatile(address as *const u32) }
}
pub fn byte(address: u32) -> u8 {
    // SAFETY: as for `word`.
    unsafe { core::ptr::read_volatile(address as *const u8) }
}
pub fn half(address: u32) -> u16 {
    // SAFETY: as for `word`.
    unsafe { core::ptr::read_volatile(address as *const u16) }
}
fn checked(address: u32, bytes: u32, permissions: u32) -> bool {
    if address == 0 || address as u64 + bytes as u64 > 0x1_0000_0000 {
        return false;
    }
    let Ok(m) = SvcKernel.query(address as u64) else {
        return false;
    };
    m.permissions & permissions == permissions && m.address <= address as u64 && m.address <= 0x1_0000_0000
        && m.size <= 0x1_0000_0000 - m.address && address as u64 + bytes as u64 <= m.address + m.size
}
pub fn readable(address: u32, bytes: u32) -> bool {
    checked(address, bytes, 1)
}
/// The builder owns this heap array until its paired return; no allocator runs during the mutation.
pub fn writable(address: u32, bytes: u32) -> bool {
    bytes != 0 && checked(address, bytes, 3)
}
pub fn field(address: u32, offset: u32, bytes: u32) -> bool {
    address as u64 + offset as u64 + bytes as u64 <= 0x1_0000_0000 && readable(address.wrapping_add(offset), bytes)
}
/// Copy `bytes` out of game memory; false leaves the destination unspecified.
pub fn copy(address: u32, out: *mut u8, bytes: u32) -> bool {
    if !readable(address, bytes) {
        return false;
    }
    for i in 0..bytes {
        // SAFETY: the source mapping covers the span and the caller owns `out` for `bytes`.
        unsafe { out.add(i as usize).write(byte(address + i)) };
    }
    true
}
pub fn copy_to<T>(address: u32, out: &mut T) -> bool {
    copy(address, (out as *mut T).cast(), core::mem::size_of::<T>() as u32)
}
