#include "quantity.h"
#include "mode.h"
#include <cassert>
#include <cstdio>
using namespace pdb;
int main() {
    Reward items[48]{};
    assert(quantity_preflight(items,48)==QuantityFault::None);
    for(unsigned i=0;i<48;++i)items[i]={uint16_t(10+i%3),uint16_t(i+1)};
    assert(quantity_preflight(items,48)==QuantityFault::None);
    items[47].amount=16383;assert(quantity_preflight(items,48)==QuantityFault::None);
    items[47].amount=16384;assert(quantity_preflight(items,48)==QuantityFault::Overflow);
    items[47]={0,1};assert(quantity_preflight(items,48)==QuantityFault::Record);
    items[47]={1,0};assert(quantity_preflight(items,48)==QuantityFault::Record);
    assert(quantity_preflight(items,49)==QuantityFault::Memory);
    Mode mode;
    for(unsigned bits=0;bits<4;++bits) {
        mode.set(Preferences{bool(bits&1),bool(bits&2)});
        auto p=mode.preferences();assert(p.force==bool(bits&1)&&p.double_quantity==bool(bits&2));
        mode.set(!p.force);assert(mode.preferences().double_quantity==p.double_quantity);
    }
    std::puts("PASS: signed quantity bounds, empty/malformed records, capacity and independent atomic modes");
}
