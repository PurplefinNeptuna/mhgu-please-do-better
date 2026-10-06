#pragma once
#include <stdint.h>

namespace pdb {
constexpr unsigned normal_luck = 22, reward_cap = 8;
// Counterfactual SLOT count only, using the already-observed rolls. This does
// not predict the item RNG sequence of a second, unmodified game execution.
struct Attribution {
    uint32_t threshold = 0, normal_stop = reward_cap;
    bool known = false, valid = true;
    void begin(unsigned tier) {
        threshold = tier; normal_stop = reward_cap; known = true;
        valid = tier == 8 || tier == 16 || tier == 22 || tier == 25 || tier == 28 || tier == 31;
    }
    void compare(unsigned slots, unsigned roll) {
        if (!known || slots >= reward_cap || roll > 31) { valid = false; return; }
        if (valid && threshold > normal_luck && roll >= normal_luck && roll < threshold &&
            normal_stop == reward_cap) normal_stop = slots ? slots : 1;
    }
    uint32_t mask(unsigned actual_slots) const {
        if (!known || !valid || actual_slots > reward_cap || normal_stop >= actual_slots) return 0;
        return ((1u << actual_slots) - 1u) & ~((1u << normal_stop) - 1u);
    }
};
struct Reward { uint16_t item, amount; };
static_assert(sizeof(Reward) == 4);
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
