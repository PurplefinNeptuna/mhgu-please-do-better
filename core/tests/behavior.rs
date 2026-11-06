use please_do_better_core::attribution::*;
use please_do_better_core::frame::comparison_nzcv;
use please_do_better_core::highlight::*;
use please_do_better_core::hooks::*;
use please_do_better_core::mailbox::Mailbox;
use please_do_better_core::mode::*;
use please_do_better_core::platform::*;
use please_do_better_core::preferences::*;
use please_do_better_core::quantity::*;
use please_do_better_core::signatures::*;
use std::collections::BTreeMap;
use std::ffi::CStr;

fn begun(tier: u32) -> Attribution {
    let mut a = Attribution::new();
    a.begin(tier, u32::MAX);
    a
}
const TIERS: [u32; 6] = [8, 16, 22, 25, 28, 31];

#[test]
fn single_comparison_masks() {
    for tier in TIERS {
        for slots in 0..8 {
            for roll in 0..32 {
                let mut a = begun(tier);
                a.compare(slots, roll);
                let actual = if tier > roll { slots + 1 } else { slots };
                let expected = if slots != 0 && tier > 22 && roll >= 22 && roll < tier { 1 << slots } else { 0 };
                assert_eq!(a.mask(actual), expected);
            }
        }
    }
}

#[test]
fn extra_luck_slots_and_their_bounds() {
    for tier in [25, 28, 31] {
        let mut a = begun(tier);
        for (slots, roll) in [(2, 0), (3, 22), (4, 0), (5, 0), (6, 0), (7, tier - 1)] {
            a.compare(slots, roll);
        }
        assert_eq!(a.mask(8), 0xf8);
        a.compare(8, 0);
        assert_eq!(a.mask(8), 0);
    }
    let mut absent = Attribution::new();
    assert_eq!(absent.mask(8), 0);
    absent.begin(24, u32::MAX);
    absent.compare(2, 22);
    assert_eq!(absent.mask(8), 0);
    // Native return clamps a zero-slot stop to one.
    let mut minimum = begun(31);
    minimum.compare(0, 22);
    minimum.compare(1, 0);
    minimum.compare(2, 0);
    assert_eq!(minimum.mask(3), 6);
}

#[test]
fn completeness_needs_a_gapless_chain() {
    for tier in TIERS {
        for first in 0..=9 {
            let mut a = Attribution::new();
            a.begin(tier, first);
            if first < 8 {
                for slot in first..8 {
                    a.compare(slot, 0);
                }
            }
            assert!(a.complete(8));
            a.begin(tier, first);
            if first < 8 {
                a.compare(first, tier);
                assert!(a.complete(if first != 0 { first } else { 1 }));
            } else {
                assert!(!a.complete(7));
            }
        }
    }
    let mut gap = Attribution::new();
    gap.begin(31, 2);
    gap.compare(3, 22);
    gap.compare(4, 31);
    assert!(!gap.complete(4));
    gap.begin(31, 2);
    gap.compare(2, 22);
    gap.compare(4, 31);
    assert!(!gap.complete(4));
    gap.begin(31, 2);
    gap.compare(2, 31);
    gap.compare(3, 0);
    assert!(!gap.complete(4));
    gap.begin(31, 2);
    gap.compare(2, 22);
    assert!(!gap.complete(3));
    gap.begin(31, u32::MAX);
    assert!(!gap.complete(8));
}

#[test]
fn provenance_and_refresh() {
    let mut p = Provenance { epoch: 10, array: 0x1000, count: 8, mask: 0x80, ..Provenance::EMPTY };
    p.items[7] = Reward { item: 123, amount: 2 };
    let r = |item, amount| Reward { item, amount };
    assert!(p.matches(10, 0x1000, 7, r(123, 2)) && p.matches(10, 0x1000, 7, r(123, 1)));
    assert!(!p.matches(10, 0x1000, 5, r(123, 2)) && !p.matches(11, 0x1000, 7, r(123, 2)) && !p.matches(10, 0x2000, 7, r(123, 2)));
    assert!(!p.matches(10, 0x1000, 7, r(0, 0)) && !p.matches(10, 0x1000, 7, r(124, 2)) && !p.matches(10, 0x1000, 7, r(123, 3)));
    for amount in 1..=8 {
        for current in 0..=9 {
            assert_eq!(compatible_refresh(r(123, amount), r(123, current)), current != 0 && current <= amount);
            assert!(compatible_refresh(r(123, amount), r(0, 0)));
            assert!(!compatible_refresh(r(123, amount), r(124, current)));
            assert!(!compatible_refresh(r(123, amount), r(0, current + 1)));
        }
    }
    assert!(compatible_refresh(r(0, 0), r(0, 0)) && !compatible_refresh(r(0, 0), r(123, 1)));
}

