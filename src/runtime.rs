//! Gateway logic. `pdb_gateway_dispatch` and `pdb_gateway_leave` run inside native routines on any
//! game thread: no locks, no I/O, no logging. Only fixed atomics and immutable snapshots cross to
//! Forge callbacks, which do the formatting.
use crate::native::{SvcKernel, copy, copy_to, field, half, readable, word, writable};
use core::cell::UnsafeCell;
use core::ffi::c_void;
use forge::patch::Patch;
use core::sync::atomic::{AtomicBool, AtomicU32, Ordering::{AcqRel, Acquire, Relaxed, Release}};
use please_do_better_core::Once;
use please_do_better_core::attribution::{Attribution, Provenance, Reward, compatible_refresh};
use please_do_better_core::frame::RawFrame;
use please_do_better_core::highlight::*;
use please_do_better_core::hooks::{Hook, LDR_PC, trampoline_matches, valid_recipe, window_matches};
use please_do_better_core::mailbox::Mailbox;
use please_do_better_core::mode::{Mode, Preferences};
use please_do_better_core::platform;
use please_do_better_core::quantity::*;
use please_do_better_core::signatures::{SITES, VERTEX_COLOR, site_offset};

unsafe extern "C" {
    fn pdb_gateway_0();
    fn pdb_gateway_1();
    fn pdb_gateway_2();
    fn pdb_gateway_3();
    fn pdb_gateway_4();
    fn pdb_gateway_5();
    fn pdb_gateway_6();
    fn pdb_gateway_7();
    fn pdb_gateway_8();
    fn pdb_gateway_9();
    fn pdb_gateway_10();
    fn pdb_gateway_11();
    fn pdb_gateway_12();
    fn pdb_gateway_13();
    fn pdb_gateway_14();
    fn pdb_gateway_15();
    fn pdb_gateway_16();
    fn pdb_gateway_19();
    fn pdb_gateway_20();
    fn pdb_gateway_21();
    fn pdb_gateway_22();
    fn pdb_gateway_23();
    fn pdb_gateway_24();
    fn pdb_gateway_25();
    fn pdb_gateway_after();
    fn pdb_main_count_original();
    // Verified against the fingerprinted MHGU 1.4.0 SDK, not Forge's Result-return declaration for
    // SetTlsValue. The wrapper resolves to the void native setter at SDK + 0x9d80c.
    fn nnosAllocateTlsSlot(slot: *mut i32, destructor: *const c_void) -> u32;
    fn nnosGetTlsValue(slot: i32) -> *mut c_void;
    fn nnosSetTlsValue(slot: i32, value: *mut c_void);
    // Immutable thread identity lets an already-entered paired scope return safely if its reserved
    // TLS value is lost. Pinned SDK body: MRC, LDR +0x1fc, BX LR.
    #[link_name = "_ZN2nn2os16GetCurrentThreadEv"]
    fn pdb_current_thread() -> *mut c_void;
}
core::arch::global_asm!(include_str!("gateway.S"), options(raw));

fn gateway(index: usize) -> u32 {
    let table: [unsafe extern "C" fn(); 22] = [
        pdb_gateway_0, pdb_gateway_1, pdb_gateway_2, pdb_gateway_3, pdb_gateway_4, pdb_gateway_5, pdb_gateway_6,
        pdb_gateway_7, pdb_gateway_8, pdb_gateway_9, pdb_gateway_10, pdb_gateway_11, pdb_gateway_12, pdb_gateway_13,
        pdb_gateway_14, pdb_gateway_15, pdb_gateway_16, pdb_gateway_21, pdb_gateway_22, pdb_gateway_23, pdb_gateway_24,
        pdb_gateway_25,
    ];
    table[index] as *const () as u32
}
fn hook(index: usize) -> Hook {
    Hook { detour: gateway(index), ..SITES[index] }
}

#[repr(C)]
#[derive(Clone, Copy, Debug, Default)]
pub struct Record {
    ui: u32,
    epoch: u32,
    tier: u32,
    kind: u32,
    generated: u32,
    coverage: u32,
    rewards: Provenance,
}
const RECORD_WORDS: usize = 6 + 4 + 8;
const EMPTY_RECORD: Record = Record { ui: 0, epoch: 0, tier: 0, kind: 0, generated: 0, coverage: 0, rewards: Provenance::EMPTY };

#[derive(Clone, Copy)]
struct CountSnapshot {
    attribution: Attribution,
    slots: u32,
    ready: bool,
}
const NO_COUNT: CountSnapshot = CountSnapshot { attribution: Attribution::INACTIVE, slots: 0, ready: false };

#[derive(Clone, Copy, Default)]
struct QuantityPage {
    array: u32,
    count: u32,
}

#[derive(Clone, Copy)]
struct Scope {
    kind: u32,
    caller: u32,
    sp: u32,
    subject: u32,
    array: u32,
    count: u32,
    force: bool,
    // Entry always assigns a latched 1..5 value before this scope can be used.
    multiplier: u8,
    quantity_ready: bool,
    player_blank: bool,
    quantity_done: bool,
    quantity_pages: [QuantityPage; 3],
    attribution: Attribution,
    epoch: u32,
    ui: u32,
    pending: [Record; 8],
    pending_count: usize,
    counts: [CountSnapshot; 3],
    counted: u32,
    copied: u32,
    incomplete: bool,
}
const EMPTY_SCOPE: Scope = Scope {
    kind: 0, caller: 0, sp: 0, subject: 0, array: 0, count: 0, force: false, multiplier: 0,
    quantity_ready: false, player_blank: false, quantity_done: false,
    quantity_pages: [QuantityPage { array: 0, count: 0 }; 3],
    attribution: Attribution::INACTIVE, epoch: 0, ui: 0, pending: [EMPTY_RECORD; 8], pending_count: 0,
    counts: [NO_COUNT; 3], counted: 0, copied: 0, incomplete: false,
};

/// Touched only by the thread whose identity claimed the context.
struct Producer {
    depth: usize,
    quarantine: bool,
    tls_lost: bool,
    serial: u32,
    last_ui: u32,
    // A uUIResult owns one result generation. Its destructor hook clears this latch before the
    // address can be reused for another quest. Mark even 1x and failed attempts: later settings or
    // rebuilds cannot alter it.
    quantity_ui: u32,
    scopes: [Scope; 4],
}
struct Context {
    cookie: AtomicU32,
    producer: UnsafeCell<Producer>,
    records: Mailbox<Record, 16, RECORD_WORDS>,
}
// SAFETY: `producer` is confined to its claiming thread; everything else is atomic.
unsafe impl Sync for Context {}
const EMPTY_CONTEXT: Context = Context {
    cookie: AtomicU32::new(0),
    producer: UnsafeCell::new(Producer { depth: 0, quarantine: false, tls_lost: false, serial: 0, last_ui: 0, quantity_ui: 0, scopes: [EMPTY_SCOPE; 4] }),
    records: Mailbox::new(),
};
static CONTEXTS: [Context; 8] = [EMPTY_CONTEXT; 8];
static CLAIMED: [AtomicU32; 8] = [const { AtomicU32::new(0) }; 8];
static TLS: AtomicU32 = AtomicU32::new(u32::MAX);

