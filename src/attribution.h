#pragma once
#include <stdint.h>

namespace pdb {
constexpr unsigned normal_luck = 22, reward_cap = 8;
// Counterfactual SLOT count only, using the already-observed rolls. This does
// not predict the item RNG sequence of a second, unmodified game execution.
struct Attribution {
    uint32_t threshold = 0, normal_stop = reward_cap;
    bool known = false, valid = true;
    uint32_t comparisons=0, last_slots=0, last_roll=0, first_slots=0;
    void begin(unsigned tier, unsigned first=UINT32_MAX) {
        threshold = tier; normal_stop = reward_cap; known = true;
        first_slots=first;
        comparisons=last_slots=last_roll=0;
        valid = tier == 8 || tier == 16 || tier == 22 || tier == 25 || tier == 28 || tier == 31;
    }
    void compare(unsigned slots, unsigned roll) {
        if (!known || slots >= reward_cap || roll > 31) { valid = false; return; }
        if(!comparisons && first_slots!=UINT32_MAX && slots!=first_slots)valid=false;
        if(comparisons && (last_roll>=threshold || slots!=last_slots+1))valid=false;
        ++comparisons;last_slots=slots;last_roll=roll;
        if (valid && threshold > normal_luck && roll >= normal_luck && roll < threshold &&
            normal_stop == reward_cap) normal_stop = slots ? slots : 1;
    }
    bool complete(unsigned actual_slots) const {
        if(!known || !valid || actual_slots>reward_cap)return false;
        if(!comparisons)return first_slots>=reward_cap && first_slots!=UINT32_MAX && actual_slots==reward_cap;
        const unsigned expected=last_slots+(last_roll<threshold?1:0);
        return actual_slots==(expected?expected:1) && (last_roll>=threshold || actual_slots==reward_cap);
    }
    uint32_t mask(unsigned actual_slots) const {
        if (!known || !valid || actual_slots > reward_cap || normal_stop >= actual_slots) return 0;
        return ((1u << actual_slots) - 1u) & ~((1u << normal_stop) - 1u);
    }
};
struct Reward { uint16_t item, amount; };
static_assert(sizeof(Reward) == 4);
// Native collection (main+0x388EE8) may reduce quantity or clear both fields.
// A refresh is checked by INDEX, never by searching for an identical item ID.
inline bool compatible_refresh(Reward original, Reward current) {
    return (!current.item && !current.amount) ||
        (original.item && current.item==original.item && current.amount &&
         current.amount<=original.amount);
}
struct Provenance {
    uint32_t epoch = 0, array = 0, count = 0, mask = 0;
    Reward items[reward_cap]{};
    bool matches(uint32_t generation, uint32_t address, unsigned index, Reward current) const {
        return epoch == generation && array == address && count <= reward_cap && index < count && (mask & (1u << index)) &&
               current.item && current.item == items[index].item && current.amount &&
               current.amount <= items[index].amount;
    }
};
}
