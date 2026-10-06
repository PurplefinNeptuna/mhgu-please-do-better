#pragma once
#include <stdint.h>

namespace pdb {
constexpr uint64_t program_id = 0x0100770008dd8000ull;
constexpr uint32_t replacement = 0xe3a00001u; // ARM mov r0, #1, without S.
struct Site { uint32_t window; uint32_t words[8]; };
// Pinned original main NSO, 32-byte windows; the replaced BL is word 3.
constexpr Site sites[2] = {
    {0x003822d0u, {0xe2804004u, 0xe3a010fbu, 0xe1a00004u, 0xebf57aafu,
                   0xe3a0501fu, 0xe3500000u, 0x1a00001cu, 0xe1a00004u}},
    {0x004d17e8u, {0xeafffda3u, 0xe1a00004u, 0xe3a010fbu, 0xebf67983u,
                   0xe3a05001u, 0xe3500001u, 0x1afffd9du, 0xe1a00004u}},
};
constexpr uint32_t site_offset(unsigned i) { return sites[i].window + 12; }
}