const fn counter() -> AtomicU32 {
    AtomicU32::new(0)
}
fn count(value: &AtomicU32) {
    value.fetch_add(1, Relaxed);
}
fn seen(value: &AtomicU32) -> u32 {
    value.load(Relaxed)
}

#[repr(C)]
#[derive(Clone, Copy, Default)]
pub struct CopyFault {
    index: u32,
    expected: u32,
    actual: u32,
    route: u32,
}

// Named so the ARM fixtures can read them; exports stay limited to Forge's callbacks.
macro_rules! visible {
    ($($name:ident: $kind:ty = $value:expr;)*) => {
        $(#[unsafe(no_mangle)] pub static $name: $kind = $value;
        core::arch::global_asm!(concat!(".hidden ", stringify!($name)));)*
    };
}
visible! {
    pdb_mode: Mode = Mode::new();
    pdb_quantity_faults: AtomicU32 = counter();
    pdb_pair_ready: AtomicU32 = counter();
    pdb_capture_ready: AtomicU32 = counter();
    pdb_drops: AtomicU32 = counter();
    pdb_expected_refreshes: AtomicU32 = counter();
    pdb_mapping_faults: AtomicU32 = counter();
    pdb_mapping_detail: Snapshot<CopyFault, 4> = Snapshot::new();
    pdb_gateway_hits: [AtomicU32; 26] = [const { counter() }; 26];
    pdb_forced_checks: [AtomicU32; 2] = [const { counter() }; 2];
    pdb_natural_checks: [AtomicU32; 2] = [const { counter() }; 2];
    pdb_update_hits: AtomicU32 = counter();
    pdb_completed_batches: AtomicU32 = counter();
    pdb_completed_generations: AtomicU32 = counter();
    pdb_published_rewards: AtomicU32 = counter();
    pdb_cleared_rewards: AtomicU32 = counter();
    pdb_last_ui_state: AtomicU32 = counter();
    pdb_last_comparison_tier: AtomicU32 = counter();
    pdb_binding_count: AtomicU32 = counter();
    pdb_latest_tier: AtomicU32 = counter();
    pdb_bonus_count: AtomicU32 = counter();
    pdb_generated_count: AtomicU32 = counter();
    pdb_summary_status: AtomicU32 = counter();
    pdb_main_count_literal: AtomicU32 = counter();
    pdb_main_count_resume: AtomicU32 = counter();
    pdb_observed: Records = Records(UnsafeCell::new([[EMPTY_RECORD; 8]; 8]));
    pdb_displayed: Records = Records(UnsafeCell::new([[EMPTY_RECORD; 8]; 8]));
}
pub struct Records(UnsafeCell<[[Record; 8]; 8]>);
// SAFETY: the Forge update callback is the only reader and writer.
unsafe impl Sync for Records {}

static BASE: AtomicU32 = counter();
static INITIALIZED: AtomicBool = AtomicBool::new(false);
static TINT_READY: AtomicBool = AtomicBool::new(false);
static REPORTED: AtomicBool = AtomicBool::new(false);

fn base() -> u32 {
    BASE.load(Relaxed)
}
fn lost() {
    pdb_drops.fetch_add(1, Relaxed);
}
fn quantity_fault(reason: QuantityFault) {
    if reason != QuantityFault::None {
        pdb_quantity_faults.fetch_or(1 << reason as u32, Relaxed);
    }
}

// Run at the original builder's paired return, before immutable observations are published. Pages
// 0/1/2 use UI+0x5C/+0x64/+0x6C respectively; page 3 (+0x74) is companion gathering/plunder and is
// excluded from every write. The UI-object latch, cleared by the destructor tap, makes this a single
// attempt per result lifetime, including 1x and unsupported-data failures.
fn multiply_player_pages(s: &mut Scope) {
    if s.multiplier == 1 || s.quantity_done {
        return;
    }
    if pdb_capture_ready.load(Acquire) == 0 {
        return quantity_fault(QuantityFault::Generation);
    }
    if !s.quantity_ready || !field(s.ui, 0x5c, 32) {
        return quantity_fault(QuantityFault::Memory);
    }
    let mut all = [QuantityPage::default(); 4];
    for page in 0..4 {
        let offset = 0x5c + page as u32 * 8;
        all[page] = QuantityPage { array: word(s.ui + offset), count: word(s.ui + offset + 4) };
        let q = all[page];
        let capacity = if page < 3 { PLAYER_PAGE_CAPACITIES[page] } else { PALICO_PAGE_CAPACITY };
        if q.count > capacity
            || (q.count != 0 && (q.array == 0 || q.array % 4 != 0 || q.array as u64 + q.count as u64 * 4 > 0x1_0000_0000))
            || (page < 3 && (q.array != s.quantity_pages[page].array || q.count != s.quantity_pages[page].count
                || (q.count != 0 && !writable(q.array, q.count * 4))))
        {
            return quantity_fault(QuantityFault::Memory);
        }
        // Native allocations are disjoint. Reject overlapping included pages or any alias into the
        // excluded Palico page, regardless of contents.
        for other in &all[..page] {
            if q.count != 0 && other.count != 0 && (q.array as u64) < other.array as u64 + other.count as u64 * 4
                && (other.array as u64) < q.array as u64 + q.count as u64 * 4
            {
                return quantity_fault(QuantityFault::Memory);
            }
        }
    }
    // Constructors zero all player arrays. For a nonempty entry preimage, require fresh observed
    // native main/free-hunt counts and matching copies. Lost observation or TLS must never authorize
    // scaling previously built data.
    if !s.player_blank && (s.counted == 0 || s.counted != s.copied) {
        return quantity_fault(QuantityFault::Generation);
    }
    let mut original = [[Reward::default(); FIRST_SCREEN_CAPACITY]; 3];
    for page in 0..3 {
        let q = all[page];
        if q.count != 0 && !copy(q.array, original[page].as_mut_ptr().cast(), q.count * 4) {
            return quantity_fault(QuantityFault::Memory);
        }
        let fault = quantity_preflight(&original[page], q.count, s.multiplier as u32);
        if fault != QuantityFault::None {
            return quantity_fault(fault);
        }
    }
    // Match captured main/free-hunt snapshots to their original live page. Validate every overlapping
    // range before touching any player page. Luck attribution, slot indices and item IDs remain
    // attached to the same slots.
    if s.pending_count > 8 {
        return quantity_fault(QuantityFault::Snapshot);
    }
    let mut on_page = [false; 8];
    for i in 0..s.pending_count {
        let r = s.pending[i].rewards;
        for page in 0..3 {
            let q = all[page];
            let end = r.array as u64 + r.count as u64 * 4;
            if q.count == 0 || r.count == 0 || r.array as u64 >= q.array as u64 + q.count as u64 * 4 || q.array as u64 >= end {
                continue;
            }
            if r.array < q.array || (r.array - q.array) % 4 != 0 || r.count > 8 || end > q.array as u64 + q.count as u64 * 4 {
                return quantity_fault(QuantityFault::Snapshot);
            }
            let start = ((r.array - q.array) / 4) as usize;
            if (0..r.count as usize).any(|j| original[page][start + j] != r.items[j]) {
                return quantity_fault(QuantityFault::Snapshot);
            }
            on_page[i] = true;
        }
    }
    // All checks passed for all three pages. Only occupied amount halfwords change. Collection and
    // appraisal therefore receive exactly the displayed product, subject to native capacity.
    let multiplier = s.multiplier as u16;
    for page in 0..3 {
        for i in 0..all[page].count as usize {
            if original[page][i].item != 0 {
                let amount = (all[page].array + i as u32 * 4 + 2) as *mut u16;
                // SAFETY: `writable` proved the page; the preflight bounded the product to 32767.
                unsafe { amount.write_volatile(original[page][i].amount * multiplier) };
            }
        }
    }
    for i in 0..s.pending_count {
        if on_page[i] {
            for j in 0..s.pending[i].rewards.count as usize {
                s.pending[i].rewards.items[j].amount *= multiplier;
            }
        }
    }
}

