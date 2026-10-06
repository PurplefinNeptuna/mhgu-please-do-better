#include "native_platform.h"
#include "patches.h"
#include "kernel_contract.h"
#include <assert.h>
#include <stdio.h>
#include <sys/mman.h>

static MemoryInfo mapping{};
static uint32_t query_rc = 0, info_rc = 0, flush_rc = 0;
static unsigned queries = 0, fail_query_call = 0, flushes = 0, checks = 0;
static uint32_t expected_flush = 0;
extern "C" Result pdb_svc_query(MemoryInfo* out, uint32_t* page, uint64_t a) {
    ++queries; *page = 0; *out = mapping; (void)a;
    return queries == fail_query_call ? 0x1234 : query_rc;
}
extern "C" Result pdb_svc_get_info(uint64_t* out, uint32_t id, uint32_t handle, uint64_t sub) {
    assert(id == 18 && handle == CUR_PROCESS_HANDLE && sub == 0);
    *out = pdb::program_id; return info_rc;
}
extern "C" Result pdb_svc_flush(uint32_t handle, uint64_t a, uint64_t size) {
    assert(handle == CUR_PROCESS_HANDLE && a == expected_flush && size == 4);
    ++flushes; return flush_rc;
}
#define CHECK(condition) do { assert(condition); ++checks; } while (0)
int main() {
    auto* page = static_cast<uint32_t*>(mmap(nullptr, 4096, PROT_READ|PROT_WRITE,
                                      MAP_PRIVATE|MAP_ANONYMOUS|MAP_32BIT, -1, 0));
    assert(page != MAP_FAILED && uintptr_t(page) <= 0xffffffffu);
    const auto address = uint32_t(uintptr_t(page));
    mapping = {address, 4096, 3, 0, 5, 0, 0, 0};
    pdb::NativePlatform p; uint64_t title = 0; uint32_t word = 0;
    CHECK(p.program(title) && title == pdb::program_id);
    info_rc = 9; CHECK(!p.program(title)); info_rc = 0;
    CHECK(p.executable(address, 32));
    CHECK(!p.executable(0, 4)); CHECK(!p.executable(address+1, 4));
    CHECK(!p.executable(address, 0)); CHECK(!p.executable(0xfffffffc, 8));
    CHECK(!p.executable(address+4092, 8));
    query_rc = 7; CHECK(!p.read(address, word)); query_rc = 0;
    mapping.type = 0; CHECK(!p.executable(address, 4)); mapping.type = 3;
    mapping.perm = 1; CHECK(!p.read(address, word)); mapping.perm = 5;
    mapping.addr = uint64_t(address)+4; CHECK(!p.read(address, word)); mapping.addr = address;
    mapping.size = 0x100000000ull; CHECK(!p.read(address, word)); mapping.size = 4096;
    page[0] = 0xebf57aaf; CHECK(p.read(address, word) && word == page[0]);
    bool stored = true;
    CHECK(!p.write(address, 0x1234, pdb::replacement, stored) && !stored && page[0] == 0xebf57aaf);
    CHECK(p.write(address, page[0], pdb::replacement, stored) && stored && page[0] == pdb::replacement);
    page[0] = 0xebf57aaf; fail_query_call = queries+2;
    CHECK(!p.write(address, page[0], pdb::replacement, stored) && stored && page[0] == pdb::replacement);
    fail_query_call = 0;
    expected_flush = address; CHECK(p.sync(address, 4) == 0 && flushes == 1);
    flush_rc = 0x4321; CHECK(p.sync(address, 4) == 0x4321 && flushes == 2);
    mapping.perm = 1; CHECK(p.sync(address, 4) == 0xffffffffu && flushes == 2);
    stored = true; CHECK(!p.write(address, page[0], 0, stored) && !stored && page[0] == pdb::replacement);
    assert(!munmap(page, 4096));
    printf("PASS: %u native platform checks (production backend, fake kernel)\n", checks);
}
