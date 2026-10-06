#pragma once
#include <stdint.h>
namespace pdb {
class NativePlatform {
    uint32_t handle = 0, rw = 0, rx = 0;
    bool owner_mapped = false, slave_mapped = false;
public:
    bool program(uint64_t& title) const;
    bool executable(uint32_t address, unsigned bytes) const;
    bool read(uint32_t address, uint32_t& word) const;
    bool write(uint32_t address, uint32_t expected, uint32_t value, bool& stored) const;
    uint32_t sync(uint32_t address, unsigned bytes) const;
    bool create(unsigned bytes);
    bool close();
    bool owns_arena() const { return handle != 0; }
    uint32_t rx_base() const { return rx; }
    bool prepare(unsigned offset, uint32_t target, uint32_t first, uint32_t second);
    bool make_executable();
};
}
