//! Stack image shared with gateway.S. Native AArch32 routines use VFP argument registers even
//! though the plugin is compiled with a soft-float ABI, so the gateway keeps their bits.
#[repr(C)]
pub struct RawFrame {
    pub target: u32,
    pub spare: u32,
    pub cpsr: u32,
    pub fpscr: u32,
    pub high_d: [u64; 16],
    pub low_d: [u64; 16],
    /// r0-r12, lr
    pub r: [u32; 14],
}
const _: () = assert!(core::mem::size_of::<RawFrame>() == 328);
const _: () = assert!(
    core::mem::offset_of!(RawFrame, cpsr) == 8
        && core::mem::offset_of!(RawFrame, fpscr) == 12
        && core::mem::offset_of!(RawFrame, high_d) == 16
        && core::mem::offset_of!(RawFrame, low_d) == 144
        && core::mem::offset_of!(RawFrame, r) == 272
);

impl RawFrame {
    /// CMP's NZCV for `a - b`, leaving Q and GE untouched.
    pub fn comparison_flags(&mut self, a: u32, b: u32) {
        self.cpsr = (self.cpsr & 0x0fff_ffff) | comparison_nzcv(a, b);
    }
}
pub const fn comparison_nzcv(a: u32, b: u32) -> u32 {
    let result = a.wrapping_sub(b);
    (result & 0x8000_0000)
        | if result == 0 { 0x4000_0000 } else { 0 }
        | if a >= b { 0x2000_0000 } else { 0 }
        | if (a ^ b) & (a ^ result) & 0x8000_0000 != 0 { 0x1000_0000 } else { 0 }
}