#[test]
fn layout_table() {
    for group in [1u32, 2, 5, 6, 7] {
        for index in 0..48 {
            let (ir, br) = match group {
                2 => (43, 44),
                5 | 6 => (66, 65),
                _ => (19, 12),
            };
            let allowed = index < match group {
                2 => 32,
                5 | 6 => 16,
                _ => 48,
            };
            let icon = 2 + index / 8 * 9 + index % 8;
            assert_eq!(frame_layout(group, ir, br, index, icon).is_some(), allowed);
            assert!(frame_layout(group, ir + 1, br, index, icon).is_none());
            assert!(frame_layout(group, ir, br, index, icon + 1).is_none());
        }
    }
}

#[test]
fn screen_transform() {
    let mut v = [0.0f32; 24];
    let mut m = [0.0f32; 16];
    let g = [2.0 / 1280.0, 2.0 / 720.0, -1.0, 1.0];
    m[0] = 1.0;
    m[5] = 1.0;
    m[10] = 1.0;
    m[15] = 1.0;
    m[12] = 100.0;
    m[13] = -50.0;
    for k in 0..4 {
        v[k * 6] = if k & 1 != 0 { 36.0 } else { 0.0 };
        v[k * 6 + 1] = if k & 2 != 0 { -36.0 } else { 0.0 };
    }
    for scale in [0.5f32, 1.0, 2.0] {
        let out = screen_quad(&v, &m, &g, 1280.0 * scale, 720.0 * scale).unwrap();
        for k in 0..4 {
            assert!((out[k * 2] - (100.0 + if k & 1 != 0 { 36.0 } else { 0.0 }) * scale).abs() < 0.001);
            assert!((out[k * 2 + 1] - (50.0 + if k & 2 != 0 { 36.0 } else { 0.0 }) * scale).abs() < 0.001);
        }
    }
    v[0] = f32::NAN;
    assert!(screen_quad(&v, &m, &g, 1280.0, 720.0).is_none());
    v[0] = 0.0;
    assert!(screen_quad(&v, &m, &g, 0.0, 720.0).is_none());
    m[5] = 0.0;
    assert!(screen_quad(&v, &m, &g, 1280.0, 720.0).is_none());
}

#[test]
fn snapshots_never_expose_a_torn_pair() {
    let s: Snapshot<Binding, BINDING_WORDS> = Snapshot::new();
    assert!(s.read().is_none());
    std::thread::scope(|scope| {
        scope.spawn(|| {
            for i in 1..100_000u32 {
                assert!(s.publish(&Binding { batch: i, index: !i, ..Default::default() }));
            }
        });
        for _ in 0..100_000 {
            if let Some(b) = s.read() {
                assert_eq!(b.index, !b.batch);
            }
        }
    });
    assert_eq!(s.read().unwrap().batch, 99_999);
}

#[test]
fn the_mailbox_discards_oldest_and_counts_the_loss() {
    let m: Mailbox<u32, 16, 1> = Mailbox::new();
    assert!(m.read().is_none());
    for i in 0..4 {
        m.publish(&i);
    }
    assert_eq!((m.read(), m.read()), (Some(0), Some(1)));
    for i in 4..40 {
        m.publish(&i);
    }
    assert_eq!(m.read(), Some(24));
    assert!(m.overwritten.load(std::sync::atomic::Ordering::Relaxed) != 0);
    let mut last = 24;
    while let Some(v) = m.read() {
        assert_eq!(v, last + 1);
        last = v;
    }
    assert_eq!(last, 39);
}

#[test]
fn signed_quantity_bounds_and_independent_modes() {
    let mut items = [Reward::default(); 48];
    for multiplier in 1..=5 {
        assert_eq!(quantity_preflight(&items, 48, multiplier), QuantityFault::None);
        for (i, item) in items.iter_mut().enumerate() {
            *item = Reward { item: 10 + i as u16 % 3, amount: i as u16 + 1 };
        }
        assert_eq!(quantity_preflight(&items, 48, multiplier), QuantityFault::None);
        items[47].amount = (32767 / multiplier) as u16;
        assert_eq!(quantity_preflight(&items, 48, multiplier), QuantityFault::None);
        items[47].amount += 1;
        assert_eq!(quantity_preflight(&items, 48, multiplier), QuantityFault::Overflow);
        items[47] = Reward { item: 0, amount: 1 };
        assert_eq!(quantity_preflight(&items, 48, multiplier), QuantityFault::Record);
        items[47] = Reward { item: 1, amount: 0 };
        assert_eq!(quantity_preflight(&items, 48, multiplier), QuantityFault::Record);
        assert_eq!(quantity_preflight(&items, 49, multiplier), QuantityFault::Memory);
        items[47] = Reward { item: 1, amount: 1 };
    }
    assert_eq!(quantity_preflight(&items, 48, 0), QuantityFault::Multiplier);
    assert_eq!(quantity_preflight(&items, 48, 6), QuantityFault::Multiplier);
    let mode = Mode::new();
    for bits in 0..10u8 {
        mode.set(Preferences { force: bits & 1 != 0, multiplier: bits / 2 + 1 });
        let p = mode.preferences();
        assert!(p.force == (bits & 1 != 0) && p.multiplier == bits / 2 + 1);
        mode.set_force(!p.force);
        assert_eq!(mode.preferences().multiplier, p.multiplier);
    }
    mode.set(Preferences { force: true, multiplier: 5 });
    mode.set(Preferences { force: false, multiplier: 0 });
    assert!(mode.preferences().force && mode.preferences().multiplier == 5);
}

