//! Optional settings rows and their page help in Purple-lib (its `API.md`). Purple-lib calls the
//! plugin's `purplelib_on_register` with its table of functions; without Purple-lib nothing here
//! runs. The records and the table mirror Purple-lib's API version 3 (Purple-lib r17 and later); a
//! later API version still reads them. The row texts and the mapping between rows and
//! `Preferences` are here so the host tests can check them.
use crate::mode::Preferences;
use core::ffi::{CStr, c_char, c_void};

pub const API_VERSION: u32 = 3;

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
    /// For text rows and action rows, which Please do Better does not use.
    pub value_text: Option<extern "C" fn(*mut c_void, u32, u32, u32) -> *const c_char>,
    pub action: Option<extern "C" fn(*mut c_void, u32)>,
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

/// Purple-lib's functions, as it passes them to `purplelib_on_register`; valid for the whole run.
#[repr(C)]
pub struct Api {
    pub version: u32,
    pub add_options: extern "C" fn(*const Options) -> bool,
    pub add_help: extern "C" fn(*const Help) -> bool,
    pub hold_input: extern "C" fn(),
    pub options_shown: extern "C" fn(*const Options) -> bool,
    pub options_row: extern "C" fn(*const Options) -> i32,
    pub add_set_help: extern "C" fn(*const Options, *const Help) -> bool,
}

