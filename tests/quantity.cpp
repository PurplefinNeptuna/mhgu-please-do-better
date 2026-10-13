#include "quantity.h"
#include "mode.h"
#include <cassert>
#include <cstdio>
using namespace pdb;
int main() {
    Reward items[48]{};
    for(unsigned multiplier=1;multiplier<=5;++multiplier) {
        assert(quantity_preflight(items,48,multiplier)==QuantityFault::None);
        for(unsigned i=0;i<48;++i)items[i]={uint16_t(10+i%3),uint16_t(i+1)};
        assert(quantity_preflight(items,48,multiplier)==QuantityFault::None);
        items[47].amount=uint16_t(32767/multiplier);
        assert(quantity_preflight(items,48,multiplier)==QuantityFault::None);
        ++items[47].amount;assert(quantity_preflight(items,48,multiplier)==QuantityFault::Overflow);
        items[47]={0,1};assert(quantity_preflight(items,48,multiplier)==QuantityFault::Record);
        items[47]={1,0};assert(quantity_preflight(items,48,multiplier)==QuantityFault::Record);
        assert(quantity_preflight(items,49,multiplier)==QuantityFault::Memory);
        items[47]={1,1};
    }
    assert(quantity_preflight(items,48,0)==QuantityFault::Multiplier);
    assert(quantity_preflight(items,48,6)==QuantityFault::Multiplier);
    Mode mode;
    for(unsigned bits=0;bits<10;++bits) {
        mode.set(Preferences{bool(bits&1),uint8_t(bits/2+1)});
        auto p=mode.preferences();assert(p.force==bool(bits&1)&&p.multiplier==bits/2+1);
        mode.set(!p.force);assert(mode.preferences().multiplier==p.multiplier);
    }
    mode.set(Preferences{true,5});mode.set(Preferences{false,0});
    assert(mode.preferences().force&&mode.preferences().multiplier==5);
    std::puts("PASS: signed quantity bounds, empty/malformed records, capacity and independent atomic modes");
}