#[test]
fn the_ini_format_is_canonical() {
    for bits in 0..10u8 {
        let want = Preferences { force: bits & 1 != 0, multiplier: bits / 2 + 1 };
        let t = encode_preferences(want);
        let text = t.as_slice().to_vec();
        assert!(!String::from_utf8_lossy(&text).contains("version="));
        assert_eq!(decode_preferences(&text), Some(want));
        assert_eq!(decode_preferences(&text[b"[PleaseDoBetter]\n".len()..]), None);
        let mut x = text.clone();
        x[1] = b'X';
        assert_eq!(decode_preferences(&x), None);
        assert_eq!(decode_preferences(&[b"version=2\n", text.as_slice()].concat()), None);
        for i in 0..text.len() {
            let mut y = text.clone();
            y[i] ^= 0x80;
            assert_eq!(decode_preferences(&y), None);
        }
        assert_eq!(decode_preferences(&text[..text.len() - 1]), None);
        let legacy = format!("version=2\nforce_miraculous={}\n", want.force as u32);
        assert_eq!(decode_preferences(legacy.as_bytes()), None);
        assert_eq!(decode_preferences(&legacy.as_bytes()[10..]), None);
        assert_eq!(decode_preferences(&t.bytes), None);
    }
    for force in 0..2 {
        for doubled in 0..2 {
            let old = format!("force_miraculous={force}\ndouble_quantity={doubled}\n");
            assert_eq!(decode_preferences(old.as_bytes()), None);
        }
    }
    for value in [0u8, 6, 255] {
        assert_eq!(encode_preferences(Preferences { force: false, multiplier: value }).size, 0);
        let bad = format!("[PleaseDoBetter]\nforce_miraculous=0\nreward_multiplier={value}\n");
        assert_eq!(decode_preferences(bad.as_bytes()), None);
    }
}

// A recording filesystem running the production persistence.
#[derive(Default)]
struct Fs {
    primary: Vec<u8>,
    exists: bool,
    unavailable: bool,
    failure: u32,
    mounts: u32,
    handles: u32,
    guards: u32,
    commits: u32,
    writes: u32,
    next: u32,
}
impl Fs {
    fn balanced(&self) {
        assert!(self.mounts == 0 && self.handles == 0 && self.guards == 0);
    }
}
impl RawFs for Fs {
    fn enter_scope(&mut self) -> u32 {
        self.guards += 1;
        42
    }
    fn leave_scope(&mut self, token: u32) {
        assert!(token == 42 && self.guards == 1);
        self.guards -= 1;
    }
    fn mount(&mut self) -> bool {
        if self.unavailable {
            return false;
        }
        self.mounts += 1;
        true
    }
    fn unmount(&mut self) {
        assert_eq!(self.mounts, 1);
        self.mounts -= 1;
    }
    fn open(&mut self, handle: &mut u32, path: &CStr, _mode: i32) -> u32 {
        assert_eq!(path, PATH);
        if !self.exists {
            return 1;
        }
        if self.failure == 7 {
            return 1;
        }
        assert_eq!(self.handles, 0);
        self.handles += 1;
        self.next += 1;
        *handle = self.next;
        0
    }
    fn close(&mut self, _handle: u32) {
        assert_eq!(self.handles, 1);
        self.handles -= 1;
    }
    fn size(&mut self, out: &mut i64, _handle: u32) -> u32 {
        *out = self.primary.len() as i64;
        (self.failure == 8) as u32
    }
    fn read(&mut self, _handle: u32, _offset: i64, out: *mut u8, bytes: u32) -> u32 {
        // SAFETY: the production code passes its own buffer of at least `bytes`.
        unsafe {
            std::ptr::copy_nonoverlapping(self.primary.as_ptr(), out, bytes as usize);
            if self.failure == 5 && bytes != 0 {
                *out = b'!';
            }
        }
        (self.failure == 4) as u32
    }
    fn write(&mut self, _handle: u32, _offset: i64, data: *const u8, bytes: u32, flush: &u32) -> u32 {
        assert_eq!(*flush, 1);
        self.writes += 1;
        let kept = if self.failure == 2 { 1 } else { bytes as usize };
        // SAFETY: the production code passes its own text of at least `bytes`.
        self.primary = unsafe { std::slice::from_raw_parts(data, kept) }.to_vec();
        (self.failure == 2) as u32
    }
    fn flush(&mut self, _handle: u32) -> u32 {
        (self.failure == 3) as u32
    }
    fn resize(&mut self, _handle: u32, bytes: i64) -> u32 {
        self.primary.resize(bytes as usize, 0);
        (self.failure == 1) as u32
    }
    fn create(&mut self, path: &CStr, bytes: i64) -> u32 {
        assert_eq!(path, PATH);
        if self.failure == 9 {
            return 1;
        }
        self.exists = true;
        self.primary.resize(bytes as usize, 0);
        0
    }
    fn commit(&mut self, mount: &CStr) -> u32 {
        assert_eq!(mount, MOUNT);
        self.commits += 1;
        (self.failure == 6) as u32
    }
}

