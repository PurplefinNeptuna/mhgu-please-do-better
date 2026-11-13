//! Optional settings rows and a help topic in Purple-lib (its `API.md`). Purple-lib is looked up
//! by symbol at start-up; without it nothing here runs. The records mirror Purple-lib's API
//! version 2 (Purple-lib r8 and later); the row texts and the mapping between rows and `Preferences` are here so the host
//! tests can check them.
use crate::mode::Preferences;
use core::ffi::{CStr, c_char, c_void};

pub const API_VERSION: u32 = 2;
pub const EXPORT_VERSION: &[u8] = b"purplelib_api_version";
pub const EXPORT_ADD_OPTIONS: &[u8] = b"purplelib_add_options";
pub const EXPORT_ADD_HELP: &[u8] = b"purplelib_add_help";

#[repr(C)]
/// Purple-lib zeroes it before each call; Please do Better's rows are labels rows, which use the
/// first four fields.
pub struct OptionRow {
    pub name: *const c_char,
    pub help: *const c_char,
    pub labels: *const *const c_char,
    pub label_count: u32,
    pub kind: u32,
    pub value_count: u32,
    pub first: i32,
    pub step: i32,
    pub suffix: *const c_char,
    pub flags: u32,
}

#[repr(C)]
pub struct Options {
    pub size: u32,
    pub context: *mut c_void,
    pub title: Option<extern "C" fn(*mut c_void, u32) -> *const c_char>,
    pub row_count: u32,
    pub row: Option<extern "C" fn(*mut c_void, u32, u32, *mut OptionRow) -> bool>,
    pub get: Option<extern "C" fn(*mut c_void, u32) -> u32>,
    pub set: Option<extern "C" fn(*mut c_void, u32, u32)>,
    pub closed: Option<extern "C" fn(*mut c_void)>,
    /// For text rows, which Please do Better does not use.
    pub value_text: Option<extern "C" fn(*mut c_void, u32, u32, u32) -> *const c_char>,
}

#[repr(C)]
pub struct Help {
    pub size: u32,
    pub context: *mut c_void,
    pub category: u32,
    pub page_count: u32,
    pub title: Option<extern "C" fn(*mut c_void, u32) -> *const c_char>,
    pub page: Option<extern "C" fn(*mut c_void, u32, u32) -> *const c_char>,
    pub open: Option<extern "C" fn(*mut c_void)>,
}

#[cfg(target_pointer_width = "32")]
const _: () = assert!(
    core::mem::size_of::<Options>() == 36 && core::mem::size_of::<Help>() == 28 && core::mem::size_of::<OptionRow>() == 40
);

pub const TITLE: &CStr = c"Please do Better";
pub const ROW_FORCE: u32 = 0;
pub const ROW_MULTIPLIER: u32 = 1;
pub const ROWS: u32 = 2;

/// English, French, Spanish, German, Italian, Traditional and Simplified Chinese.
pub const LANGUAGES: usize = 7;
/// Index into the tables from the game's language byte, which Purple-lib passes (anything unknown
/// is English).
pub const fn language_index(byte: u32) -> usize {
    match byte {
        2 => 1,
        3 => 2,
        4 => 3,
        5 => 4,
        7 => 5,
        8 => 6,
        _ => 0,
    }
}

