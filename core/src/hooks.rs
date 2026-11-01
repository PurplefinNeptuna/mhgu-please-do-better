//! Guarded publication of branch-over hooks. Every word is journaled separately: an intervening
//! external edit is never restored over, even if the other word in that detour still belongs to us.
pub const PROGRAM_ID: u64 = 0x0100770008dd8000;
pub const LDR_PC: u32 = 0xe51ff004;
pub const MAX_HOOKS: usize = 24;
pub const TRAMPOLINE_BYTES: u32 = 32;

#[repr(u32)]
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum State {
    #[default]
    Fresh,
    Applied,
    Rejected,
    RolledBack,
    Unsafe,
}
#[repr(u32)]
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub enum Failure {
    #[default]
    None,
    Program,
    Address,
    Signature,
    Write,
    Cache,
    Readback,
    Changed,
}

#[derive(Clone, Copy, Debug)]
pub struct Hook {
    pub site: u32,
    pub window: u32,
    pub detour: u32,
    pub words: [u32; 8],
    pub paired: bool,
}
impl Hook {
    pub const EMPTY: Self = Self { site: 0, window: 0, detour: 0, words: [0; 8], paired: false };
}

#[derive(Clone, Copy, Debug, Default)]
pub struct HookReport {
    pub state: State,
    pub failure: Failure,
    pub owned: u64,
    pub unsafe_words: u64,
    pub site: u32,
    pub cache: u32,
}

pub trait Platform {
    fn program(&self) -> Option<u64>;
    fn executable(&self, address: u32, bytes: u32) -> bool;
    fn read(&self, address: u32) -> Option<u32>;
    /// Replace `expected`. `stored` reports an actual store even when the readback then fails.
    fn write(&mut self, address: u32, expected: u32, value: u32, stored: &mut bool) -> bool;
    fn sync(&mut self, address: u32, bytes: u32) -> u32;
    fn create(&mut self, bytes: u32) -> bool;
    fn close(&mut self) -> bool;
    fn owns_arena(&self) -> bool;
    fn rx_base(&self) -> u32;
    fn prepare(&mut self, offset: u32, target: u32, first: u32, second: u32) -> bool;
    fn make_executable(&mut self) -> bool;
}

