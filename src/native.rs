//! Private kernel wrappers and checked reads. Forge's public API has no mapping query, program-ID
//! query, process cache flush or CodeMemory for a relocated trampoline; `svc.S` covers those gaps.
use core::cell::UnsafeCell;
use please_do_better_core::platform::{Kernel, KernelPlatform, MemoryInfo};

// Horizon's pseudo-handle for this process; nothing owns or closes it.
const CURRENT_PROCESS: u32 = 0xffff8001;

unsafe extern "C" {
    fn pdb_svc_query(info: *mut MemoryInfo, page: *mut u32, address: u64) -> u32;
    fn pdb_svc_get_info(out: *mut u64, id: u32, handle: u32, sub_id: u64) -> u32;
    fn pdb_svc_create(handle: *mut u32, source: *mut u8, bytes: u64) -> u32;
    fn pdb_svc_control(handle: u32, operation: u32, address: u64, bytes: u64, permission: u32) -> u32;
    fn pdb_svc_close(handle: u32) -> u32;
    fn pdb_svc_flush(handle: u32, address: u64, bytes: u64) -> u32;
}
core::arch::global_asm!(include_str!("svc.S"), options(raw));
core::arch::global_asm!(
    ".hidden pdb_svc_query\n.hidden pdb_svc_get_info\n.hidden pdb_svc_create\n.hidden pdb_svc_control\n.hidden pdb_svc_close\n.hidden pdb_svc_flush"
);

// A dedicated page: lending it to CodeMemory must not lend other plugin data.
#[repr(align(4096))]
struct Page(UnsafeCell<[u32; 1024]>);
// SAFETY: only its address is used here; the kernel owns the contents once lent.
unsafe impl Sync for Page {}
static SOURCE_PAGE: Page = Page(UnsafeCell::new([0; 1024]));

pub struct SvcKernel;
// SAFETY for every call below: outputs are live, correctly sized locals and the handle is the
// current-process pseudo-handle or one this platform owns, matching the pinned SVC ABI.
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
    fn flush(&mut self, address: u64, bytes: u64) -> u32 {
        unsafe { pdb_svc_flush(CURRENT_PROCESS, address, bytes) }
    }
    fn create_code(&mut self, source_page: u32, bytes: u64) -> Result<u32, u32> {
        let mut handle = 0;
        match unsafe { pdb_svc_create(&mut handle, source_page as *mut u8, bytes) } {
            0 => Ok(handle),
            rc => Err(rc),
        }
    }
    fn control_code(&mut self, handle: u32, operation: u32, address: u64, bytes: u64, permission: u32) -> u32 {
        unsafe { pdb_svc_control(handle, operation, address, bytes, permission) }
    }
    fn close(&mut self, handle: u32) -> u32 {
        unsafe { pdb_svc_close(handle) }
    }
    fn source_page(&self) -> u32 {
        SOURCE_PAGE.0.get() as u32
    }
    fn load(&self, address: u32) -> u32 {
        // SAFETY: the platform checks the mapping first, or this is its own arena mapping.
        unsafe { core::ptr::read_volatile(address as *const u32) }
    }
    fn store(&mut self, address: u32, value: u32) {
        // SAFETY: the platform checks the mapping and the expected current word first.
        unsafe { core::ptr::write_volatile(address as *mut u32, value) }
    }
}
pub type NativePlatform = KernelPlatform<SvcKernel>;

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
