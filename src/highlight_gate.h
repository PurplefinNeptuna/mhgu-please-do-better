#pragma once
#include "hooks.h"
extern "C" void pdb_gateway_26();
namespace pdb {
// A safe instruction boundary alone cannot establish where a border belongs.
// Keep this gate closed until all three proofs have reproducible native fixtures.
constexpr bool verified_slot_frame_identity=false;
constexpr bool verified_gui_screen_transform=false;
constexpr bool verified_presented_frame_correspondence=false;
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
