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
fn snapshots_never_expose_a_torn_pair() {
    let s: Snapshot<[u32; 2], 2> = Snapshot::new();
    assert!(s.read().is_none());
    std::thread::scope(|scope| {
        scope.spawn(|| {
            for i in 1..100_000u32 {
                assert!(s.publish(&[i, !i]));
            }
        });
        for _ in 0..100_000 {
            if let Some([a, b]) = s.read() {
                assert_eq!(b, !a);
            }
        }
    });
    assert_eq!(s.read().unwrap()[0], 99_999);
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

// ---- hook recipes and windows ----
fn installed(h: &Hook, detour: u32) -> [u32; 8] {
    let mut w = h.words;
    w[h.at()] = LDR_PC;
    w[h.at() + 1] = detour;
    w
}

#[test]
fn every_recipe_is_valid_and_keeps_its_site_inside_its_window() {
    let hooks: Vec<Hook> = SITES.iter().enumerate().map(|(i, h)| Hook { detour: 0x0320_0000 + 4 * i as u32, ..*h }).collect();
    assert!(valid_recipe(&hooks));
    for h in SITES.iter() {
        assert!(h.site >= h.window && h.site + 8 <= h.window + 32);
    }
    assert_eq!(site_offset(0), 0x3822dc);
    assert_eq!(site_offset(1), 0x4d17f4);
    let mut bad = hooks.clone();
    bad[3].detour = 0;
    assert!(!valid_recipe(&bad), "a missing detour");
    let mut bad = hooks.clone();
    bad[3].site += 2;
    assert!(!valid_recipe(&bad), "a misaligned site");
    let mut bad = hooks.clone();
    bad[3].site = bad[3].window + 28;
    assert!(!valid_recipe(&bad), "displaced words past the window");
    let mut bad = hooks;
    bad[4].site = bad[3].site + 4;
    bad[4].window = bad[3].window;
    assert!(!valid_recipe(&bad), "overlapping sites");
}

#[test]
fn only_paired_entries_chain_and_the_pc_relative_entry_does_not() {
    let chained: Vec<u32> = SITES.iter().filter(|h| h.chains).map(|h| h.site).collect();
    assert_eq!(chained, [0x382e1c, 0x38211c, 0x3874e0, 0x381d30, 0x623c08, 0x384848, 0x384408]);
    assert!(SITES.iter().filter(|h| h.chains).all(|h| h.site == h.window));
    let main_count = SITES.iter().find(|h| h.site == 0x381fec).unwrap();
    assert!(main_count.paired && !main_count.chains);
    assert_eq!(main_count.words[..2], [0xe92d4070, 0xe59f0108], "push {{r4,r5,r6,lr}}; ldr r0,[pc,#0x108]");
}

#[test]
fn a_window_before_install_is_the_original_or_a_foreign_hook_on_a_chaining_entry() {
    for h in SITES.iter() {
        let h = Hook { detour: 0x0320_0100, ..*h };
        assert!(window_matches(&h, &h.words, false));
        let foreign = installed(&h, 0x0400_0000);
        assert_eq!(window_matches(&h, &foreign, false), h.chains, "foreign hook at {:x}", h.site);
        for j in 0..8 {
            let mut w = h.words;
            w[j] ^= 1;
            assert!(!window_matches(&h, &w, false), "changed word {j} at {:x}", h.site);
            if h.chains && j != h.at() && j != h.at() + 1 {
                let mut w = foreign;
                w[j] ^= 1;
                assert!(!window_matches(&h, &w, false), "a foreign hook does not excuse other words");
            }
        }
        let mut w = h.words;
        w[h.at()] = 0xe3a00001;
        assert!(!window_matches(&h, &w, false), "a cheat over the site is a conflict");
    }
}

#[test]
fn a_window_after_install_holds_our_branch_or_a_later_forge_hook_on_a_chaining_entry() {
    for h in SITES.iter() {
        let h = Hook { detour: 0x0320_0100, ..*h };
        assert!(window_matches(&h, &installed(&h, h.detour), true));
        assert!(!window_matches(&h, &h.words, true), "an unhooked site after install");
        assert_eq!(window_matches(&h, &installed(&h, 0x0400_0000), true), h.chains);
        let mut w = installed(&h, h.detour);
        w[(h.at() + 2) % 8] ^= 1;
        assert!(!window_matches(&h, &w, true));
    }
}

#[test]
fn forge_trampolines_must_hold_the_found_words_and_return_after_the_site() {
    let found = [0xe92d48f0, 0xe24dd008];
    assert!(trampoline_matches(0x0438_2e1c, found, &[found[0], found[1], LDR_PC, 0x0438_2e24]));
    assert!(trampoline_matches(0x0438_2e1c, [LDR_PC, 0x0400_0000], &[LDR_PC, 0x0400_0000, LDR_PC, 0x0438_2e24]),
        "a foreign branch moves with its literal");
    assert!(!trampoline_matches(0x0438_2e1c, found, &[found[0], found[1], LDR_PC, 0x0438_2e20]));
    assert!(!trampoline_matches(0x0438_2e1c, found, &[found[1], found[0], LDR_PC, 0x0438_2e24]));
    assert!(!trampoline_matches(0x0438_2e1c, found, &[found[0], found[1], 0, 0x0438_2e24]));
}

// ---- kernel queries ----
struct FakeKernel {
    regions: Vec<(u64, u64, u32, u32)>,
    memory: BTreeMap<u32, u32>,
    program: u64,
    flush: u32,
}
impl Kernel for FakeKernel {
    fn query(&self, address: u64) -> Result<MemoryInfo, u32> {
        let (start, size, kind, permissions) =
            self.regions.iter().copied().find(|&(s, n, _, _)| s <= address && address < s + n).unwrap_or((address, 4096, 0, 0));
        Ok(MemoryInfo { address: start, size, kind, permissions, ..Default::default() })
    }
    fn get_info(&self, id: u32, _: u64) -> Result<u64, u32> {
        if id == 18 { Ok(self.program) } else { Err(1) }
    }
    fn flush(&self, _: u64, _: u64) -> u32 {
        self.flush
    }
    fn load(&self, address: u32) -> u32 {
        self.memory.get(&address).copied().unwrap_or(0)
    }
}

#[test]
fn queries_check_the_program_and_the_whole_executable_span() {
    let mut k = FakeKernel { regions: vec![(0x1000, 0x1000, 3, PERM_RX), (0x2000, 0x1000, 3, 3)], memory: BTreeMap::new(), program: 0, flush: 0 };
    assert!(!is_mhgu(&k));
    k.program = 0x0100770008dd8000;
    assert!(is_mhgu(&k));
    assert!(executable(&k, 0x1000, 32) && executable(&k, 0x1fe0, 32));
    assert!(!executable(&k, 0x1fe4, 32), "a span running off the region");
    assert!(!executable(&k, 0x2000, 4), "writable but not executable");
    assert!(!executable(&k, 0x1002, 4) && !executable(&k, 0, 4) && !executable(&k, 0x1000, 0));
    for i in 0..8 {
        k.memory.insert(0x1100 + i * 4, i);
    }
    assert_eq!(window(&k, 0x1100), Some([0, 1, 2, 3, 4, 5, 6, 7]));
    assert_eq!(window(&k, 0x2000), None);
    assert!(sync(&k, 0x1100, 8));
    assert!(!sync(&k, 0x2000, 8));
    k.flush = 99;
    assert!(!sync(&k, 0x1100, 8));
}

// ---- Purple-lib ----
use please_do_better_core::mode::Preferences;
use please_do_better_core::purple_lib as purple;

#[test]
fn purple_lib_rows_map_to_the_preferences_both_ways() {
    let p = Preferences { force: false, multiplier: 1 };
    assert_eq!((purple::value(p, purple::ROW_FORCE), purple::value(p, purple::ROW_MULTIPLIER)), (0, 0));
    for value in 0..=4 {
        let q = purple::with_value(p, purple::ROW_MULTIPLIER, value).unwrap();
        assert_eq!(q.multiplier as u32, value + 1, "label {value} is {}x", value + 1);
        assert_eq!(purple::value(q, purple::ROW_MULTIPLIER), value);
        assert!(!q.force);
    }
    let on = purple::with_value(p, purple::ROW_FORCE, 1).unwrap();
    assert!(on.force && on.multiplier == 1);
    assert_eq!(purple::value(on, purple::ROW_FORCE), 1);
    assert_eq!(purple::with_value(p, purple::ROW_MULTIPLIER, 5), None, "6x does not exist");
    assert_eq!(purple::with_value(p, purple::ROW_FORCE, 2), None);
    assert_eq!(purple::with_value(p, 2, 0), None);
}

#[test]
fn purple_lib_rows_match_the_plugin_ui_settings() {
    assert_eq!(purple::ROW_TEXT.len() as u32, purple::ROWS);
    assert_eq!(purple::ROW_TEXT[0].name[0].to_str().unwrap(), "Force Miraculous Luck");
    assert_eq!(purple::ROW_TEXT[1].name[0].to_str().unwrap(), "Reward multiplier");
    for language in 0..purple::LANGUAGES {
        assert_eq!(purple::labels(purple::ROW_FORCE, language).len(), 2);
        let labels: Vec<_> = purple::labels(purple::ROW_MULTIPLIER, language).iter().map(|l| l.to_str().unwrap()).collect();
        assert_eq!(labels, ["1x", "2x", "3x", "4x", "5x"]);
    }
}

#[test]
fn every_language_maps_from_the_game_byte_and_unknown_is_english() {
    let expected = [(2, 1), (3, 2), (4, 3), (5, 4), (7, 5), (8, 6), (0, 0), (1, 0), (6, 0), (99, 0)];
    for (byte, index) in expected {
        assert_eq!(purple::language_index(byte), index, "{byte}");
    }
}

#[test]
fn purple_lib_text_fits_in_every_language() {
    assert_eq!(purple::HELP_CATEGORY, 0, "the page's own help");
    let fits = |text: &str, lines: usize| text.split("\r\n").count() <= lines && text.split("\r\n").all(|l| purple::columns(l) <= 40);
    for language in 0..purple::LANGUAGES {
        for page in purple::HELP_TEXT.iter().flat_map(|topic| topic[language]) {
            assert!(fits(page.to_str().unwrap(), 5), "{page:?}");
        }
        for row in &purple::ROW_TEXT {
            assert!(fits(row.help[language].to_str().unwrap(), 2), "{:?}", row.help[language]);
            assert!(purple::columns(row.name[language].to_str().unwrap()) <= 28, "{:?}", row.name[language]);
        }
    }
}

struct Bytes(Vec<u8>);
impl purple::Memory for Bytes {
    fn read(&mut self, address: u32, out: &mut [u8]) -> bool {
        let start = address as usize;
        match self.0.get(start..start + out.len()) {
            Some(src) => {
                out.copy_from_slice(src);
                true
            }
            None => false,
        }
    }
}

/// The lookup that finds Purple-lib, run on this build's own NRO loaded at base 0 (Forge maps an
/// NRO's segments at their file offsets): it must find the address nm reports for the ELF.
#[test]
fn the_symbol_lookup_finds_exports_in_a_real_nro() {
    let (Ok(nro), Ok(symbols)) = (std::env::var("PDB_NRO"), std::env::var("PDB_SYMBOLS")) else {
        eprintln!("PDB_NRO not set: ./build.sh test --host before a build; the full test sets it");
        return;
    };
    let mut memory = Bytes(std::fs::read(nro).unwrap());
    let listing = std::fs::read_to_string(symbols).unwrap();
    for name in ["forge_onInit", "forge_onUpdate", "forge_onImGuiFreeRender"] {
        let nm = listing
            .lines()
            .find_map(|l| l.strip_suffix(&format!(" T {name}")).map(|a| u32::from_str_radix(a, 16).unwrap()))
            .unwrap_or_else(|| panic!("{name} not in nm"));
        assert_eq!(purple::nro_symbol(&mut memory, 0, name.as_bytes()), Some(nm), "{name}");
    }
    assert_eq!(purple::nro_symbol(&mut memory, 0, purple::EXPORT_VERSION), None, "Please do Better is not Purple-lib");
    assert_eq!(purple::nro_symbol(&mut memory, 0x1000, b"forge_onInit"), None, "no NRO header at the wrong base");
}
