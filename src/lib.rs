//! Please do Better: marks verified extra luck reward slots with a pulsing gold border, optionally
//! forces Miraculous Luck, and scales player reward pages by a 1x to 5x multiplier. Interior taps run
//! through the audited gateways in `gateway.S`. Patches are process-lived; nothing unpatches during
//! gameplay. Forge's `forge_log` filters below its configured level.
#![no_std]
mod native;
mod purple_lib;
mod runtime;
mod settings;

use core::ffi::c_void;
use core::ptr::null;
use forge::sys::imgui::*;
use please_do_better_core::mode::Preferences;

// forge-rs names only the six-byte version prefix of Forge's 70-byte output record.
#[repr(C)]
struct PluginMetadata {
    version: forge::ForgeVersion,
    name: [u8; 64],
}
const _: () = assert!(
    core::mem::size_of::<*const u8>() == 4
        && core::mem::size_of::<PluginMetadata>() == 70
        && core::mem::offset_of!(PluginMetadata, name) == 6
);

#[unsafe(no_mangle)]
pub unsafe extern "C" fn forge_onLoad(params: *mut forge::PluginInitParams) {
    if params.is_null() {
        return;
    }
    let mut name = [0; 64];
    let label = concat!("Please do Better ", env!("PDB_VERSION")).as_bytes();
    name[..label.len()].copy_from_slice(label);
    // SAFETY: Forge owns the writable native metadata record for this call.
    unsafe {
        params.cast::<PluginMetadata>().write(PluginMetadata {
            version: forge::ForgeVersion { major: 1, minor: 5, patch: 1 },
            name,
        });
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn forge_onInit() {
    runtime::start();
    match purple_lib::register() {
        purple_lib::Registered::Done => log::info!("[please-do-better] settings and help added to Purple-lib"),
        purple_lib::Registered::Missing => {}
        purple_lib::Registered::OtherVersion(v) => {
            log::warn!("[please-do-better] Purple-lib API version {v} is not the supported 1; Mod Options not added")
        }
        purple_lib::Registered::Refused { options, help } => {
            log::warn!("[please-do-better] Purple-lib refused the registration (settings {options}, help {help})")
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn forge_onUpdate(_delta: f32) {
    runtime::update();
}

#[unsafe(no_mangle)]
pub unsafe extern "C" fn forge_onImGuiInit(context: *mut c_void, allocate: *mut c_void, release: *mut c_void) {
    // SAFETY: Forge supplies its live context and matching allocator callbacks with these ABI types.
    unsafe {
        igSetCurrentContext(context.cast());
        igSetAllocatorFunctions(
            core::mem::transmute::<*mut c_void, ImGuiMemAllocFunc>(allocate),
            core::mem::transmute::<*mut c_void, ImGuiMemFreeFunc>(release),
            core::ptr::null_mut(),
        );
    }
}

// Forge calls this inside Plugin UI, so it owns only the settings row.
#[unsafe(no_mangle)]
pub extern "C" fn forge_onImGuiRender() {
    // SAFETY: the current context was set in forge_onImGuiInit; every label is NUL-terminated and
    // the opened tree node is paired with the TreePop below.
    unsafe {
        if !igTreeNode_Str(c"Please do Better###pdb_panel".as_ptr()) {
            return;
        }
        let mut p: Preferences = runtime::requested_preferences();
        if igCheckbox(c"Force Miraculous Luck###pdb_force".as_ptr(), &mut p.force) {
            settings::changed();
            runtime::request_preferences(p);
        }
        let mut multiplier = p.multiplier as i32;
        // Clamp typed input as well as dragging; validate again before narrowing to the stored
        // byte so every published gameplay value stays within 1..5.
        if igSliderInt(
            c"Reward multiplier###pdb_multiplier".as_ptr(),
            &mut multiplier,
            1,
            5,
            c"%dx".as_ptr(),
            ImGuiSliderFlags::AlwaysClamp,
        ) {
            p.multiplier = multiplier.clamp(1, 5) as u8;
            settings::changed();
            runtime::request_preferences(p);
        }
        if igButton(c"Save settings###pdb_save".as_ptr(), ImVec2_c { x: 0.0, y: 0.0 }) {
            settings::save(p);
        }
        igTextUnformatted(settings::status().as_ptr(), null());
        igTreePop();
    }
}

// Keep all preference access with the ImGui callbacks; free-render runs with the settings panel
// closed too. Mode publication is the only cross-thread edit.
#[unsafe(no_mangle)]
pub extern "C" fn forge_onImGuiFreeRender() {
    // Changes made in Purple-lib's Mod Options: drop a pending load, then save once it closed.
    if purple_lib::EDITED.swap(false, core::sync::atomic::Ordering::AcqRel) {
        settings::changed();
    }
    if purple_lib::SAVE.swap(false, core::sync::atomic::Ordering::AcqRel) {
        settings::save(runtime::requested_preferences());
    }
    settings::retry_load();
}