#[test]
fn production_persistence_round_trips_and_balances_every_failure() {
    let mut fs = Fs::default();
    let mut store = PreferenceStore::new();
    let session = Preferences { force: true, multiplier: 5 };
    assert!(store.save(&mut fs, session));
    fs.balanced();
    assert!(fs.exists && !String::from_utf8_lossy(&fs.primary).contains("version="));
    store.pending = true;
    assert_eq!(store.load(&mut fs), Some(session));
    fs.balanced();
    for bits in 0..10u8 {
        let wanted = Preferences { force: bits & 1 != 0, multiplier: bits / 2 + 1 };
        assert!(store.save(&mut fs, wanted));
        store.pending = true;
        assert_eq!(store.load(&mut fs), Some(wanted));
        fs.balanced();
    }
    for old in ["version=2\nforce_miraculous=1\n", "force_miraculous=1\ndouble_quantity=1\n", "force_miraculous=1\nreward_multiplier=5\n"] {
        fs.primary = old.as_bytes().to_vec();
        store.pending = true;
        assert_eq!(store.load(&mut fs), None);
        assert_eq!(fs.primary, old.as_bytes());
        fs.balanced();
    }
    let session = Preferences { force: false, multiplier: 5 };
    assert!(store.save(&mut fs, session) && store.save(&mut fs, session));
    for failure in 1..=9 {
        fs.failure = failure;
        fs.exists = failure != 9;
        assert!(!store.save(&mut fs, session), "failure {failure}");
        fs.balanced();
        assert!(store.status.to_str().unwrap().contains("session choice retained"), "failure {failure}");
    }
    fs.failure = 0;
    fs.unavailable = true;
    assert!(!store.save(&mut fs, session));
    fs.balanced();
    fs.unavailable = false;
    fs.exists = true;
    fs.primary = b"invalid primary".to_vec();
    store.pending = true;
    assert_eq!(store.load(&mut fs), None);
    fs.balanced();
    fs.exists = false;
    store.pending = true;
    assert_eq!(store.load(&mut fs), None);
    fs.balanced();
    let forced = Preferences { force: true, multiplier: 1 };
    assert!(store.save(&mut fs, forced));
    store.pending = true;
    assert_eq!(store.load(&mut fs), Some(forced));
}

#[test]
fn delayed_load_and_session_choices() {
    let mut fs = Fs::default();
    let mut store = PreferenceStore::new();
    assert_eq!(store.load(&mut fs), None);
    assert!(!store.pending && fs.mounts == 0 && fs.writes == 0);
    // Storage arrives after the user changed a setting: that choice wins.
    let mut fs = Fs { unavailable: true, ..Fs::default() };
    let mut store = PreferenceStore::new();
    assert_eq!(store.load(&mut fs), None);
    assert!(store.pending);
    store.changed();
    fs.unavailable = false;
    fs.exists = true;
    fs.primary = encode_preferences(Preferences { force: true, multiplier: 1 }).as_slice().to_vec();
    assert_eq!(store.load(&mut fs), None);
    let mut store = PreferenceStore::new();
    let mut fs = Fs::default();
    assert!(store.save(&mut fs, Preferences { force: true, multiplier: 1 }) && store.save(&mut fs, Preferences::default()));
    assert_eq!(decode_preferences(&fs.primary), Some(Preferences::default()));
    assert!(fs.commits == 2 && fs.writes == 2);
}

#[test]
fn comparison_flags_match_cmp() {
    assert_eq!(comparison_nzcv(5, 5), 0x6000_0000); // Z, C
    assert_eq!(comparison_nzcv(1, 2), 0x8000_0000); // N
    assert_eq!(comparison_nzcv(2, 1), 0x2000_0000); // C
    assert_eq!(comparison_nzcv(0x8000_0000, 1), 0x3000_0000); // C, V
}

