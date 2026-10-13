#include "native_platform.h"
#include "runtime.h"
#include "settings.h"
#include <forge/log.h>
// This maintained header lacks a C++ linkage guard; installed exports are C.
extern "C" {
#include <forge/mem.h>
}
#include <stdarg.h>
#define CIMGUI_DEFINE_ENUMS_AND_STRUCTS
#include <cimgui.h>
#include <stddef.h>

struct ForgeVersion { uint16_t major, minor, patch; };
struct PluginInitParam { ForgeVersion required_ver; char name[64]; };
static_assert(sizeof(void*) == 4 && sizeof(PluginInitParam) == 70 &&
              offsetof(PluginInitParam, name) == 6, "Native Forge plugin ARM32 ABI");

extern "C" void init() {}
extern "C" void fini() {} // Patches are process-lived; never unpatch during gameplay.
extern "C" void forge_onLoad(PluginInitParam* out) {
    if (!out) return;
    auto* bytes = reinterpret_cast<volatile unsigned char*>(out);
    for (unsigned i = 0; i < sizeof(*out); ++i) bytes[i] = 0;
    out->required_ver = {1, 4, 1};
    const char* name = "Please do Better";
    for (unsigned i = 0; name[i]; ++i) bytes[offsetof(PluginInitParam, name)+i] = name[i];
}
extern "C" void forge_onInit() { pdb::install(); static bool reported; if(reported)return; reported=true; forge_log_info("[please-do-better] r21-multiplier loaded; %s",pdb::startup_status()); }
extern "C" void forge_onUpdate(float) { pdb::update(); }
extern "C" void forge_onImGuiInit(void* context, void* allocate, void* release) {
    igSetCurrentContext(static_cast<ImGuiContext*>(context));
    igSetAllocatorFunctions(reinterpret_cast<ImGuiMemAllocFunc>(allocate),
                           reinterpret_cast<ImGuiMemFreeFunc>(release), nullptr);
}
extern "C" void forge_onImGuiRender() {
    if (!igTreeNode_Str("Please do Better###pdb_panel")) return;
    auto p=pdb::requested_preferences();
    if(igCheckbox("Force Miraculous Luck###pdb_force", &p.force)) {
        pdb::preferences_changed();pdb::request_preferences(p);
    }
    int multiplier=p.multiplier;
    // Clamp typed input as well as dragging; validate again before narrowing
    // to the stored byte so every published gameplay value stays within 1..5.
    if(igSliderInt("Reward multiplier###pdb_multiplier", &multiplier,1,5,"%dx",ImGuiSliderFlags_AlwaysClamp)) {
        multiplier=multiplier<1?1:multiplier>5?5:multiplier;
        p.multiplier=uint8_t(multiplier);
        pdb::preferences_changed();pdb::request_preferences(p);
    }
    if(igButton("Save settings###pdb_save",ImVec2_c{0,0}))pdb::save_preferences(p);
    igTextUnformatted(pdb::preferences_status(),nullptr);
    igTreePop();
}
extern "C" void forge_onImGuiFreeRender() {
    // Forge update and NVN presentation need not share a thread. Keep all
    // preference access with the ImGui callbacks; free-render runs with the
    // settings panel closed too. Mode publication is the only cross-thread edit.
    static uint32_t retry=59;
    if(pdb::preferences_pending() && ++retry>=60) {
        retry=0;pdb::Preferences p{};
        if(pdb::load_preferences(p))pdb::request_preferences(p);
    }
    pdb::render();
}
