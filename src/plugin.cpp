#include "native_platform.h"
#include "transaction.h"
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
static pdb::NativePlatform platform;
static pdb::Transaction<pdb::NativePlatform> transaction(platform);
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
extern "C" void forge_onInit() {
    const auto r = transaction.install(forge_mem_getMainTextAddr());
    forge_log(r.state == pdb::State::Applied ? LOG_LEVEL_INFO : LOG_LEVEL_ERROR,
              "[please-do-better] %s reason=%s site=%u owned=0x%X rollback=0x%X cache=0x%X rollback_cache=0x%X",
              pdb::status(r.state), pdb::failure_status(r.failure), r.site, r.owned, r.rollback_failed,
              r.cache_result, r.rollback_cache_result);
    forge_log_info("[please-do-better] r1: Miraculous Luck branch; no equipped luck skill required. "
                   "Translation freshness/gameplay unverified; legacy Great Luck cheat must be disabled.");
}
extern "C" void forge_onUpdate(float) {}
extern "C" void forge_onImGuiInit(void* context, void* allocate, void* release) {
    igSetCurrentContext(static_cast<ImGuiContext*>(context));
    igSetAllocatorFunctions(reinterpret_cast<ImGuiMemAllocFunc>(allocate),
                           reinterpret_cast<ImGuiMemFreeFunc>(release), nullptr);
}
extern "C" void forge_onImGuiRender() {
    if (!igTreeNode_Str("Please do Better###pdb_panel")) return;
    const auto r = transaction.report();
    igTextUnformatted(pdb::status(r.state), nullptr);
    igTextUnformatted("Reproduces Great Luck cheat's Miraculous Luck reward branch.", nullptr);
    igTextUnformatted("No equipped luck skill required. Gameplay/cache freshness unverified.", nullptr);
    igTextUnformatted("Disable the legacy cheat. Removing this plugin requires a full restart.", nullptr);
    if (igTreeNode_Str("Diagnostics###pdb_diagnostics")) {
        igText("r1 state=%u failure=%u site=%u", unsigned(r.state), unsigned(r.failure), r.site);
        igTextUnformatted(pdb::failure_status(r.failure), nullptr);
        igText("Owned=0x%X rollback failures=0x%X cache result=0x%X", r.owned, r.rollback_failed, r.cache_result);
        igText("Rollback cache result=0x%X", r.rollback_cache_result);
        igTreePop();
    }
    igTreePop();
}
extern "C" void forge_onImGuiFreeRender() {}