// ---- hook publication ----
#[derive(Clone)]
struct Fake {
    memory: BTreeMap<u32, u32>,
    writes: u32,
    flushes: u32,
    prepares: u32,
    creates: u32,
    fail_write: u32,
    fail_flush: u32,
    rollback_after: u32,
    poststore: bool,
    external: bool,
    rollback_fail: bool,
    allocate: bool,
    prepared: bool,
    owned: bool,
    bad_mapping: bool,
    fail_close: bool,
    title: u64,
}
impl Platform for Fake {
    fn program(&self) -> Option<u64> {
        Some(self.title)
    }
    fn executable(&self, a: u32, n: u32) -> bool {
        !self.bad_mapping && (a >= 0x800000 || (self.memory.contains_key(&a) && self.memory.contains_key(&(a + n - 4))))
    }
    fn read(&self, a: u32) -> Option<u32> {
        self.memory.get(&a).copied()
    }
    fn write(&mut self, a: u32, expected: u32, value: u32, stored: &mut bool) -> bool {
        self.writes += 1;
        *stored = false;
        if self.rollback_fail && self.writes > self.rollback_after {
            return false;
        }
        if self.writes == self.fail_write && !self.poststore {
            return false;
        }
        if self.memory[&a] != expected {
            return false;
        }
        self.memory.insert(a, value);
        *stored = true;
        self.writes != self.fail_write
    }
    fn sync(&mut self, a: u32, _n: u32) -> u32 {
        self.flushes += 1;
        if self.external && self.flushes == 1 {
            self.memory.insert(a, 0xe1a00000);
        }
        if self.flushes == self.fail_flush { 99 } else { 0 }
    }
    fn create(&mut self, n: u32) -> bool {
        assert_eq!(n, 4096);
        self.creates += 1;
        self.owned = self.allocate;
        self.allocate
    }
    fn close(&mut self) -> bool {
        if self.fail_close {
            return false;
        }
        self.owned = false;
        true
    }
    fn owns_arena(&self) -> bool {
        self.owned
    }
    fn rx_base(&self) -> u32 {
        0x900000
    }
    fn prepare(&mut self, off: u32, _t: u32, _a: u32, _b: u32) -> bool {
        assert_eq!(off % 32, 0);
        self.prepares += 1;
        self.prepared
    }
    fn make_executable(&mut self) -> bool {
        self.prepared
    }
}
const HS: [Hook; 2] = [
    Hook { site: 0x10c, window: 0x100, detour: 0x800000, words: [1, 2, 3, 4, 5, 6, 7, 8], paired: true, chains: false },
    Hook { site: 0x20c, window: 0x200, detour: 0x800100, words: [9, 10, 11, 12, 13, 14, 15, 16], paired: true, chains: false },
];
const BASE: u32 = 0x100000;
fn fresh() -> Fake {
    let mut memory = BTreeMap::new();
    for h in HS {
        for j in 0..8 {
            memory.insert(BASE + h.window + 4 * j, h.words[j as usize]);
        }
    }
    Fake {
        memory, writes: 0, flushes: 0, prepares: 0, creates: 0, fail_write: 0, fail_flush: 0, rollback_after: 2,
        poststore: false, external: false, rollback_fail: false, allocate: true, prepared: true, owned: false,
        bad_mapping: false, fail_close: false, title: PROGRAM_ID,
    }
}

#[test]
fn a_clean_install_never_writes_twice() {
    let mut f = fresh();
    let mut t = Hooks::new();
    assert_eq!(t.install(&mut f, BASE, &HS).state, State::Applied);
    assert!(f.creates == 1 && f.prepares == 2 && f.flushes == 2 && t.original(&f, 0) == 0x900000);
    let writes = f.writes;
    assert!(t.install(&mut f, BASE, &HS).state == State::Applied && f.writes == writes);
}

#[test]
fn write_and_flush_failures_restore_everything() {
    for fail in 1..=4 {
        for after in [false, true] {
            let mut f = fresh();
            let before = f.memory.clone();
            f.fail_write = fail;
            f.poststore = after;
            let mut t = Hooks::new();
            assert_ne!(t.install(&mut f, BASE, &HS).state, State::Applied);
            assert!(f.memory == before && !f.owned);
        }
    }
    for fail in 1..=2 {
        let mut f = fresh();
        let before = f.memory.clone();
        f.fail_flush = fail;
        let mut t = Hooks::new();
        assert_eq!(t.install(&mut f, BASE, &HS).state, State::RolledBack);
        assert!(f.memory == before && !f.owned);
    }
}

#[test]
fn foreign_edits_and_failed_rollback_are_unsafe_and_keep_the_arena() {
    let mut f = fresh();
    f.fail_flush = 1;
    f.external = true;
    let mut t = Hooks::new();
    assert_eq!(t.install(&mut f, BASE, &HS).state, State::Unsafe);
    assert!(f.owned && f.memory[&0x10010c] == 0xe1a00000);
    let mut f = fresh();
    f.fail_flush = 1;
    f.rollback_fail = true;
    let mut t = Hooks::new();
    assert_eq!(t.install(&mut f, BASE, &HS).state, State::Unsafe);
    assert!(f.owned);
}

