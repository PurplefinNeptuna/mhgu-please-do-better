#pragma once
#include <stdint.h>
using Result = uint32_t;
struct MemoryInfo {
    uint64_t addr, size;
    uint32_t type, attr, perm, ipc_refcount, device_refcount, padding;
};
constexpr uint32_t MemType_Unmapped = 0, Perm_Rx = 5, CUR_PROCESS_HANDLE = 0xffff8001u;
