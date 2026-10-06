#include "attribution.h"
#include <assert.h>
#include <stdio.h>
#include <initializer_list>
using namespace pdb;
int main(){
    unsigned checks=0;
    for(unsigned tier:{8u,16u,22u,25u,28u,31u})for(unsigned slots=0;slots<8;++slots)for(unsigned roll=0;roll<32;++roll){
        Attribution a;a.begin(tier);a.compare(slots,roll);
        const unsigned actual=tier>roll?slots+1:slots;
        assert(a.mask(actual)==(slots && tier>22 && roll>=22 && roll<tier ? 1u<<slots : 0u));++checks;
    }
    for(unsigned tier:{25u,28u,31u}){
        Attribution a;a.begin(tier);
        a.compare(2,0);a.compare(3,22);a.compare(4,0);a.compare(5,0);a.compare(6,0);a.compare(7,tier-1);
        assert(a.mask(8)==0xf8);++checks;
        a.compare(8,0);assert(!a.mask(8));++checks;
    }
    Attribution absent;assert(!absent.mask(8));absent.begin(24);absent.compare(2,22);assert(!absent.mask(8));++checks;
    Attribution minimum;minimum.begin(31);minimum.compare(0,22);minimum.compare(1,0);minimum.compare(2,0);
    assert(minimum.mask(3)==6);++checks; // Native return clamps a zero-slot stop to one.
    Provenance p{};p.epoch=10;p.array=0x1000;p.count=8;p.mask=0xc0;p.items[6]={123,2};p.items[7]={123,2};
    assert(p.matches(10,0x1000,6,{123,2})&&p.matches(10,0x1000,7,{123,1}));++checks;
    assert(!p.matches(10,0x1000,5,{123,2})&&!p.matches(11,0x1000,7,{123,2})&&!p.matches(10,0x2000,7,{123,2}));++checks;
    assert(!p.matches(10,0x1000,7,{0,0})&&!p.matches(10,0x1000,7,{124,2})&&!p.matches(10,0x1000,7,{123,3}));++checks;
    printf("PASS: %u attribution boundary and provenance checks\n",checks);
}