#[test]
fn rejection_happens_before_any_write_or_allocation() {
    for i in 0..2 {
        for j in 0..8 {
            let mut f = fresh();
            *f.memory.get_mut(&(BASE + HS[i].window + 4 * j)).unwrap() ^= 1;
            let mut t = Hooks::new();
            assert_eq!(t.install(&mut f, BASE, &HS).state, State::Rejected);
            assert!(f.writes == 0 && f.creates == 0);
        }
    }
    for which in 0..3 {
        let mut f = fresh();
        match which {
            0 => f.title = 0,
            1 => f.allocate = false,
            _ => f.prepared = false,
        }
        let mut t = Hooks::new();
        assert_eq!(t.install(&mut f, BASE, &HS).state, State::Rejected);
        assert!(f.writes == 0 && !f.owned);
    }
    for which in 0..7 {
        let mut f = fresh();
        let mut wrong = HS;
        let mut base = BASE;
        match which {
            0 => base = 0xffff_fffc,
            1 => wrong[0].site |= 1,
            2 => wrong[0].window += 16,
            3 => wrong[0].detour = 0,
            4 => wrong[0].detour = base + wrong[0].site,
            5 => wrong[1].site = wrong[0].site,
            _ => f.bad_mapping = true,
        }
        let mut t = Hooks::new();
        assert_eq!(t.install(&mut f, base, &wrong).state, State::Rejected, "which {which}");
        assert!(f.writes == 0 && f.creates == 0);
    }
    let mut f = fresh();
    f.prepared = false;
    f.fail_close = true;
    let mut t = Hooks::new();
    assert_eq!(t.install(&mut f, BASE, &HS).state, State::Unsafe);
    assert!(f.owned && f.writes == 0);
}

#[test]
fn a_later_conflict_is_reported_without_a_write() {
    let mut f = fresh();
    let mut t = Hooks::new();
    assert_eq!(t.install(&mut f, BASE, &HS).state, State::Applied);
    f.memory.insert(0x10010c, 0xdead_beef);
    let (writes, creates) = (f.writes, f.creates);
    let r = t.install(&mut f, BASE, &HS);
    assert!(r.state == State::Unsafe && r.failure == Failure::Changed && r.unsafe_words != 0);
    assert!(f.writes == writes && f.creates == creates && f.memory[&0x10010c] == 0xdead_beef);
}

#[test]
fn an_optional_boundary_group_cannot_roll_back_a_working_group() {
    for failure in 0..=6 {
        let mut f = fresh();
        let mut core = Hooks::new();
        assert_eq!(core.install(&mut f, BASE, &HS).state, State::Applied);
        let mut boundary = HIGHLIGHT_BOUNDARY;
        boundary.detour = 0x800200;
        for j in 0..8 {
            f.memory.insert(BASE + boundary.window + j * 4, boundary.words[j as usize]);
        }
        let before = f.memory.clone();
        let created = f.creates;
        match failure {
            1 => *f.memory.get_mut(&(BASE + boundary.window)).unwrap() ^= 1,
            2 => f.fail_write = f.writes + 1,
            3 => f.fail_write = f.writes + 2,
            _ => {}
        }
        if failure >= 4 {
            f.fail_flush = f.flushes + 1;
        }
        if failure == 5 {
            f.external = true;
            f.flushes = 0;
            f.fail_flush = 1;
        }
        if failure == 6 {
            f.rollback_fail = true;
            f.rollback_after = f.writes + 2;
        }
        let mut optional = Hooks::new();
        let r = optional.install(&mut f, BASE, &[boundary]);
        let expected = match failure {
            0 => State::Applied,
            1 | 2 => State::Rejected,
            5 | 6 => State::Unsafe,
            _ => State::RolledBack,
        };
        assert_eq!(r.state, expected, "failure {failure}");
        assert!(f.creates == created && core.report().state == State::Applied);
        for h in HS {
            for j in 0..8 {
                let a = BASE + h.window + j * 4;
                assert_eq!(f.memory[&a], before[&a]);
            }
        }
    }
}

#[test]
fn every_recipe_keeps_its_two_displaced_words_inside_its_window() {
    for h in SITES.iter().chain([&HIGHLIGHT_BOUNDARY, &PRESENTATION]) {
        assert!(h.site >= h.window && h.site + 8 <= h.window + 32);
    }
    assert_eq!(site_offset(0), 0x3822dc);
    assert_eq!(site_offset(1), 0x4d17f4);
}

// ---- kernel-backed platform ----
struct FakeKernel {
    words: BTreeMap<u32, u32>,
    mapping: MemoryInfo,
    query_rc: u32,
    info_rc: u32,
    flush_rc: u32,
    flushes: u32,
}
impl Kernel for FakeKernel {
    fn query(&self, _address: u64) -> Result<MemoryInfo, u32> {
        if self.query_rc != 0 { Err(self.query_rc) } else { Ok(self.mapping) }
    }
    fn get_info(&self, id: u32, _sub: u64) -> Result<u64, u32> {
        if self.info_rc != 0 {
            return Err(self.info_rc);
        }
        Ok(if id == 18 { PROGRAM_ID } else { 0 })
    }
    fn flush(&mut self, _a: u64, _n: u64) -> u32 {
        self.flushes += 1;
        self.flush_rc
    }
    fn create_code(&mut self, _p: u32, _n: u64) -> Result<u32, u32> {
        Ok(7)
    }
    fn control_code(&mut self, _h: u32, _o: u32, _a: u64, _n: u64, _p: u32) -> u32 {
        0
    }
    fn close(&mut self, _h: u32) -> u32 {
        0
    }
    fn source_page(&self) -> u32 {
        0x1000
    }
    fn load(&self, a: u32) -> u32 {
        self.words[&a]
    }
    fn store(&mut self, a: u32, v: u32) {
        self.words.insert(a, v);
    }
}
const PAGE: u32 = 0x40000;