fn gui_node(holder: u32, root_index: u32, node_index: u32) -> u32 {
    if root_index >= 128 || node_index >= 128 || !field(holder, 0x298, 4) {
        return 0;
    }
    let split = word(holder + 0x298);
    if split > 128 {
        return 0;
    }
    let (offset, adjusted) = if root_index < split { (0xf8, root_index) } else { (0x294, root_index - split) };
    if !field(holder, offset, 4) {
        return 0;
    }
    let table = word(holder + offset);
    if !field(table, adjusted * 4, 4) {
        return 0;
    }
    let root = word(table + adjusted * 4);
    if !field(root, 0xd8, 4) {
        return 0;
    }
    let table = word(root + 0xd8);
    if !field(table, node_index * 4, 4) {
        return 0;
    }
    word(table + node_index * 4)
}
/// Festa's subclass inherits the texture layout and draw/vertex methods. Both exact vtables are
/// verified against the pinned original executable.
fn texture_node(node: u32) -> bool {
    if !readable(node, 0x130) {
        return false;
    }
    let vft = word(node);
    vft == base().wrapping_add(0x178fcc8) || vft == base().wrapping_add(0x176c7c4)
}



fn context() -> Option<&'static Context> {
    let tls = TLS.load(Relaxed);
    if tls == u32::MAX {
        return None;
    }
    let tls = tls as i32;
    // SAFETY: fixed SDK exports with the verified signatures above and an allocated slot.
    let cookie = unsafe { pdb_current_thread() } as u32;
    if cookie == 0 {
        lost();
        return None;
    }
    let mut p = unsafe { nnosGetTlsValue(tls) };
    for i in 0..8 {
        if CLAIMED[i].load(Acquire) == 2 && CONTEXTS[i].cookie.load(Relaxed) == cookie {
            let c = &CONTEXTS[i];
            // SAFETY: this context's cookie is the current thread, so `producer` is exclusively ours.
            let producer = unsafe { &mut *c.producer.get() };
            if p != c as *const Context as *mut c_void {
                producer.quarantine = true;
                if !producer.tls_lost {
                    producer.tls_lost = true;
                    lost();
                    c.records.publish(&Record { kind: 4, ui: producer.last_ui, coverage: 1, ..EMPTY_RECORD });
                }
            } else {
                producer.tls_lost = false;
            }
            // Do not overwrite an external TLS edit. Immutable native identity retains the original
            // caller and mode while attribution is quarantined.
            return Some(c);
        }
    }
    if !p.is_null() {
        if p as usize != 1 {
            lost();
        }
        return None;
    }
    for i in 0..8 {
        if CLAIMED[i].compare_exchange_weak(0, 1, AcqRel, Relaxed).is_ok() {
            let c = &CONTEXTS[i];
            c.cookie.store(cookie, Relaxed);
            CLAIMED[i].store(2, Release);
            p = c as *const Context as *mut c_void;
            // SAFETY: as above.
            unsafe { nnosSetTlsValue(tls, p) };
            if unsafe { nnosGetTlsValue(tls) } != p {
                // SAFETY: this thread just claimed the context.
                let producer = unsafe { &mut *c.producer.get() };
                producer.quarantine = true;
                producer.tls_lost = true;
                lost();
            }
            return Some(c);
        }
    }
    // SAFETY: as above.
    unsafe { nnosSetTlsValue(tls, 1 as *mut c_void) };
    lost();
    None
}
fn find(c: &Producer, kind: u32) -> Option<usize> {
    (0..c.depth).rev().find(|&i| c.scopes[i].kind == kind)
}
pub fn forcing_available() -> bool {
    pdb_pair_ready.load(Acquire) != 0 && pdb_capture_ready.load(Acquire) != 0
}
fn force(c: Option<&Producer>) -> bool {
    if !forcing_available() {
        return false;
    }
    // A missing context cannot latch a batch. Fail natural rather than allowing a UI change to alter
    // an unidentified batch partway through generation.
    match c {
        None => false,
        Some(c) if c.depth != 0 => c.scopes[0].force,
        Some(_) => pdb_mode.force(),
    }
}
fn producer(c: &'static Context) -> &'static mut Producer {
    // SAFETY: `context()` returned this context for the current thread, so `producer` is ours; the
    // gateway calls do not nest with another borrow of it.
    unsafe { &mut *c.producer.get() }
}
fn trap() -> ! {
    // Never invent a native return address.
    // SAFETY: a permanently undefined instruction; execution cannot continue.
    unsafe { core::arch::asm!("udf #0", options(noreturn, nostack)) }
}

/// Conditional natural returns use separate fixed gateways. The original callee sees untouched
/// argument and working registers and the original stack. Its output registers and flags are
/// preserved; only the LR value created by BL is reconstructed.
#[unsafe(no_mangle)]
pub extern "C" fn pdb_gateway_dispatch(kind: u32, f: *mut RawFrame) -> u32 {
    // SAFETY: gateway.S passes the frame it just pushed on this thread's stack.
    let f = unsafe { &mut *f };
    let base = base();
    if kind < 26 {
        count(&pdb_gateway_hits[kind as usize]);
    }
    if kind == 25 {
        let scope = context().map(producer).filter(|c| !c.quarantine).and_then(|c| find(c, 9).map(|i| &mut c.scopes[i]));
        match scope {
            Some(s) => s.attribution.begin(f.r[0], f.r[4]),
            None => lost(),
        }
        f.r[5] = f.r[0];
        f.comparison_flags(f.r[4], 7);
        return base + 0x3820bc;
    }
    if (21..=24).contains(&kind) {
        return copy_boundary(kind, f, base);
    }
    if kind == 19 || kind == 20 {
        let i = (kind - 19) as usize;
        f.r[5] = if i != 0 { 1 } else { 31 };
        f.r[13] = base + site_offset(i) + 4;
        return base + site_offset(i) + 8;
    }
    if kind < 2 {
        let c = context();
        let p = c.map(producer);
        let forced = force(p.as_deref());
        if forced {
            count(&pdb_forced_checks[kind as usize]);
            if let Some(p) = p.filter(|p| kind == 0 && !p.quarantine) {
                let selected = find(p, 9).or_else(|| find(p, 10));
                if let Some(i) = selected {
                    let first = if p.scopes[i].kind == 10 { 2 } else { u32::MAX };
                    p.scopes[i].attribution.begin(31, first);
                }
            }
            f.r[0] = 1;
            f.r[5] = if kind != 0 { 1 } else { 31 };
            return base + site_offset(kind as usize) + 8;
        }
        count(&pdb_natural_checks[kind as usize]);
        f.r[13] = if kind != 0 { pdb_gateway_20 as *const () as u32 } else { pdb_gateway_19 as *const () as u32 };
        return base + if kind != 0 { 0x26fe08 } else { 0xe0da0 };
    }
    if kind < 9 {
        let threshold = f.r[if kind == 2 { 5 } else { 6 }];
        pdb_last_comparison_tier.store(threshold, Relaxed);
        if let Some(c) = context().map(producer).filter(|c| !c.quarantine) {
            match find(c, if kind == 2 { 9 } else { 10 }) {
                Some(i) => {
                    let a = &mut c.scopes[i].attribution;
                    if !a.known {
                        a.begin(threshold, if kind == 2 { u32::MAX } else { 2 });
                        if kind == 2 {
                            a.valid = false; // Missing initial-count tap.
                        }
                    } else if a.threshold != threshold {
                        a.valid = false;
                    }
                    if kind == 2 && a.first_slots == u32::MAX {
                        a.valid = false;
                    }
                    a.compare(if kind == 2 { f.r[4] } else { kind - 1 }, f.r[0] & 31);
                }
                None => lost(),
            }
        }
        // Replay both displaced words. Carry/overflow are those of CMP, with Q and GE inherited
        // untouched. AND/MOV have no S bit.
        if kind == 2 {
            f.r[0] &= 31;
        } else {
            f.r[7] = kind - 1;
        }
        f.comparison_flags(threshold, f.r[0]);
        return base + SITES[kind as usize].site + 8;
    }
    enter_scope(kind, f)
}

/// Actual native copy boundary, after generation and before freeing its temporary. Never depends on
/// execution of the generator-entry detour.
fn copy_boundary(kind: u32, f: &mut RawFrame, base: u32) -> u32 {
    let index = if kind < 23 { 0 } else { (kind - 22) as usize };
    let object = f.r[4];
    let source = f.r[if kind < 23 { 7 } else if kind == 23 { 6 } else { 5 }];
    let offset = if kind == 24 { 0x64 } else { 0x5c };
    if let Some(c) = context().map(producer).filter(|c| !c.quarantine) {
        if let Some(u) = find(c, 12) {
            let ui = &mut c.scopes[u];
            if ui.subject == object && ui.counts[index].ready {
                let selected = ui.counts[index];
                ui.counts[index].ready = false;
                let mut r = Record {
                    kind: 2, ui: object, epoch: ui.epoch, tier: selected.attribution.threshold,
                    generated: selected.slots, coverage: 1 << index, ..EMPTY_RECORD
                };
                r.rewards.epoch = r.epoch;
                r.rewards.count = 8;
                let mut valid = selected.slots <= 8 && field(object, offset, 4) && copy_to(source, &mut r.rewards.items);
                if valid {
                    let destination = word(object + offset);
                    let start = if kind < 23 { 0 } else { 32 };
                    valid = destination != 0 && destination as u64 + start as u64 + 32 <= 0x1_0000_0000;
                    r.rewards.array = destination.wrapping_add(start);
                    let empty = r.rewards.items.iter().all(|i| i.item == 0 && i.amount == 0);
                    if empty {
                        r.generated = 0; // Count ran but absent table produced no items.
                    } else {
                        for (j, item) in r.rewards.items.iter().enumerate() {
                            valid = valid && if (j as u32) < selected.slots { item.item != 0 && item.amount != 0 } else { item.item == 0 && item.amount == 0 };
                        }
                    }
                    let complete = empty || selected.attribution.complete(selected.slots);
                    if !complete {
                        r.coverage |= 0x8000_0000;
                        lost();
                    }
                    r.rewards.mask = if complete { selected.attribution.mask(r.generated) } else { 0 };
                }
                if valid && ui.pending_count < 8 {
                    ui.pending[ui.pending_count] = r;
                    ui.pending_count += 1;
                    ui.copied |= 1 << index;
                } else {
                    ui.incomplete = true;
                    lost();
                }
            } else {
                ui.incomplete = true;
                lost();
            }
        }
    }
    // Replay LDR r0,[r4,#field] / LDRH r1,[source]. Neither writes flags.
    f.r[0] = word(object + offset);
    f.r[1] = half(source) as u32;
    base + SITES[kind as usize - 4].site + 8
}

/// Where a paired gateway continues: Forge's trampoline, or for the main-count entry the fixed stub
/// in gateway.S, whose cells install fills before any hook is published.
fn paired_original(kind: u32) -> u32 {
    if SITES[kind as usize].site == MAIN_COUNT_SITE {
        pdb_main_count_original as *const () as u32
    } else {
        ORIGINALS[kind as usize].load(Acquire)
    }
}

fn enter_scope(kind: u32, f: &mut RawFrame) -> u32 {
    let original = paired_original(kind);
    let Some(context) = context() else {
        return original;
    };
    if pdb_capture_ready.load(Acquire) == 0 {
        return original;
    }
    let c = producer(context);
    if c.depth == 4 {
        c.quarantine = true;
        lost();
        return original;
    }
    let requested = pdb_mode.preferences();
    let latched = if c.depth != 0 { force(Some(c)) } else { requested.force && forcing_available() };
    let multiplier = if c.depth != 0 { c.scopes[0].multiplier } else { requested.multiplier };
    let at = c.depth;
    c.depth += 1;
    c.scopes[at] = Scope {
        kind, caller: f.r[13], sp: caller_sp(f), force: latched, multiplier, subject: f.r[0], ..EMPTY_SCOPE
    };
    match kind {
        12 => enter_builder(context, at),
        9 => c.scopes[at].subject = f.r[1], // Native main A/B category, not an item pointer.
        10 | 13 => {
            let subject = f.r[if kind == 10 { 1 } else { 2 }];
            c.scopes[at].subject = subject;
            if readable(subject, 4) {
                c.scopes[at].array = word(subject);
            }
        }
        11 => {
            let subject = c.scopes[at].subject;
            if readable(subject, 4) {
                c.scopes[at].array = word(subject);
            }
            c.scopes[at].count = f.r[3];
            let parent = find(c, 10).or_else(|| find(c, 13)).or_else(|| find(c, 12));
            if let Some(parent) = parent {
                c.scopes[at].attribution = c.scopes[parent].attribution;
            }
        }
        14 => {
            if readable(f.r[1], 8) {
                c.scopes[at].array = word(f.r[1]);
                c.scopes[at].count = word(f.r[1] + 4);
            }
            if let Some(ui) = find(c, 15) {
                c.scopes[at].ui = c.scopes[ui].subject;
            }
        }
        16 => {
            if c.quantity_ui == c.scopes[at].subject {
                c.quantity_ui = 0;
            }
        }
        15 => enter_update(c, at),
        _ => {}
    }
    f.r[13] = pdb_gateway_after as *const () as u32;
    original
}
fn caller_sp(f: &RawFrame) -> u32 {
    f as *const RawFrame as u32 + core::mem::size_of::<RawFrame>() as u32
}
fn enter_builder(context: &'static Context, at: usize) {
    let c = producer(context);
    let serial = c.serial.wrapping_add(1);
    let subject = c.scopes[at].subject;
    let done = c.quantity_ui == subject;
    let s = &mut c.scopes[at];
    s.quantity_done = done;
    if s.multiplier != 1 && !done && field(subject, 0x5c, 24) {
        s.quantity_ready = true;
        s.player_blank = true;
        for page in 0..3 {
            let offset = 0x5c + page as u32 * 8;
            let q = QuantityPage { array: word(subject + offset), count: word(subject + offset + 4) };
            s.quantity_pages[page] = q;
            let mut before = [Reward::default(); FIRST_SCREEN_CAPACITY];
            if q.count > PLAYER_PAGE_CAPACITIES[page]
                || (q.count != 0 && (q.array % 4 != 0 || !writable(q.array, q.count * 4) || !copy(q.array, before.as_mut_ptr().cast(), q.count * 4)))
            {
                s.quantity_ready = false;
                break;
            }
            s.player_blank = s.player_blank && before[..q.count as usize].iter().all(|r| r.item == 0 && r.amount == 0);
        }
    }
    s.epoch = serial;
    s.ui = subject;
    c.serial = serial;
    // State 1 resizes first, then calls this builder inside the same paired update (native BL at
    // 0x384fc0). Its empty pre-generation snapshot is superseded by this newly verified batch, not a
    // copy of old rewards. Different UI objects retain their independent relocation checks.
    if let Some(refresh) = find(c, 15) {
        if c.scopes[refresh].subject == subject {
            c.scopes[refresh].array = 0;
            c.scopes[refresh].pending_count = 0;
            c.scopes[refresh].incomplete = false;
        }
    }
    c.last_ui = subject;
    context.records.publish(&Record { kind: 1, ui: subject, epoch: serial, ..EMPTY_RECORD });
}
/// State 1 may reallocate the main array before opening the grid. Snapshot before native frees it,
/// through the existing paired update hook; no additional arena, TLS slot or game writes are needed.
fn enter_update(c: &mut Producer, at: usize) {
    let serial = c.serial;
    let s = &mut c.scopes[at];
    if !field(s.subject, 0x3c, 4) || word(s.subject + 0x3c) != 1 {
        return;
    }
    s.epoch = serial;
    if !field(s.subject, 0x5c, 8) {
        s.incomplete = true;
        return;
    }
    s.array = word(s.subject + 0x5c);
    s.count = word(s.subject + 0x60);
    if s.count > 48 || s.array == 0 {
        s.incomplete = true;
        return;
    }
    let mut start = 0;
    while start < s.count {
        let count = (s.count - start).min(8);
        let mut r = Record { kind: 7, ui: s.subject, epoch: s.array + start * 4, tier: s.epoch, ..EMPTY_RECORD };
        r.rewards.count = count;
        if s.array as u64 + start as u64 * 4 + count as u64 * 4 > 0x1_0000_0000
            || !copy(r.epoch, r.rewards.items.as_mut_ptr().cast(), count * 4)
        {
            s.incomplete = true;
            break;
        }
        s.pending[s.pending_count] = r;
        s.pending_count += 1;
        start += 8;
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn pdb_gateway_leave(f: *mut RawFrame) -> u32 {
    // SAFETY: gateway.S passes the frame it just pushed on this thread's stack.
    let f = unsafe { &mut *f };
    let Some(context) = context() else { trap() };
    let c = producer(context);
    if c.depth == 0 {
        trap();
    }
    c.depth -= 1;
    let mut s = c.scopes[c.depth];
    if s.sp != caller_sp(f) {
        trap();
    }
    if f.r[13] == pdb_gateway_after as *const () as u32 {
        f.r[13] = s.caller;
    }
    if c.quarantine {
        if c.depth == 0 {
            c.quarantine = false;
        }
        return s.caller;
    }
    let base = base();
    match s.kind {
        11 => count(&pdb_completed_generations),
        9 => {
            if let Some(parent) = find(c, 13).or_else(|| find(c, 12)) {
                c.scopes[parent].attribution = s.attribution;
            }
            if let Some(u) = find(c, 12) {
                let ui = &mut c.scopes[u];
                let index = if s.caller == base + 0x381dc4 && s.subject == 0 {
                    Some(0)
                } else if s.caller == base + 0x387a98 && s.subject == 1 {
                    Some(1)
                } else {
                    None
                };
                match index {
                    Some(i) if f.r[0] <= 8 && !ui.counts[i].ready => {
                        ui.counts[i] = CountSnapshot { attribution: s.attribution, slots: f.r[0], ready: true };
                        ui.counted |= 1 << i;
                    }
                    _ => {
                        ui.incomplete = true;
                        lost();
                    }
                }
            }
        }
        10 => {
            if let Some(u) = find(c, 12) {
                let ui = &mut c.scopes[u];
                // This native routine returns void: r0 is not its slot count. Use its observed
                // comparisons, then validate the generated prefix.
                let a = s.attribution;
                let slots = if a.comparisons != 0 { a.last_slots + (a.last_roll < a.threshold) as u32 } else { 0 };
                if s.caller == base + 0x388084 && slots <= 8 && !ui.counts[2].ready {
                    ui.counts[2] = CountSnapshot { attribution: a, slots, ready: true };
                    ui.counted |= 4;
                } else {
                    ui.incomplete = true;
                    lost();
                }
            }
        }
        12 => {
            multiply_player_pages(&mut s);
            c.quantity_ui = s.ui;
            let order = pdb_completed_batches.fetch_add(1, Relaxed).wrapping_add(1);
            for r in &s.pending[..s.pending_count] {
                let mut check = [Reward::default(); 8];
                if copy(r.rewards.array, check.as_mut_ptr().cast(), r.rewards.count * 4)
                    && check[..r.rewards.count as usize] == r.rewards.items[..r.rewards.count as usize]
                {
                    context.records.publish(r);
                    count(&pdb_published_rewards);
                } else {
                    lost();
                }
            }
            context.records.publish(&Record {
                kind: 6, ui: s.ui, epoch: s.epoch,
                coverage: if s.counted != 0 && s.counted == s.copied && !s.incomplete { 1 } else { 2 },
                generated: s.pending_count as u32, tier: order, ..EMPTY_RECORD
            });
        }
        14 if s.ui != 0 && s.array != 0 && field(s.subject, 0x5c, 4) => leave_list_copy(context, &s, c.serial),
        15 => leave_update(context, &s),
        16 => context.records.publish(&Record { kind: 3, ui: s.subject, ..EMPTY_RECORD }),
        _ => {}
    }
    s.caller
}

/// Native 0x623c08 copies source[i] to list.buffer[i], up to capacity. The consumer follows that
/// index mapping only after checking contents. Immutable eight-entry chunks fit the mailbox payload;
/// capture now, before a later list refresh or the update callback reads them.
fn leave_list_copy(context: &Context, s: &Scope, serial: u32) {
    let clear_copy = || {
        let mut r = Record { kind: 5, ui: s.ui, tier: s.subject, coverage: 1, ..EMPTY_RECORD };
        r.rewards.epoch = serial;
        context.records.publish(&r);
    };
    let total = s.count.min(word(s.subject + 0x5c));
    if total > 48 || s.subject as u64 + 0x60 + total as u64 * 4 > 0x1_0000_0000 || s.array as u64 + total as u64 * 4 > 0x1_0000_0000 {
        clear_copy();
        lost();
        return;
    }
    let mut start = 0;
    while start < total || start == 0 {
        let mut r = Record { kind: 5, ui: s.ui, epoch: s.array + start * 4, tier: s.subject, coverage: (start == 0) as u32, ..EMPTY_RECORD };
        r.rewards.epoch = serial;
        r.rewards.array = s.subject + 0x60 + start * 4;
        r.rewards.count = (total - start).min(8);
        if !copy(r.rewards.array, r.rewards.items.as_mut_ptr().cast(), r.rewards.count * 4) {
            clear_copy();
            lost();
            break;
        }
        context.records.publish(&r);
        if total == 0 {
            break;
        }
        start += 8;
    }
}
fn packed(r: Reward) -> u32 {
    r.item as u32 | (r.amount as u32) << 16
}
fn leave_update(context: &Context, s: &Scope) {
    let mapping_failed = |context: &Context| {
        lost();
        count(&pdb_mapping_faults);
        context.records.publish(&Record { kind: 4, ui: s.subject, coverage: 2, ..EMPTY_RECORD });
    };
    if s.array != 0 && s.pending_count != 0 {
        let mut valid = !s.incomplete && field(s.subject, 0x5c, 8);
        let destination = if valid { word(s.subject + 0x5c) } else { 0 };
        valid = valid && destination != 0 && word(s.subject + 0x60) >= s.count && word(s.subject + 0x60) <= 48;
        if !valid {
            pdb_mapping_detail.publish(&CopyFault { route: 3, ..Default::default() });
        }
        for r in &s.pending[..s.pending_count] {
            if !valid {
                break;
            }
            let mut contents = [Reward::default(); 8];
            let offset = r.epoch - s.array;
            valid = destination as u64 + offset as u64 + r.rewards.count as u64 * 4 <= 0x1_0000_0000
                && copy(destination + offset, contents.as_mut_ptr().cast(), r.rewards.count * 4);
            if !valid {
                pdb_mapping_detail.publish(&CopyFault { index: offset / 4, route: 3, ..Default::default() });
            }
            for j in 0..r.rewards.count {
                if !valid {
                    break;
                }
                let (want, have) = (r.rewards.items[j as usize], contents[j as usize]);
                valid = want == have;
                if !valid {
                    pdb_mapping_detail.publish(&CopyFault { index: offset / 4 + j, expected: packed(want), actual: packed(have), route: 1 });
                }
            }
        }
        if valid {
            for r in &s.pending[..s.pending_count] {
                let mut moved = *r;
                moved.rewards.array = destination + (r.epoch - s.array);
                context.records.publish(&moved);
            }
        } else {
            mapping_failed(context);
        }
    } else if s.incomplete {
        pdb_mapping_detail.publish(&CopyFault { route: 3, ..Default::default() });
        mapping_failed(context);
    }
    if field(s.subject, 0x3c, 4) {
        pdb_last_ui_state.store(word(s.subject + 0x3c), Relaxed);
    }
    if !field(s.subject, 0x3c, 4) || word(s.subject + 0x3c) < 2 || word(s.subject + 0x3c) > 5 {
        count(&pdb_cleared_rewards);
        context.records.publish(&Record { kind: 4, ui: s.subject, ..EMPTY_RECORD });
    }
}

// ---- Forge callbacks ----
pub fn requested_preferences() -> Preferences {
    pdb_mode.preferences()
}
pub fn request_preferences(p: Preferences) {
    pdb_mode.set(p);
}
core::arch::global_asm!(".hidden pdb_gateway_dispatch\n.hidden pdb_gateway_leave");

struct Global<T>(UnsafeCell<T>);
// SAFETY: each Global names its single writer; forge_onInit finishes before any reader runs.
unsafe impl<T> Sync for Global<T> {}
const WHITE: u32 = 0xffff_ffff;
const MAIN_COUNT_SITE: u32 = 0x381fec;
/// main+0x381FF0 `ldr r0,[pc,#0x108]` reads this literal.
const MAIN_COUNT_LITERAL: u32 = 0x381ff8 + 0x108;

// Forge's trampoline for each chaining entry, by SITES index; zero elsewhere.
static ORIGINALS: [AtomicU32; 22] = [const { AtomicU32::new(0) }; 22];
// Disabled Forge snapshots of each site's first eight bytes: the rollback record. They live for the
// process, since Forge keeps their buffers and a hook may remain reachable.
static SNAPSHOTS: Global<[Option<Patch>; 22]> = Global(UnsafeCell::new([const { None }; 22]));
static HOOKED: AtomicBool = AtomicBool::new(false);

/// Every site is checked before Forge hooks any of them; a later failure restores what was hooked.
fn install_hooks(text: u32) -> Result<(), &'static str> {
    let k = SvcKernel;
    if !platform::is_mhgu(&k) {
        return Err("not MHGU");
    }
    let hooks: [Hook; 22] = core::array::from_fn(hook);
    if text == 0 || text & 3 != 0 || !valid_recipe(&hooks) {
        return Err("invalid hook recipe");
    }
    let mut found = [[0u32; 2]; 22];
    for (i, h) in hooks.iter().enumerate() {
        let Some(w) = platform::window(&k, text + h.window) else {
            return Err("unreadable game code");
        };
        if !window_matches(h, &w, false) || !readable(h.detour, 4) {
            return Err("MHGU 1.4.0 code mismatch or a conflicting patch");
        }
        found[i] = [w[h.at()], w[h.at() + 1]];
    }
    let literal = text + MAIN_COUNT_LITERAL;
    if !platform::executable(&k, literal, 4) {
        return Err("unreadable game code");
    }
    pdb_main_count_literal.store(word(literal), Release);
    pdb_main_count_resume.store(text + MAIN_COUNT_SITE + 8, Release);
    // SAFETY: forge_onInit is the only writer, before any gateway can run.
    let snapshots = unsafe { &mut *SNAPSHOTS.0.get() };
    for (i, h) in hooks.iter().enumerate() {
        let mut branch = [0u8; 8];
        branch[..4].copy_from_slice(&LDR_PC.to_le_bytes());
        branch[4..].copy_from_slice(&h.detour.to_le_bytes());
        snapshots[i] = Some(Patch::new(text + h.site, &branch, false));
    }
    for (i, h) in hooks.iter().enumerate() {
        let target = text + h.site;
        let mut original = core::ptr::null();
        let out = if h.chains { &mut original as *mut *const c_void } else { core::ptr::null_mut() };
        // SAFETY: the window was checked above; an interior site's gateway replays its displaced
        // words and needs no callable original. Forge runs this before original_sApp_run.
        let created = unsafe { forge::sys::hook::forge_hook_create(target as *const c_void, h.detour as *const c_void, out) };
        let continuation = original as u32;
        let trampoline = !h.chains
            || (continuation & 3 == 0 && platform::executable(&k, continuation, 16) && {
                let words: [u32; 4] = core::array::from_fn(|j| word(continuation + j as u32 * 4));
                trampoline_matches(target, found[i], &words)
            });
        if trampoline && h.chains {
            // Kept even if a later step fails: a reachable gateway needs a valid continuation.
            ORIGINALS[i].store(continuation, Release);
        }
        let branch = platform::window(&k, text + h.window).is_some_and(|w| window_matches(h, &w, true) && w[h.at() + 1] == h.detour);
        if !trampoline || created.target as u32 != target || created.detour as u32 != h.detour
            || created.original as u32 != continuation || !branch || !platform::sync(&k, target, 8)
        {
            return Err(if rollback() { "Forge hook installation failed" } else { "hook rollback failed; restart required" });
        }
    }
    HOOKED.store(true, Release);
    Ok(())
}
/// Restore every site still holding our branch, newest first. A word that is neither ours nor the
/// original belongs to someone else and is left alone, which fails the rollback.
fn rollback() -> bool {
    let k = SvcKernel;
    // SAFETY: forge_onInit is the only writer, before any gateway can run.
    let snapshots = unsafe { &mut *SNAPSHOTS.0.get() };
    let mut restored = true;
    for patch in snapshots.iter_mut().rev().flatten() {
        let at = patch.addr();
        let original: [u8; 8] = patch.original_bytes().try_into().unwrap_or([0; 8]);
        let replacement: [u8; 8] = patch.patch_bytes().try_into().unwrap_or([0; 8]);
        let mut current = [0u8; 8];
        if !platform::executable(&k, at, 8) || !copy(at, current.as_mut_ptr(), 8) {
            restored = false;
            continue;
        }
        if current != original {
            if !(0..8).step_by(4).all(|j| current[j..j + 4] == original[j..j + 4] || current[j..j + 4] == replacement[j..j + 4]) {
                restored = false;
                continue;
            }
            // Patch has no conditional restore: enabling records ownership and disabling writes the
            // snapshot back.
            patch.enable();
            patch.disable();
        }
        restored &= platform::sync(&k, at, 8) && copy(at, current.as_mut_ptr(), 8) && current == original;
    }
    restored
}
fn install() {
    if INITIALIZED.swap(true, Relaxed) {
        // Recheck every site without hooking again. A conflict cancels forcing and attribution.
        let text = base();
        let k = SvcKernel;
        let intact = (0..22).all(|i| {
            let h = hook(i);
            platform::window(&k, text + h.window).is_some_and(|w| window_matches(&h, &w, true))
        });
        if HOOKED.load(Acquire) && !intact {
            pdb_pair_ready.store(0, Release);
            pdb_capture_ready.store(0, Release);
        }
        return;
    }
    let text = forge::mem::text_addr();
    BASE.store(text, Relaxed);
    let mut slot = -1;
    // SAFETY: a fixed SDK export with a live output and no destructor.
    if unsafe { nnosAllocateTlsSlot(&mut slot, core::ptr::null()) } != 0 || slot < 0 {
        lost();
        log::warn!("[please-do-better] Reward capture TLS unavailable; reduce loaded plugins and restart");
        return;
    }
    TLS.store(slot as u32, Relaxed);
    if let Err(reason) = install_hooks(text) {
        log::warn!("[please-do-better] Hooks unavailable: {reason}; remove conflicting mods, verify game/Forge, then restart");
        return;
    }
    pdb_pair_ready.store(1, Release);
    pdb_capture_ready.store(1, Release);
    let (at, words) = VERTEX_COLOR;
    let setter = text + at;
    if readable(setter, 32) && (0..8).all(|i| word(setter + i * 4) == words[i as usize]) {
        TINT_READY.store(true, Relaxed);
    } else {
        log::warn!("[please-do-better] Highlights unavailable: the frame colour setter differs; verify game/Forge");
    }
}
pub fn start() {
    if !REPORTED.load(Relaxed) {
        forge::log::init().expect("Failed to initialize the Forge logger");
    }
    install();
    if !REPORTED.swap(true, Relaxed) {
        let status = if !forcing_available() {
            "forcing unavailable"
        } else if TINT_READY.load(Relaxed) {
            "forcing and highlights ready"
        } else {
            "forcing ready; highlights unavailable"
        };
        log::info!(concat!("[please-do-better] ", env!("PDB_VERSION"), " loaded; {}"), status);
    }
}

static EPOCHS: Global<[u32; 8]> = Global(UnsafeCell::new([0; 8]));
static OWNERS: Global<[u32; 8]> = Global(UnsafeCell::new([0; 8]));
static SUMMARY_ORDER: AtomicU32 = counter();
static QUANTITY_REPORTED: Once = Once::new();
static FAILURES: Once = Once::new();

pub fn update() {
    count(&pdb_update_hits);
    const FAULTS: [&str; 7] = [
        "", "unwritable or unsupported reward array", "invalid item/amount record", "quantity exceeds the native signed limit",
        "no fresh first-screen generation", "reward snapshot changed", "invalid multiplier",
    ];
    let faults = seen(&pdb_quantity_faults);
    for reason in 1..7u32 {
        if faults & (1 << reason) != 0 && QUANTITY_REPORTED.claim(reason) {
            log::warn!("[please-do-better] Multiplier skipped: {}; quantities retained. Restart if persistent.", FAULTS[reason as usize]);
        }
    }
    if seen(&pdb_mapping_faults) != 0 && FAILURES.claim(0) {
        log::warn!("[please-do-better] Reward mapping incomplete; uncertain highlights skipped; restart if persistent");
    }
    // SAFETY: only this callback touches these consumer tables.
    let (observed, displayed, epochs, owners) = unsafe {
        (&mut *pdb_observed.0.get(), &mut *pdb_displayed.0.get(), &mut *EPOCHS.0.get(), &mut *OWNERS.0.get())
    };
    for thread in 0..8 {
        let records = &CONTEXTS[thread].records;
        let lost_before = records.overwritten.load(Relaxed);
        for _ in 0..16 {
            let Some(r) = records.read() else { break };
            if records.overwritten.load(Relaxed) != lost_before {
                break;
            }
            consume(&r, thread, observed, displayed, epochs, owners);
        }
        if records.overwritten.load(Relaxed) != lost_before {
            owners[thread] = 0;
            observed[thread] = [EMPTY_RECORD; 8];
            displayed[thread] = [EMPTY_RECORD; 8];
            lost();
            pdb_summary_status.store(2, Release);
        }
    }
    let whitened = whiten_slots(displayed);
    pdb_binding_count.store(whitened, Release);
}

fn consume(r: &Record, thread: usize, observed: &mut [[Record; 8]; 8], displayed: &mut [[Record; 8]; 8], epochs: &mut [u32; 8], owners: &mut [u32; 8]) {
    let owned = r.ui == owners[thread];
    match r.kind {
        1 | 3 | 4 if r.kind == 1 || owned => {
            if r.kind == 4 && r.coverage == 1 {
                pdb_summary_status.store(2, Release);
            }
            observed[thread] = [EMPTY_RECORD; 8];
            displayed[thread] = [EMPTY_RECORD; 8];
            owners[thread] = if r.kind == 1 { r.ui } else { 0 };
            epochs[thread] = r.epoch;
        }
        2 if owned && r.epoch == epochs[thread] => match observed[thread].iter_mut().find(|e| e.kind == 0) {
            Some(slot) => *slot = *r,
            None => lost(),
        },
        2 => lost(), // Nested or stale batches are never silently adopted.
        6 if owned && r.epoch == epochs[thread] && {
            let delta = r.tier.wrapping_sub(SUMMARY_ORDER.load(Relaxed));
            delta > 0 && delta < 0x8000_0000
        } => {
            let (mut records, mut tier, mut bonuses, mut generated) = (0u32, 0u32, 0u32, 0u32);
            let mut complete = r.coverage == 1;
            for record in observed[thread].iter().filter(|e| e.kind != 0) {
                records += 1;
                if record.tier != 0 {
                    tier = if tier == 0 || tier == record.tier { record.tier } else { u32::MAX };
                }
                generated += record.generated;
                complete = complete && record.coverage & 0x8000_0000 == 0;
                bonuses += record.rewards.mask.count_ones();
            }
            SUMMARY_ORDER.store(r.tier, Relaxed);
            pdb_latest_tier.store(tier, Release);
            pdb_bonus_count.store(bonuses, Release);
            pdb_generated_count.store(generated, Release);
            pdb_summary_status.store(if records != 0 && records == r.generated && complete { 1 } else { 2 }, Release);
        }
        7 if owned && r.tier == epochs[thread] => {
            for source in observed[thread].iter_mut() {
                if source.kind == 0 || source.rewards.array < r.epoch {
                    continue;
                }
                let offset = source.rewards.array - r.epoch;
                if offset & 3 != 0 || offset as u64 + source.rewards.count as u64 * 4 > r.rewards.count as u64 * 4 {
                    continue;
                }
                let first = (offset / 4) as usize;
                let n = source.rewards.count as usize;
                let mismatch = (0..n).find(|&j| source.rewards.items[j] != r.rewards.items[first + j]);
                match mismatch {
                    None => source.rewards.array = r.rewards.array + offset,
                    Some(j) => {
                        pdb_mapping_detail.publish(&CopyFault {
                            index: (first + j) as u32, expected: packed(source.rewards.items[j]),
                            actual: packed(r.rewards.items[first + j]), route: 2,
                        });
                        *source = EMPTY_RECORD;
                        lost();
                        count(&pdb_mapping_faults);
                    }
                }
            }
        }
        5 if owned && r.rewards.epoch == epochs[thread] => {
            if r.coverage != 0 {
                for record in displayed[thread].iter_mut() {
                    if record.generated == r.tier {
                        *record = EMPTY_RECORD;
                    }
                }
            }
            for i in 0..8 {
                let source = observed[thread][i];
                if source.kind == 0 || source.rewards.array < r.epoch {
                    continue;
                }
                let offset = source.rewards.array - r.epoch;
                if offset & 3 != 0 || offset as u64 + source.rewards.count as u64 * 4 > r.rewards.count as u64 * 4
                    || r.rewards.array as u64 + offset as u64 + source.rewards.count as u64 * 4 > 0x1_0000_0000
                {
                    continue;
                }
                let mut target = source;
                target.generated = r.tier;
                target.rewards.array = r.rewards.array + offset;
                let first = (offset / 4) as usize;
                let (mut same, mut changed) = (true, false);
                for j in 0..target.rewards.count as usize {
                    let current = r.rewards.items[first + j];
                    if !compatible_refresh(target.rewards.items[j], current) {
                        same = false;
                        pdb_mapping_detail.publish(&CopyFault {
                            index: (first + j) as u32, expected: packed(target.rewards.items[j]), actual: packed(current), route: 0,
                        });
                    }
                    changed = changed || current != target.rewards.items[j];
                    if current.item == 0 {
                        target.rewards.mask &= !(1 << j);
                    }
                }
                if same {
                    match displayed[thread].iter_mut().find(|e| e.kind == 0) {
                        Some(slot) => *slot = target,
                        None => lost(),
                    }
                    if changed {
                        count(&pdb_expected_refreshes);
                    }
                } else {
                    lost();
                    count(&pdb_mapping_faults);
                }
            }
        }
        _ => {}
    }
}

/// Highlights each displayed extra-luck slot by setting its native background frame's four vertex
/// colours to white, which shows the frame texture without its red or blue tint. The setter returns
/// at once when a colour already matches, so calling it every update is cheap and restores the tint
/// if anything rewrites it. Frames are never set back: a new reward screen builds its own colours.
/// Each node is resolved and validated in this callback, from the live list, before the call.
fn whiten_slots(displayed: &[[Record; 8]; 8]) -> u32 {
    if !TINT_READY.load(Relaxed) {
        return 0;
    }
    // SAFETY: VERTEX_COLOR's bytes were checked at install; the setter takes the object, a pointer
    // to one colour word and a vertex index 0..3, and returns nothing.
    let set: unsafe extern "C" fn(u32, *const u32, u32) = unsafe { core::mem::transmute((base() + VERTEX_COLOR.0) as usize) };
    let mut whitened = 0;
    for record in displayed.iter().flatten().filter(|r| r.kind != 0 && r.generated != 0) {
        let list = record.generated;
        if record.rewards.array < list + 0x60 || !field(list, 0x4c, 4) || !field(list, 0x24, 4) {
            continue;
        }
        let first = (record.rewards.array - list - 0x60) / 4;
        let group = word(list + 0x4c);
        if group > 7 || first >= 48 || !field(list, 0x160 + group * 0x28, 20) {
            continue;
        }
        let holder = word(list + 0x24);
        let icon_root = word(list + 0x160 + group * 0x28);
        let background_root = word(list + 0x164 + group * 0x28);
        let ids = word(list + 0x16c + group * 0x28);
        for j in 0..record.rewards.count {
            if (record.rewards.mask >> j) & 1 == 0 {
                continue;
            }
            let index = first + j;
            if index >= 48 || !field(ids, index * 4, 4) {
                continue;
            }
            let icon_index = word(ids + index * 4);
            let Some((frame_index, id)) = frame_layout(group, icon_root, background_root, index, icon_index) else {
                continue;
            };
            let icon = gui_node(holder, icon_root, icon_index);
            let node = gui_node(holder, background_root, frame_index);
            if !texture_node(icon) || !texture_node(node) || word(node + 0x50) != id {
                continue;
            }
            for vertex in 0..4 {
                // SAFETY: `node` is a live cGUIObjTexture checked above in this callback.
                unsafe { set(node, &WHITE, vertex) };
            }
            whitened += 1;
        }
    }
    whitened
}
