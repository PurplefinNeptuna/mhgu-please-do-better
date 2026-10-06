#include "native_platform.h"
#if defined(PDB_HOST_PLATFORM_TEST)
#include "kernel_contract.h"
#else
#include <switch.h>
#endif

extern "C" {
Result pdb_svc_query(MemoryInfo*, uint32_t*, uint64_t);
Result pdb_svc_get_info(uint64_t*, uint32_t, uint32_t, uint64_t);
Result pdb_svc_flush(uint32_t, uint64_t, uint64_t);
}
namespace pdb {
static_assert(sizeof(MemoryInfo) == 40 && Perm_Rx == 5 && CUR_PROCESS_HANDLE == 0xffff8001u,
              "Pinned ARM32 query/cache ABI");
bool NativePlatform::program(uint64_t& title) const {
    title = 0;
    return pdb_svc_get_info(&title, 18, CUR_PROCESS_HANDLE, 0) == 0;
}
bool NativePlatform::executable(uint32_t address, unsigned bytes) const {
    MemoryInfo info{}; uint32_t page = 0;
    const uint64_t end = uint64_t(address) + bytes;
    if (!address || (address & 3) || !bytes || end > 0x100000000ull ||
        pdb_svc_query(&info, &page, address) || info.type == MemType_Unmapped ||
        (info.perm & Perm_Rx) != Perm_Rx || info.addr > address ||
        info.addr > 0x100000000ull || info.size > 0x100000000ull - info.addr ||
        end > info.addr + info.size) return false;
    return true;
}
bool NativePlatform::read(uint32_t address, uint32_t& word) const {
    if (!executable(address, 4)) return false;
    word = *reinterpret_cast<volatile const uint32_t*>(uintptr_t(address));
    return true;
}
bool NativePlatform::write(uint32_t address, uint32_t expected, uint32_t value, bool& stored) const {
    stored = false;
    uint32_t original = 0;
    if (!read(address, original) || original != expected) return false;
    // Emulator-only direct publication, matching the maintained controls backend.
    // RX query checks mapping identity; it does not grant native Switch writes.
    *reinterpret_cast<volatile uint32_t*>(uintptr_t(address)) = value;
    stored = true;
    __asm__ volatile("" ::: "memory");
    uint32_t result = 0;
    return read(address, result) && result == value;
}
uint32_t NativePlatform::sync(uint32_t address, unsigned bytes) const {
    if (!executable(address, bytes)) return 0xffffffffu; // private invalid-range sentinel
    __asm__ volatile("" ::: "memory");
#if defined(__arm__)
    __asm__ volatile("dsb sy" ::: "memory");
#endif
    const Result rc = pdb_svc_flush(CUR_PROCESS_HANDLE, address, bytes);
#if defined(__arm__)
    __asm__ volatile("dsb sy\n\tisb" ::: "memory");
#endif
    __asm__ volatile("" ::: "memory");
    // A zero result checks the SVC, not Eden translation freshness.
    return rc;
}
}
