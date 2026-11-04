//! The Horizon-backed hook platform: checked mappings, direct publication and a private CodeMemory
//! arena. Forge copies a target's first eight bytes without relocating them, and the entry of
//! main+0x381fec has `ldr r0,[pc,#0x108]` as its second word, so Forge's own trampolines cannot
//! hook it. This arena relocates exactly that literal; every other prologue is checked instead.
use crate::hooks::{LDR_PC, Platform};

pub const PERM_RW: u32 = 3;
pub const PERM_RX: u32 = 5;
const MEMORY_UNMAPPED: u32 = 0;
const MAP_OWNER: u32 = 0;
const MAP_SLAVE: u32 = 1;
const UNMAP_OWNER: u32 = 2;
const UNMAP_SLAVE: u32 = 3;
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

/// The private SVC wrappers and raw word accesses. A nonzero result is the kernel's failure code.
pub trait Kernel {
    fn query(&self, address: u64) -> Result<MemoryInfo, u32>;
    fn get_info(&self, id: u32, sub_id: u64) -> Result<u64, u32>;
    fn flush(&mut self, address: u64, bytes: u64) -> u32;
    fn create_code(&mut self, source_page: u32, bytes: u64) -> Result<u32, u32>;
    fn control_code(&mut self, handle: u32, operation: u32, address: u64, bytes: u64, permission: u32) -> u32;
    fn close(&mut self, handle: u32) -> u32;
    /// The dedicated page lent to CodeMemory, so no other plugin data is lent with it.
    fn source_page(&self) -> u32;
    fn load(&self, address: u32) -> u32;
    fn store(&mut self, address: u32, value: u32);
}

pub struct KernelPlatform<K> {
    pub kernel: K,
    handle: u32,
    rw: u32,
    rx: u32,
    owner_mapped: bool,
    slave_mapped: bool,
}

impl<K: Kernel> KernelPlatform<K> {
    pub const fn new(kernel: K) -> Self {
        Self { kernel, handle: 0, rw: 0, rx: 0, owner_mapped: false, slave_mapped: false }
    }
    fn region(&self, address_info: u32, size_info: u32) -> Option<(u64, u64)> {
        let address = self.kernel.get_info(address_info, 0).ok()?;
        let size = self.kernel.get_info(size_info, 0).ok()?;
        (address <= U32_END && size <= U32_END - address).then_some((address, address + size))
    }
    /// Match pinned libnx virtmemFindCodeMemory: ASLR space, excluding alias and heap reservations.
    /// The kernel is the authority for mapping availability. Callers establish the boot boundary.
    fn unused_page(&self) -> u32 {
        let (Some(aslr), Some(alias), Some(heap)) = (self.region(12, 13), self.region(2, 3), self.region(4, 5)) else {
            return 0;
        };
        if aslr.1 - aslr.0 < 4096 {
            return 0;
        }
        let mut cursor = (aslr.0 + 4095) & !4095;
        if cursor == 0 {
            cursor = 4096;
        }
        'search: while cursor + 4096 <= aslr.1 {
            for excluded in [alias, heap] {
                if cursor < excluded.1 && excluded.0 < cursor + 4096 {
                    cursor = (excluded.1 + 4095) & !4095;
                    continue 'search;
                }
            }
            let Ok(info) = self.kernel.query(cursor) else {
                return 0;
            };
            if info.address > U32_END || info.size > U32_END - info.address {
                return 0;
            }
            let end = info.address + info.size;
            if info.address > cursor || end <= cursor || end > U32_END {
                return 0;
            }
            if info.kind == MEMORY_UNMAPPED && end - cursor >= 4096 {
                return cursor as u32;
            }
            cursor = (end + 4095) & !4095;
        }
        0
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
}