/// Purple-lib keeps every pointer it is given, so all text is static. The game's own words are
/// used where it has them: the skill name Miraculous Luck (skillData 502), its option labels
/// Off/On (StartMenuMsg 175/176), its words for rewards (ResultMsg 8) and Palicoes (StartMenuMsg 9).
pub struct RowText {
    pub name: [&'static CStr; LANGUAGES],
    pub help: [&'static CStr; LANGUAGES],
}
pub static ROW_TEXT: [RowText; ROWS as usize] = [
    RowText {
        name: [c"Force Miraculous Luck", c"Forcer Grande fortune", c"Forzar Suerte +2", c"Glücksverstärker erzwingen", c"Forza Gran fortuna", c"強制激運", c"强制激运"],
        help: [
            c"Use Miraculous Luck the next time\r\nrewards are generated.",
            c"Utilise Grande fortune lors de la\r\nprochaine génération de récompenses.",
            c"Usa Suerte +2 la próxima vez que\r\nse generen las recompensas.",
            c"Nutzt Glücksverstärker, wenn die\r\nnächste Belohnung erstellt wird.",
            c"Usa Gran fortuna la prossima volta\r\nche vengono generati i premi.",
            c"下次產生任務報酬時\r\n套用激運。",
            c"下次生成任务报酬时\r\n套用激运。",
        ],
    },
    RowText {
        name: [c"Reward multiplier", c"Multipl. récompenses", c"Multiplicador de recomp.", c"Belohnungsmultiplikator", c"Moltiplicatore premi", c"報酬倍率", c"报酬倍率"],
        help: [
            c"Multiply every occupied slot on the\r\nplayer reward pages.",
            c"Multiplie chaque emplacement occupé\r\ndes pages de récompenses du joueur.",
            c"Multiplica cada espacio ocupado de\r\nlas páginas de recompensas del jugador.",
            c"Vervielfacht jeden belegten Platz\r\nauf den Belohnungsseiten des Jägers.",
            c"Moltiplica ogni casella occupata\r\nnelle pagine dei premi del giocatore.",
            c"將玩家報酬頁面中\r\n每個有道具的欄位乘以倍率。",
            c"将玩家报酬页面中\r\n每个有道具的栏位乘以倍率。",
        ],
    },
];
/// Force Miraculous Luck's labels: the game's own option Off/On (StartMenuMsg 175/176).
pub static OFF_ON: [[&CStr; 2]; LANGUAGES] = [
    [c"Off", c"On"],
    [c"Désactivé", c"Activé"],
    [c"No", c"Sí"],
    [c"Aus", c"An"],
    [c"No", c"Sì"],
    [c"不使用", c"使用"],
    [c"不使用", c"使用"],
];
/// The multiplier's labels, the same in every language.
pub static MULTIPLIER: [&CStr; 5] = [c"1x", c"2x", c"3x", c"4x", c"5x"];

/// A row's labels in a language.
pub fn labels(row: u32, language: usize) -> &'static [&'static CStr] {
    match row {
        ROW_FORCE => &OFF_ON[language],
        _ => &MULTIPLIER,
    }
}

/// The value Purple-lib shows: the label index.
pub fn value(p: Preferences, row: u32) -> u32 {
    match row {
        ROW_FORCE => p.force as u32,
        ROW_MULTIPLIER => p.multiplier.clamp(1, 5) as u32 - 1,
        _ => 0,
    }
}

/// The preferences with one row set to a label index; None for an index out of range.
pub fn with_value(mut p: Preferences, row: u32, value: u32) -> Option<Preferences> {
    match (row, value) {
        (ROW_FORCE, 0..=1) => p.force = value == 1,
        (ROW_MULTIPLIER, 0..=4) => p.multiplier = value as u8 + 1,
        _ => return None,
    }
    Some(p)
}

/// Help topic in Village/Hub (category 18): five lines at most, about 40 columns a line (a CJK
/// character takes two).
pub const HELP_CATEGORY: u32 = 18;
pub const HELP_PAGES: usize = 3;
pub static HELP_TEXT: [[&CStr; HELP_PAGES]; LANGUAGES] = [
    [
        c"Please do Better marks the extra reward\r\nslots that Luck skills give with a\r\nwhite frame on the reward screen.",
        c"Force Miraculous Luck gives Miraculous\r\nLuck the next time rewards are\r\ngenerated, without changing skills.",
        c"Reward multiplier multiplies every\r\noccupied slot on the player reward\r\npages; the Palico page is unchanged.\r\nBoth are in Options > Mod Options.",
    ],
    [
        c"Please do Better encadre en blanc les\r\nemplacements de récompense en plus que\r\ndonnent les talents de chance.",
        c"Forcer Grande fortune applique Grande\r\nfortune à la prochaine génération des\r\nrécompenses, sans changer de talents.",
        c"Le multiplicateur multiplie chaque\r\nemplacement occupé des pages de\r\nrécompenses du joueur, pas celles des\r\nPalicos. Voir Options > Options de Mod.",
    ],
    [
        c"Please do Better marca con un marco\r\nblanco los espacios extra de\r\nrecompensa que dan las habilidades\r\nde suerte.",
        c"Forzar Suerte +2 aplica Suerte +2 la\r\npróxima vez que se generen las\r\nrecompensas, sin cambiar habilidades.",
        c"El multiplicador multiplica cada\r\nespacio ocupado de las páginas de\r\nrecompensas del jugador, no las de\r\nlos Camaradas. Está en Opciones >\r\nOpciones de Mod.",
    ],
    [
        c"Please do Better markiert die durch\r\nGlück zusätzlichen Belohnungsplätze\r\nmit einem weißen Rahmen.",
        c"Glücksverstärker erzwingen nutzt\r\nGlücksverstärker bei der nächsten\r\nBelohnung, ohne Fertigkeiten zu ändern.",
        c"Der Multiplikator vervielfacht jeden\r\nbelegten Platz der Belohnungsseiten\r\ndes Jägers, nicht die der Kameraden.\r\nUnter Optionen > Mod-Optionen.",
    ],
    [
        c"Please do Better evidenzia in bianco\r\ngli spazi premio extra dati dalle\r\nabilità della fortuna.",
        c"Forza Gran fortuna applica Gran\r\nfortuna alla prossima generazione\r\ndei premi, senza cambiare abilità.",
        c"Il moltiplicatore moltiplica ogni\r\ncasella occupata nelle pagine dei\r\npremi del giocatore, non quelle dei\r\nCompagni. In Opzioni > Opzioni Mod.",
    ],
    [
        c"Please do Better會以白框標示\r\n幸運類技能額外增加的報酬欄位。",
        c"「強制激運」會在下次產生報酬時\r\n套用激運，不需變更技能。",
        c"「報酬倍率」會將玩家報酬頁面中\r\n每個有道具的欄位乘以倍率，\r\n隨從的報酬不變。\r\n設定位於選項 > Mod選項。",
    ],
    [
        c"Please do Better会以白框标示\r\n幸运类技能额外增加的报酬栏位。",
        c"「强制激运」会在下次生成报酬时\r\n套用激运，不需更改技能。",
        c"「报酬倍率」会将玩家报酬页面中\r\n每个有道具的栏位乘以倍率，\r\n随从的报酬不变。\r\n设置位于选项 > Mod选项。",
    ],
];

/// Display width as the help screens count it, roughly: a CJK character is two columns.
pub fn columns(text: &str) -> usize {
    text.chars().map(|c| if (c as u32) >= 0x2e80 { 2 } else { 1 }).sum()
}

/// Reads `out.len()` bytes at `address`, or returns false without touching unmapped memory.
pub trait Memory {
    fn read(&mut self, address: u32, out: &mut [u8]) -> bool;
    fn words<const N: usize>(&mut self, address: u32) -> Option<[u32; N]> {
        let mut raw = [0u8; 64];
        let bytes = &mut raw[..N * 4];
        self.read(address, bytes).then(|| core::array::from_fn(|i| u32::from_le_bytes(bytes[i * 4..i * 4 + 4].try_into().unwrap())))
    }
}

/// A defined symbol of the NRO mapped at `base`. Forge maps an NRO's segments at their file
/// offsets, so the dynamic table (found through the header's MOD0 offset) and every symbol value
/// are offsets from `base`. Imports have value 0 and are never returned. The same reader as the
/// WishFinder bridge for My Weapon Tree.
pub fn nro_symbol(m: &mut impl Memory, base: u32, name: &[u8]) -> Option<u32> {
    if name.is_empty() || name.len() > 40 || m.words::<1>(base + 0x10)?[0] != u32::from_le_bytes(*b"NRO0") {
        return None;
    }
    let mod0 = m.words::<1>(base + 4)?[0];
    let [magic, dynamic] = m.words::<2>(base + mod0)?;
    if magic != u32::from_le_bytes(*b"MOD0") {
        return None;
    }
    let dynamic = mod0.wrapping_add((dynamic as i32) as u32);
    let (mut hash, mut strtab, mut symtab, mut strsz) = (None, None, None, None);
    for i in 0..32u32 {
        let [tag, value] = m.words::<2>(base + dynamic + i * 8)?;
        if tag == 0 {
            break;
        }
        match tag {
            4 => hash = Some(value),
            5 => strtab = Some(value),
            6 => symtab = Some(value),
            10 => strsz = Some(value),
            11 if value != 16 => return None,
            _ => {}
        }
    }
    let (hash, strtab, symtab, strsz) = (hash?, strtab?, symtab?, strsz?);
    let [_, count] = m.words::<2>(base + hash)?;
    if !(2..=4096).contains(&count) || strsz > 0x10_0000 {
        return None;
    }
    let mut needle = [0u8; 41];
    needle[..name.len()].copy_from_slice(name);
    for i in 1..count {
        let [st_name, st_value, _, _] = m.words::<4>(base + symtab + i * 16)?;
        if st_value == 0 || st_name >= strsz {
            continue;
        }
        let mut found = [0u8; 41];
        if !m.read(base + strtab + st_name, &mut found[..name.len() + 1]) {
            return None;
        }
        if found[..=name.len()] == needle[..=name.len()] {
            return Some(base + st_value);
        }
    }
    None
}
