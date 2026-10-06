#include "hooks.h"
#include <map>
#include <assert.h>
#include <stdio.h>
using namespace pdb;
struct Fake {
    std::map<uint32_t,uint32_t> memory;
    unsigned writes=0,flushes=0,prepares=0,creates=0,closes=0;
    unsigned fail_write=0,fail_flush=0;
    bool poststore=false,external=false,rollback_fail=false,allocate=true,prepared=true;
    bool owned=false,bad_mapping=false,fail_close=false;uint64_t title=program_id;
    bool program(uint64_t& id){id=title;return true;}
    bool executable(uint32_t a,unsigned n){return !bad_mapping && (a>=0x800000 || (memory.count(a)&&memory.count(a+n-4)));}
    bool read(uint32_t a,uint32_t& out){if(!memory.count(a))return false;out=memory[a];return true;}
    bool write(uint32_t a,uint32_t expected,uint32_t value,bool& stored){
        ++writes;stored=false;
        if(rollback_fail && writes>2)return false;
        if(writes==fail_write && !poststore)return false;
        if(memory[a]!=expected)return false;
        memory[a]=value;stored=true;return writes!=fail_write;
    }
    uint32_t sync(uint32_t a,unsigned){++flushes;
        if(external&&flushes==1)memory[a]=0xe1a00000;
        return flushes==fail_flush?99:0;
    }
    bool create(unsigned n){assert(n==4096);++creates;owned=allocate;return allocate;}
    bool close(){++closes;if(fail_close)return false;owned=false;return true;}
    bool owns_arena()const{return owned;}
    uint32_t rx_base()const{return 0x900000;}
    bool prepare(unsigned off,uint32_t,uint32_t,uint32_t){assert(off%32==0);++prepares;return prepared;}
    bool make_executable(){return prepared;}
};
static constexpr Hook hs[2]={
 {0x10c,0x100,0x800000,{1,2,3,4,5,6,7,8},true},
 {0x20c,0x200,0x800100,{9,10,11,12,13,14,15,16},true}};
Fake fresh(){Fake f;for(auto& h:hs)for(unsigned j=0;j<8;++j)f.memory[0x100000+h.window+4*j]=h.words[j];return f;}
int main(){unsigned checks=0;
 {auto f=fresh();Hooks<Fake> t(f);assert(t.install(0x100000,hs,2).state==State::Applied);
  assert(f.creates==1&&f.prepares==2&&f.flushes==2&&t.original(0)==0x900000);
  const auto n=f.writes;assert(t.install(0x100000,hs,2).state==State::Applied&&f.writes==n);++checks;}
 for(unsigned fail=1;fail<=4;++fail)for(bool after:{false,true}){
  auto f=fresh();const auto before=f.memory;f.fail_write=fail;f.poststore=after;Hooks<Fake> t(f);
  assert(t.install(0x100000,hs,2).state!=State::Applied&&f.memory==before&&!f.owned);++checks;}
 for(unsigned fail=1;fail<=2;++fail){auto f=fresh();const auto before=f.memory;f.fail_flush=fail;Hooks<Fake> t(f);
  assert(t.install(0x100000,hs,2).state==State::RolledBack&&f.memory==before&&!f.owned);++checks;}
 {auto f=fresh();f.fail_flush=1;f.external=true;Hooks<Fake> t(f);
  assert(t.install(0x100000,hs,2).state==State::Unsafe&&f.owned&&f.memory[0x10010c]==0xe1a00000);++checks;}
 {auto f=fresh();f.fail_flush=1;f.rollback_fail=true;Hooks<Fake> t(f);
  assert(t.install(0x100000,hs,2).state==State::Unsafe&&f.owned);++checks;}
 for(unsigned i=0;i<2;++i)for(unsigned j=0;j<8;++j){auto f=fresh();f.memory[0x100000+hs[i].window+4*j]^=1;Hooks<Fake> t(f);
  assert(t.install(0x100000,hs,2).state==State::Rejected&&!f.writes&&!f.creates);++checks;}
 for(unsigned which=0;which<3;++which){auto f=fresh();if(which==0)f.title=0;if(which==1)f.allocate=false;if(which==2)f.prepared=false;Hooks<Fake> t(f);
  assert(t.install(0x100000,hs,2).state==State::Rejected&&!f.writes&&!f.owned);++checks;}
 for(unsigned which=0;which<7;++which){auto f=fresh();Hook wrong[2]={hs[0],hs[1]};uint32_t base=0x100000;
  if(which==0)base=0xfffffffcu;
  if(which==1)wrong[0].site|=1;
  if(which==2)wrong[0].window+=16;
  if(which==3)wrong[0].detour=0;
  if(which==4)wrong[0].detour=base+wrong[0].site;
  if(which==5)wrong[1].site=wrong[0].site;
  if(which==6)f.bad_mapping=true;
  Hooks<Fake> t(f);assert(t.install(base,wrong,2).state==State::Rejected&&!f.writes&&!f.creates);++checks;}
 {auto f=fresh();f.prepared=false;f.fail_close=true;Hooks<Fake> t(f);
  assert(t.install(0x100000,hs,2).state==State::Unsafe&&f.owned&&!f.writes);++checks;}
 {auto f=fresh();Hooks<Fake> t(f);assert(t.install(0x100000,hs,2).state==State::Applied);
  f.memory[0x10010c]=0xdeadbeef;const auto writes=f.writes,creates=f.creates;
  const auto r=t.install(0x100000,hs,2);assert(r.state==State::Unsafe&&r.failure==Failure::Changed&&r.unsafe&&
   f.writes==writes&&f.creates==creates&&f.memory[0x10010c]==0xdeadbeef);++checks;}
 printf("PASS: %u guarded hook publication/ownership rollback checks\n",checks);
}