impl<K: Kernel> Platform for KernelPlatform<K> {
    fn program(&self) -> Option<u64> {
        self.kernel.get_info(18, 0).ok()
    }
    fn executable(&self, address: u32, bytes: u32) -> bool {
        let end = address as u64 + bytes as u64;
        if address == 0 || address & 3 != 0 || bytes == 0 || end > U32_END {
            return false;
        }
        let Ok(info) = self.kernel.query(address as u64) else {
            return false;
        };
        info.kind != MEMORY_UNMAPPED && info.permissions & PERM_RX == PERM_RX && info.address <= address as u64
            && info.address <= U32_END && info.size <= U32_END - info.address && end <= info.address + info.size
    }
    fn read(&self, address: u32) -> Option<u32> {
        self.executable(address, 4).then(|| self.kernel.load(address))
    }
    fn write(&mut self, address: u32, expected: u32, value: u32, stored: &mut bool) -> bool {
        *stored = false;
        if self.read(address) != Some(expected) {
            return false;
        }
        // Emulator-only direct publication, matching Forge's own store to code. The RX query
        // checks mapping identity; it does not grant native Switch writes.
        self.kernel.store(address, value);
        *stored = true;
        self.read(address) == Some(value)
    }
    fn sync(&mut self, address: u32, bytes: u32) -> u32 {
        if !self.executable(address, bytes) {
            return u32::MAX; // private invalid-range sentinel
        }
        Self::barrier();
        let result = self.kernel.flush(address as u64, bytes as u64);
        Self::barrier_isb();
        // A zero result checks the SVC, not Eden translation freshness.
        result
    }
    fn create(&mut self, bytes: u32) -> bool {
        if bytes != 4096 || self.handle != 0 || self.owner_mapped || self.slave_mapped {
            return false;
        }
        // Cleanup of failed preparation happens here, before reporting failure. On cleanup failure
        // keep the handle owned; never retry or reuse it.
        let page = self.kernel.source_page();
        match self.kernel.create_code(page, 4096) {
            Ok(handle) => self.handle = handle,
            // The SVC wrapper stores its output even on failure; it is not an owned handle.
            Err(_) => return false,
        }
        self.rw = self.unused_page();
        if self.rw == 0 || self.kernel.control_code(self.handle, MAP_OWNER, self.rw as u64, 4096, PERM_RW) != 0 {
            self.close();
            return false;
        }
        self.owner_mapped = true;
        self.rx = self.unused_page();
        if self.rx == 0 || self.kernel.control_code(self.handle, MAP_SLAVE, self.rx as u64, 4096, PERM_RX) != 0 {
            self.close();
            return false;
        }
        self.slave_mapped = true;
        true
    }
    fn close(&mut self) -> bool {
        // All mappings must be gone before closing or reclaiming the backing page.
        if self.slave_mapped {
            if self.kernel.control_code(self.handle, UNMAP_SLAVE, self.rx as u64, 4096, 0) != 0 {
                return false;
            }
            self.slave_mapped = false;
        }
        if self.owner_mapped {
            if self.kernel.control_code(self.handle, UNMAP_OWNER, self.rw as u64, 4096, 0) != 0 {
                return false;
            }
            self.owner_mapped = false;
        }
        if self.handle != 0 && self.kernel.close(self.handle) != 0 {
            return false;
        }
        self.handle = 0;
        self.rw = 0;
        self.rx = 0;
        true
    }
    fn owns_arena(&self) -> bool {
        self.handle != 0
    }
    fn rx_base(&self) -> u32 {
        self.rx
    }
    fn prepare(&mut self, offset: u32, target: u32, first: u32, second: u32) -> bool {
        if !self.owner_mapped || offset > 4096 - 32 || offset & 31 != 0 {
            return false;
        }
        let mut words = [first, second, LDR_PC, target.wrapping_add(8), 0, 0, 0, 0];
        // Only this pinned entry's PC-relative literal is relocated. Snapshot its original data
        // cell before publication; no general instruction rewriting.
        if first == 0xe92d4070 && second == 0xe59f0108 {
            let literal = target as u64 + 12 + (second & 4095) as u64;
            if literal + 4 > U32_END {
                return false;
            }
            let Some(value) = self.read(literal as u32) else {
                return false;
            };
            words[1] = 0xe59f000c;
            words[6] = value;
        } else if first != LDR_PC {
            // A foreign Forge branch moves as it stands: its literal travels with it.
            let push = first & 0xffff_0000 == 0xe92d_0000 && first & 0xa000 == 0;
            let stack = second & 0xffff_f000 == 0xe24d_d000;
            let moved = second & 0xffff_0ff0 == 0xe1a0_0000 && (second >> 12) & 15 != 15 && second & 15 != 15;
            let load = first == 0xe92d4830 && second == 0xe5913004;
            if !push || !(stack || moved || load) {
                return false;
            }
        }
        for (i, &word) in words.iter().enumerate() {
            self.kernel.store(self.rw + offset + i as u32 * 4, word);
        }
        words.iter().enumerate().all(|(i, &word)| self.kernel.load(self.rw + offset + i as u32 * 4) == word)
    }
    fn make_executable(&mut self) -> bool {
        if !self.owner_mapped || !self.slave_mapped {
            return false;
        }
        Self::barrier();
        let result = self.kernel.flush(self.rw as u64, 4096);
        Self::barrier_isb();
        result == 0
    }
}