#[cfg(target_pointer_width = "32")]
const _: () = assert!(
    core::mem::size_of::<Options>() == 40
        && core::mem::size_of::<Help>() == 28
        && core::mem::size_of::<OptionRow>() == 40
        && core::mem::size_of::<Api>() == 28
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

/// The page's own help, which the help button opens on the Mod Options page
/// (`purplelib_add_set_help`, category 0): one topic per row, titled with the row's name, in row
/// order. A page has five lines at most, about 40 columns a line (a CJK character takes two).
pub const HELP_CATEGORY: u32 = 0;
pub const HELP_PAGES: usize = 2;
/// `HELP_TEXT[row][language][page]`: what the option does, then why it is there.
pub static HELP_TEXT: [[[&CStr; HELP_PAGES]; LANGUAGES]; ROWS as usize] = [
    [
        [
            c"Gives you Miraculous Luck the next time\r\nrewards are generated, without changing\r\nyour skills. Slots added by any Luck\r\nskill get a white frame on the reward\r\nscreen.",
            c"Miraculous Luck gives the most reward\r\nslots, but your gear needs a Luck skill\r\nfor it. This option gets you those slots\r\nwhile you keep the skills you want.",
        ],
        [
            c"Donne Grande fortune à la prochaine\r\ngénération des récompenses, sans changer\r\nde talents. Les emplacements en plus dus\r\nà la chance ont un cadre blanc.",
            c"Grande fortune donne le plus\r\nd'emplacements, mais demande un talent\r\nde chance sur l'équipement. Cette option\r\nles donne en gardant vos talents.",
        ],
        [
            c"Aplica Suerte +2 la próxima vez que se\r\ngeneren las recompensas, sin cambiar\r\nhabilidades. Los espacios extra de las\r\nhabilidades de suerte tienen un marco\r\nblanco.",
            c"Suerte +2 da el máximo de espacios,\r\npero requiere una habilidad de suerte\r\nen el equipo. Esta opción los da sin\r\nque cambies de habilidades.",
        ],
        [
            c"Nutzt Glücksverstärker bei der nächsten\r\nBelohnung, ohne Fertigkeiten zu ändern.\r\nZusätzliche Plätze durch Glück erhalten\r\neinen weißen Rahmen.",
            c"Glücksverstärker gibt die meisten\r\nBelohnungsplätze, braucht aber eine\r\nGlücksfertigkeit auf der Ausrüstung.\r\nSo behältst du deine Fertigkeiten.",
        ],
        [
            c"Applica Gran fortuna alla prossima\r\ngenerazione dei premi, senza cambiare\r\nabilità. Gli spazi extra dati dalla\r\nfortuna hanno una cornice bianca.",
            c"Gran fortuna dà il massimo degli spazi,\r\nma richiede un'abilità della fortuna\r\nsull'equipaggiamento. Questa opzione li\r\ndà senza cambiare le tue abilità.",
        ],
        [
            c"下次產生報酬時套用激運，\r\n不需變更技能。\r\n幸運類技能額外增加的報酬欄位\r\n會以白框標示。",
            c"激運能得到最多的報酬欄位，\r\n但需要裝備提供幸運類技能。\r\n此選項讓你保留想要的技能，\r\n同時得到這些欄位。",
        ],
        [
            c"下次生成报酬时套用激运，\r\n不需更改技能。\r\n幸运类技能额外增加的报酬栏位\r\n会以白框标示。",
            c"激运能得到最多的报酬栏位，\r\n但需要装备提供幸运类技能。\r\n此选项让你保留想要的技能，\r\n同时得到这些栏位。",
        ],
    ],
    [
        [
            c"Multiplies the quantity in every\r\noccupied slot on the player reward\r\npages, from 1x to 5x. The items and the\r\nnumber of slots stay the same. Palico\r\nrewards are not multiplied.",
            c"Use it when you need many of one\r\nmaterial and don't want to repeat the\r\nsame hunt over and over. 1x leaves\r\nrewards as the game gives them.",
        ],
        [
            c"Multiplie de 1x à 5x chaque emplacement\r\noccupé des pages de récompenses du\r\njoueur. Les objets et le nombre\r\nd'emplacements ne changent pas. Les\r\nPalicos ne sont pas concernés.",
            c"Utile pour obtenir beaucoup d'un même\r\nmatériau sans refaire la même chasse.\r\nÀ 1x, les récompenses sont celles du\r\njeu.",
        ],
        [
            c"Multiplica de 1x a 5x cada espacio\r\nocupado de las páginas de recompensas\r\ndel jugador. Los objetos y el número de\r\nespacios no cambian. Las recompensas\r\nde los Camaradas no se multiplican.",
            c"Útil cuando necesitas mucho de un\r\nmaterial y no quieres repetir la misma\r\ncacería. Con 1x las recompensas no\r\ncambian.",
        ],
        [
            c"Vervielfacht jeden belegten Platz der\r\nBelohnungsseiten des Jägers um 1x bis\r\n5x. Gegenstände und Anzahl der Plätze\r\nbleiben gleich. Belohnungen der\r\nKameraden bleiben unverändert.",
            c"Nützlich, wenn du viel von einem\r\nMaterial brauchst und dieselbe Jagd\r\nnicht wiederholen willst. Bei 1x\r\nbleiben die Belohnungen gleich.",
        ],
        [
            c"Moltiplica da 1x a 5x ogni casella\r\noccupata nelle pagine dei premi del\r\ngiocatore. Oggetti e numero di caselle\r\nnon cambiano. I premi dei Compagni non\r\nvengono moltiplicati.",
            c"Utile quando serve molto di un\r\nmateriale e non vuoi ripetere la\r\nstessa caccia. A 1x i premi restano\r\nquelli del gioco.",
        ],
        [
            c"將玩家報酬頁面中每個有道具的\r\n欄位乘以1至5倍。\r\n道具與欄位數量不變，\r\n隨從的報酬也不變。",
            c"需要大量同一種素材時，\r\n不必一再重複同一場狩獵。\r\n設為1x時報酬維持原樣。",
        ],
        [
            c"将玩家报酬页面中每个有道具的\r\n栏位乘以1至5倍。\r\n道具与栏位数量不变，\r\n随从的报酬也不变。",
            c"需要大量同一种素材时，\r\n不必一再重复同一场狩猎。\r\n设为1x时报酬维持原样。",
        ],
    ],
];

/// Display width as the help screens count it, roughly: a CJK character is two columns.
pub fn columns(text: &str) -> usize {
    text.chars().map(|c| if (c as u32) >= 0x2e80 { 2 } else { 1 }).sum()
}
