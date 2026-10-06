#pragma once
#include "hooks.h"
extern "C" void pdb_gateway_26();
extern "C" void pdb_gateway_27();
namespace pdb {
// R6 fixtures trace resource node ordinals, all pinned GUI position programs,
// and the native producer/executor/present routes. Unsupported paths fail closed.
constexpr bool verified_slot_frame_identity=true;
constexpr bool verified_gui_screen_transform=true;
constexpr bool verified_presented_frame_correspondence=true;
constexpr bool highlight_rendering_accepted=verified_slot_frame_identity &&
    verified_gui_screen_transform && verified_presented_frame_correspondence;
inline Hook highlight_boundary_recipe() {
    // Success paths of both texture-vertex constructors join here. The fixed
    // gateway has no callable original and requires no trampoline arena.
    return {0x00a4fe50,0x00a4fe50,uint32_t(uintptr_t(pdb_gateway_26)),
        {0xe5960000,0xe200000f,0xe3500006,0x8a000011,
         0xe3a01001,0xe3a02036,0xe1120011,0x0a000006},false};
}
}

namespace pdb {
inline Hook presentation_recipe() {
    // Tail of the game's NVN wrapper: MOV r0,r12 / BX r3. The fixed gateway
    // records the exact queue/window/index, then tail-calls the installed Forge
    // interceptor with the native LR and all argument/state registers intact.
    return {0x0086a330,0x0086a31c,uint32_t(uintptr_t(pdb_gateway_27)),
        {0xe3041740,0xe0801001,0xe59f000c,0xe79f0000,
         0xe5903000,0xe1a0000c,0xe12fff13,0x00fd7000},false};
}
}