#[test]
fn the_platform_checks_the_mapping_before_every_code_access() {
    let mapping = MemoryInfo { address: PAGE as u64, size: 4096, kind: 3, permissions: 5, ..Default::default() };
    let kernel = FakeKernel { words: BTreeMap::from([(PAGE, 0xebf57aaf)]), mapping, query_rc: 0, info_rc: 0, flush_rc: 0, flushes: 0 };
    let mut p = KernelPlatform::new(kernel);
    assert_eq!(p.program(), Some(PROGRAM_ID));
    p.kernel.info_rc = 9;
    assert_eq!(p.program(), None);
    p.kernel.info_rc = 0;
    assert!(p.executable(PAGE, 32));
    assert!(!p.executable(0, 4) && !p.executable(PAGE + 1, 4) && !p.executable(PAGE, 0));
    assert!(!p.executable(0xffff_fffc, 8) && !p.executable(PAGE + 4092, 8));
    p.kernel.query_rc = 7;
    assert_eq!(p.read(PAGE), None);
    p.kernel.query_rc = 0;
    p.kernel.mapping.kind = 0;
    assert!(!p.executable(PAGE, 4));
    p.kernel.mapping.kind = 3;
    p.kernel.mapping.permissions = 1;
    assert_eq!(p.read(PAGE), None);
    p.kernel.mapping.permissions = 5;
    p.kernel.mapping.address = PAGE as u64 + 4;
    assert_eq!(p.read(PAGE), None);
    p.kernel.mapping.address = PAGE as u64;
    p.kernel.mapping.size = 0x1_0000_0000;
    assert_eq!(p.read(PAGE), None);
    p.kernel.mapping.size = 4096;
    assert_eq!(p.read(PAGE), Some(0xebf57aaf));
    let mut stored = true;
    assert!(!p.write(PAGE, 0x1234, 0xe3a00001, &mut stored) && !stored);
    assert_eq!(p.kernel.words[&PAGE], 0xebf57aaf);
    assert!(p.write(PAGE, 0xebf57aaf, 0xe3a00001, &mut stored) && stored);
    assert_eq!(p.sync(PAGE, 4), 0);
    assert_eq!(p.kernel.flushes, 1);
    p.kernel.flush_rc = 0x4321;
    assert_eq!(p.sync(PAGE, 4), 0x4321);
    p.kernel.mapping.permissions = 1;
    assert_eq!(p.sync(PAGE, 4), u32::MAX);
    assert_eq!(p.kernel.flushes, 2);
    assert!(!p.write(PAGE, 0xe3a00001, 0, &mut stored) && !stored);
}

// Code below this address, unmapped address space above it, with ASLR at 16 MiB.
struct ArenaKernel {
    words: BTreeMap<u32, u32>,
}
impl Kernel for ArenaKernel {
    fn query(&self, address: u64) -> Result<MemoryInfo, u32> {
        Ok(if address >= 0x100_0000 {
            MemoryInfo { address: 0x100_0000, size: 0x10_0000, kind: 0, ..Default::default() }
        } else {
            MemoryInfo { address: 0, size: 0x100_0000, kind: 3, permissions: 5, ..Default::default() }
        })
    }
    fn get_info(&self, id: u32, _sub: u64) -> Result<u64, u32> {
        Ok(match id {
            12 => 0x100_0000,
            13 => 0x10_0000,
            18 => PROGRAM_ID,
            _ => 0,
        })
    }
    fn flush(&mut self, _a: u64, _n: u64) -> u32 { 0 }
    fn create_code(&mut self, _p: u32, _n: u64) -> Result<u32, u32> { Ok(7) }
    fn control_code(&mut self, _h: u32, _o: u32, _a: u64, _n: u64, _p: u32) -> u32 { 0 }
    fn close(&mut self, _h: u32) -> u32 { 0 }
    fn source_page(&self) -> u32 { 0x1000 }
    fn load(&self, a: u32) -> u32 { *self.words.get(&a).unwrap_or(&0) }
    fn store(&mut self, a: u32, v: u32) { self.words.insert(a, v); }
}

