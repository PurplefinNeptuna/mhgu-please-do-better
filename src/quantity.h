#pragma once
#include "attribution.h"
namespace pdb {
constexpr unsigned first_screen_capacity=48;
enum class QuantityFault : unsigned { None, Memory, Record, Overflow, Generation, Snapshot, Multiplier };

// Collection/appraisal consumes amounts as signed shorts. Keep the multiplied
// value <=32767 rather than allowing an apparently valid u16 to become negative.
// Validate every record before writing any, including empty item/amount pairs.
inline QuantityFault quantity_preflight(const Reward* items,unsigned count,unsigned multiplier) {
    if(multiplier<1 || multiplier>5)return QuantityFault::Multiplier;
    if(count>first_screen_capacity)return QuantityFault::Memory;
    for(unsigned i=0;i<count;++i) {
        if(bool(items[i].item)!=bool(items[i].amount))return QuantityFault::Record;
        if(uint32_t(items[i].amount)*multiplier>32767)return QuantityFault::Overflow;
    }
    return QuantityFault::None;
}
}