pub struct Hooks {
    recipe: [Hook; MAX_HOOKS],
    base: u32,
    count: usize,
    report: HookReport,
    arena: bool,
}
impl Hooks {
    pub const fn new() -> Self {
        Self {
            recipe: [Hook::EMPTY; MAX_HOOKS],
            base: 0,
            count: 0,
            report: HookReport {
                state: State::Fresh, failure: Failure::None, owned: 0, unsafe_words: 0, site: 0, cache: 0,
            },
            arena: false,
        }
    }
    pub const fn report(&self) -> HookReport {
        self.report
    }
    fn signature<P: Platform>(&self, p: &P, i: usize, installed: bool) -> bool {
        let h = &self.recipe[i];
        (0..8).all(|j| {
            let offset = h.window + j * 4;
            let expected = if installed && offset == h.site {
                LDR_PC
            } else if installed && offset == h.site + 4 {
                h.detour
            } else {
                h.words[j as usize]
            };
            p.read(self.base + offset) == Some(expected)
        })
    }
    fn original_word(&self, i: usize, j: usize) -> u32 {
        self.recipe[i].words[(self.recipe[i].site - self.recipe[i].window) as usize / 4 + j]
    }
    fn close_arena<P: Platform>(&mut self, p: &mut P, state: State) {
        self.report.state = state;
        if self.arena && !p.close() {
            self.report.state = State::Unsafe;
            self.report.unsafe_words = u64::MAX;
        } else {
            self.arena = false;
        }
    }
    fn restore<P: Platform>(&mut self, p: &mut P) {
        for k in (0..self.count * 2).rev() {
            let (i, j) = (k / 2, k % 2);
            let bit = 1u64 << k;
            if self.report.owned & bit == 0 {
                continue;
            }
            let address = self.base + self.recipe[i].site + j as u32 * 4;
            let installed = if j != 0 { self.recipe[i].detour } else { LDR_PC };
            let original = self.original_word(i, j);
            let Some(value) = p.read(address) else {
                self.report.unsafe_words |= bit;
                continue;
            };
            let mut stored = false;
            if value != original && (value != installed || !p.write(address, installed, original, &mut stored)) {
                self.report.unsafe_words |= bit;
                continue;
            }
            let rc = p.sync(address, 4);
            if rc != 0 {
                self.report.cache = rc;
            }
            if rc != 0 || p.read(address) != Some(original) {
                self.report.unsafe_words |= bit;
            } else {
                self.report.owned &= !bit;
            }
        }
        if self.report.unsafe_words != 0 || self.report.owned != 0 {
            self.report.state = State::Unsafe;
        } else {
            self.close_arena(p, State::RolledBack);
        }
    }
    fn fail<P: Platform>(&mut self, p: &mut P, failure: Failure, site: u32) -> HookReport {
        self.report.failure = failure;
        self.report.site = site;
        if self.report.owned != 0 {
            self.restore(p);
        } else {
            self.close_arena(p, State::Rejected);
        }
        self.report
    }
    /// Zero for an unpaired hook, which has no callable original.
    pub fn original<P: Platform>(&self, p: &P, i: usize) -> u32 {
        if self.arena && i < self.count && self.recipe[i].paired {
            p.rx_base() + i as u32 * TRAMPOLINE_BYTES
        } else {
            0
        }
    }
    /// A second call never writes: it rechecks an applied group, so a conflict can be noticed.
    pub fn install<P: Platform>(&mut self, p: &mut P, main: u32, hooks: &[Hook]) -> HookReport {
        if self.report.state != State::Fresh {
            if self.report.state == State::Applied {
                for i in 0..self.count {
                    if !self.signature(p, i, true) {
                        self.report.state = State::Unsafe;
                        self.report.failure = Failure::Changed;
                        self.report.site = i as u32 + 1;
                        self.report.unsafe_words |= 3 << (2 * i);
                        break;
                    }
                }
            }
            return self.report;
        }
        if p.program() != Some(PROGRAM_ID) {
            return self.fail(p, Failure::Program, 0);
        }
        if main == 0 || main & 3 != 0 || hooks.is_empty() || hooks.len() > MAX_HOOKS {
            return self.fail(p, Failure::Address, 0);
        }
        self.base = main;
        self.count = hooks.len();
        let mut need_arena = false;
        for i in 0..hooks.len() {
            self.recipe[i] = hooks[i];
            let h = self.recipe[i];
            let start = main as u64 + h.window as u64;
            if (h.site | h.window | h.detour) & 3 != 0 || h.detour == 0 || h.site < h.window
                || h.site as u64 + 8 > h.window as u64 + 32 || start + 32 > 0x1_0000_0000
                || !p.executable(main + h.window, 32) || h.detour as u64 + 4 > 0x1_0000_0000
                || !p.executable(h.detour, 4)
                || ((h.detour as u64) < start + 32 && start < h.detour as u64 + 4)
                || self.recipe[..i].iter().any(|o| (h.site as u64) < o.site as u64 + 8 && (o.site as u64) < h.site as u64 + 8)
            {
                return self.fail(p, Failure::Address, i as u32 + 1);
            }
            if !self.signature(p, i, false) {
                return self.fail(p, Failure::Signature, i as u32 + 1);
            }
            need_arena = need_arena || h.paired;
        }
        if need_arena {
            if !p.create(4096) {
                self.arena = p.owns_arena();
                return self.fail(p, Failure::Address, 0);
            }
            self.arena = true;
            for i in 0..hooks.len() {
                if self.recipe[i].paired {
                    let target = self.base + self.recipe[i].site;
                    let (first, second) = (self.original_word(i, 0), self.original_word(i, 1));
                    if !p.prepare(i as u32 * TRAMPOLINE_BYTES, target, first, second) {
                        return self.fail(p, Failure::Address, i as u32 + 1);
                    }
                }
            }
            if !p.make_executable() {
                return self.fail(p, Failure::Cache, 0);
            }
        }
        for i in 0..hooks.len() {
            if !self.signature(p, i, false) {
                return self.fail(p, Failure::Signature, i as u32 + 1);
            }
            // Literal first, instruction last. This is startup-only publication.
            for j in [1usize, 0] {
                let mut stored = false;
                let value = if j != 0 { self.recipe[i].detour } else { LDR_PC };
                let address = self.base + self.recipe[i].site + 4 * j as u32;
                let ok = p.write(address, self.original_word(i, j), value, &mut stored);
                if stored {
                    self.report.owned |= 1u64 << (2 * i + j);
                }
                if !ok || !stored {
                    return self.fail(p, Failure::Write, i as u32 + 1);
                }
            }
            self.report.cache = p.sync(self.base + self.recipe[i].site, 8);
            if self.report.cache != 0 {
                return self.fail(p, Failure::Cache, i as u32 + 1);
            }
        }
        for i in 0..hooks.len() {
            if !self.signature(p, i, true) {
                return self.fail(p, Failure::Readback, i as u32 + 1);
            }
        }
        self.report.state = State::Applied;
        self.report
    }
}
impl Default for Hooks {
    fn default() -> Self {
        Self::new()
    }
}