#[test]
fn trampolines_relocate_only_the_pinned_literal_and_refuse_other_pc_uses() {
    let target = 0x50000u32;
    let literal = target + 12 + 0x108;
    let mut p = KernelPlatform::new(ArenaKernel { words: BTreeMap::from([(literal, 0xcafe_f00d)]) });
    // Not mapped yet: nothing may be prepared.
    assert!(!p.prepare(0, target, 0xe92d4070, 0xe24dd008));
    assert!(p.create(4096) && p.owns_arena() && p.make_executable());
    let rw = 0x100_0000;
    // `ldr r0,[pc,#0x108]` becomes `ldr r0,[pc,#0xc]`, which reaches word 6 of its own slot.
    assert!(p.prepare(0, target, 0xe92d4070, 0xe59f0108));
    let slot: Vec<u32> = (0..8).map(|i| p.kernel.load(rw + i * 4)).collect();
    assert_eq!(slot, [0xe92d4070, 0xe59f000c, LDR_PC, target + 8, 0, 0, 0xcafe_f00d, 0]);
    // An ordinary prologue is copied as it stands.
    assert!(p.prepare(32, target, 0xe92d4ff0, 0xe24dd014));
    assert_eq!(p.kernel.load(rw + 36), 0xe24dd014);
    // Any other PC-relative second word, a non-push first word and a bad slot are refused.
    assert!(!p.prepare(64, target, 0xe92d4ff0, 0xe59f0108));
    assert!(!p.prepare(64, target, 0xe59f0000, 0xe24dd014));
    assert!(!p.prepare(65, target, 0xe92d4ff0, 0xe24dd014));
    assert!(!p.create(4096));
    assert!(p.close() && !p.owns_arena());
}

#[test]
fn a_chaining_entry_stacks_on_a_foreign_forge_hook_and_restores_it() {
    let mut hs = HS;
    hs[0].chains = true;
    let mut f = fresh();
    f.memory.insert(BASE + 0x10c, LDR_PC);
    f.memory.insert(BASE + 0x110, 0x0320_1000);
    f.memory.insert(BASE + 0x114, 0xdead_beef);
    let mut t = Hooks::new();
    assert_eq!(t.install(&mut f, BASE, &hs).state, State::Rejected, "past the pair the window stays exact");
    assert_eq!(f.writes, 0);
    let mut f = fresh();
    f.memory.insert(BASE + 0x10c, LDR_PC);
    f.memory.insert(BASE + 0x110, 0x0320_1000);
    let mut t = Hooks::new();
    assert_eq!(t.install(&mut f, BASE, &hs).state, State::Applied);
    assert!(f.memory[&(BASE + 0x10c)] == LDR_PC && f.memory[&(BASE + 0x110)] == hs[0].detour);
}

#[test]
fn only_paired_entries_chain_and_the_pc_relative_entry_does_not() {
    let chained: Vec<u32> = SITES.iter().filter(|h| h.chains).map(|h| h.site).collect();
    assert_eq!(chained, [0x382e1c, 0x38211c, 0x3874e0, 0x381d30, 0x623c08, 0x384848, 0x384408]);
    assert!(SITES.iter().filter(|h| h.chains).all(|h| h.site == h.window));
    assert!(!HIGHLIGHT_BOUNDARY.chains && !PRESENTATION.chains);
}

#[test]
fn a_foreign_hook_on_a_strict_entry_is_refused() {
    let mut f = fresh();
    f.memory.insert(BASE + 0x10c, LDR_PC);
    f.memory.insert(BASE + 0x110, 0x0320_1000);
    let mut t = Hooks::new();
    assert_eq!(t.install(&mut f, BASE, &HS).state, State::Rejected);
    assert_eq!(f.writes, 0);
}

#[test]
fn a_later_forge_hook_over_a_chaining_entry_is_not_a_conflict() {
    let mut hs = HS;
    hs[0].chains = true;
    let mut f = fresh();
    let mut t = Hooks::new();
    assert_eq!(t.install(&mut f, BASE, &hs).state, State::Applied);
    f.memory.insert(BASE + 0x110, 0x0320_1000);
    assert_eq!(t.install(&mut f, BASE, &[]).state, State::Applied);
    f.memory.insert(BASE + 0x10c, 0xdead_beef);
    assert_eq!(t.install(&mut f, BASE, &[]).state, State::Unsafe, "anything else over the entry is still a conflict");
}

#[test]
fn each_frame_is_tinted_and_reported_once() {
    let mut t = Tints::new();
    assert!(matches!(t.note(0x1000), Tint::New));
    assert!(matches!(t.note(0x1000), Tint::Known(0)));
    assert!(matches!(t.note(0x2000), Tint::New));
    assert!(t.report_change(1));
    assert!(!t.report_change(1), "a change is logged once");
    t.clear();
    assert!(matches!(t.note(0x2000), Tint::New), "a new screen starts over");
    assert!(t.report_change(0));
    for n in 1..64 {
        assert!(matches!(t.note(0x3000 + n), Tint::New));
    }
    assert!(matches!(t.note(0x9000), Tint::Full));
    assert!(matches!(t.note(0x3001), Tint::Known(1)));
}
