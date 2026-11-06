//! Hook recipes and the byte checks made before and after Forge installs them. Forge writes
//! `ldr pc,[pc,#-4]` and the detour address over a site's first two words; this crate never
//! writes code.
pub const PROGRAM_ID: u64 = 0x0100770008dd8000;
pub const LDR_PC: u32 = 0xe51ff004;

#[derive(Clone, Copy, Debug)]
pub struct Hook {
    pub site: u32,
    pub window: u32,
    pub detour: u32,
    /// The original 32 bytes at `window`.
    pub words: [u32; 8],
    /// The gateway continues into a callable original of this entry.
    pub paired: bool,
    /// Runs the original once with its arguments and returns its result, so another plugin's Forge
    /// hook may sit on this entry, found there at install or laid over ours later.
    pub chains: bool,
}
impl Hook {
    pub const EMPTY: Self = Self { site: 0, window: 0, detour: 0, words: [0; 8], paired: false, chains: false };
    /// Index of the site's first word in `words`.
    pub const fn at(&self) -> usize {
        ((self.site - self.window) / 4) as usize
    }
}

/// Alignment, window bounds, a nonzero detour and no two sites overlapping their eight bytes.
pub fn valid_recipe(hooks: &[Hook]) -> bool {
    hooks.iter().enumerate().all(|(i, h)| {
        (h.site | h.window | h.detour) & 3 == 0
            && h.detour != 0
            && h.site >= h.window
            && h.site as u64 + 8 <= h.window as u64 + 32
            && hooks[..i].iter().all(|o| h.site as u64 + 8 <= o.site as u64 || o.site as u64 + 8 <= h.site as u64)
    })
}

/// The window as it may legitimately be found. Before install (`installed == false`) the site
/// holds its original words, or, on a chaining entry, another plugin's Forge branch. After install
/// it holds our branch, or, on a chaining entry, any Forge branch laid over ours. Every other word
/// stays exact either way, so a different game build is still refused.
pub fn window_matches(h: &Hook, words: &[u32; 8], installed: bool) -> bool {
    let at = h.at();
    let branch = words[at] == LDR_PC;
    let site = if installed {
        branch && (words[at + 1] == h.detour || h.chains)
    } else {
        (words[at] == h.words[at] && words[at + 1] == h.words[at + 1]) || (h.chains && branch)
    };
    site && (0..8).filter(|&j| j != at && j != at + 1).all(|j| words[j] == h.words[j])
}

/// Forge's ARM trampoline: the two words found at the site, then `ldr pc,[pc,#-4]` and site + 8.
pub fn trampoline_matches(site: u32, found: [u32; 2], trampoline: &[u32; 4]) -> bool {
    *trampoline == [found[0], found[1], LDR_PC, site.wrapping_add(8)]
}
