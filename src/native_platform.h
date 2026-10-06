#pragma once
#include <stdint.h>
namespace pdb {
class NativePlatform {
public:
    bool program(uint64_t& title) const;
    bool executable(uint32_t address, unsigned bytes) const;
    bool read(uint32_t address, uint32_t& word) const;
    bool write(uint32_t address, uint32_t expected, uint32_t value, bool& stored) const;
    uint32_t sync(uint32_t address, unsigned bytes) const;
};
}
