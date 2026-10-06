#include "runtime.h"
#include "mode.h"
#include "attribution.h"
#include "gateway.h"
#include "signatures.h"
#include "native_platform.h"
#include "sdk_tls.h"
#include "mailbox.h"
#include <switch.h>
#include <forge/log.h>
extern "C" {
#include <forge/mem.h>
Result pdb_svc_query(MemoryInfo*,uint32_t*,uint64_t);
}
#include <stdarg.h>
#define CIMGUI_DEFINE_ENUMS_AND_STRUCTS
#include <cimgui.h>
namespace pdb {
static NativePlatform platform;
static Hooks<NativePlatform> conditional(platform), visual(platform);
static Mode mode;
static uint32_t base, initialized, pair_ready, capture_ready, drops;
// Execution evidence is distinct from successful instruction publication.
// Only scalar atomics cross from gameplay producers to the ImGui reader.
static uint32_t gateway_hits[21]{}, forced_checks[2]{}, natural_checks[2]{};
static uint32_t update_hits, completed_batches, completed_generations, published_rewards;
static uint32_t cleared_rewards, last_ui_state, last_comparison_tier;
static void count(uint32_t& value) { __atomic_fetch_add(&value,1,__ATOMIC_RELAXED); }
static uint32_t seen(const uint32_t& value) { return __atomic_load_n(&value,__ATOMIC_RELAXED); }
static TlsSlot tls=-1;
static uint32_t claimed[8]{};
struct Record { uint32_t ui=0, epoch=0, tier=0, kind=0; Provenance rewards{}; };
struct Scope {
    uint32_t kind=0, caller=0, sp=0, subject=0, array=0, start=0, count=0;
    bool force=false;
    // Unknown scopes are zero-initialized BSS. begin() supplies the threshold
    // and stop sentinel only when a real comparison is observed.
    Attribution attribution{0,0,false,false};
    uint32_t epoch=0, ui=0;
    Record pending[8]{};
    unsigned pending_count=0;
};
struct Context {
    unsigned depth=0; bool quarantine=false;
    bool tls_lost=false;
    uint32_t cookie=0,serial=0,last_ui=0;
    Scope scopes[4]{};
    Mailbox<Record,16> records;
};
static Context contexts[8];
static bool readable(uint32_t a,unsigned n) {
    MemoryInfo m{};uint32_t page=0;
    return a && uint64_t(a)+n<=0x100000000ull && !pdb_svc_query(&m,&page,a) &&
        (m.perm&1) && m.addr<=a && m.addr<=0x100000000ull &&
        m.size<=0x100000000ull-m.addr && uint64_t(a)+n<=m.addr+m.size;
}
static uint32_t word(uint32_t a) { return *reinterpret_cast<volatile const uint32_t*>(a); }
static bool field(uint32_t a,unsigned offset,unsigned n) {
    return uint64_t(a)+offset+n<=0x100000000ull && readable(a+offset,n);
}
static bool copy(uint32_t a,void* dest,unsigned n) {
    if (!readable(a,n))return false;
    auto* d=static_cast<unsigned char*>(dest);
    auto* s=reinterpret_cast<volatile const unsigned char*>(a);
    for(unsigned i=0;i<n;++i)d[i]=s[i];
    return true;
}
static void lost() { __atomic_fetch_add(&drops,1,__ATOMIC_RELAXED); }
static Context* context() {
    if(tls<0)return nullptr;
    const auto cookie=uint32_t(uintptr_t(pdb_current_thread()));
    if(!cookie) {lost();return nullptr;}
    void* p=nnosGetTlsValue(tls);
    for(unsigned i=0;i<8;++i)if(__atomic_load_n(&claimed[i],__ATOMIC_ACQUIRE)==2 && contexts[i].cookie==cookie) {
        auto& c=contexts[i];
        if(p!=&c) {
            c.quarantine=true;
            if(!c.tls_lost) { c.tls_lost=true;lost();Record r{};r.kind=4;r.ui=c.last_ui;c.records.publish(r); }
        } else c.tls_lost=false;
        // Do not overwrite an external TLS edit. Immutable native identity
        // retains the original caller/mode while attribution is quarantined.
        return &c;
    }
    if(p) {if(p!=reinterpret_cast<void*>(1))lost();return nullptr;}
    for(unsigned i=0;i<8;++i) {
        uint32_t expected=0;
        if(__atomic_compare_exchange_n(&claimed[i],&expected,1,true,__ATOMIC_ACQ_REL,__ATOMIC_RELAXED)) {
            contexts[i].cookie=cookie;
            __atomic_store_n(&claimed[i],2,__ATOMIC_RELEASE);
            p=&contexts[i];nnosSetTlsValue(tls,p);
            if(nnosGetTlsValue(tls)==p)return static_cast<Context*>(p);
            contexts[i].quarantine=contexts[i].tls_lost=true;
            lost();return &contexts[i];
        }
    }
    nnosSetTlsValue(tls,reinterpret_cast<void*>(1));lost();return nullptr;
}
static Scope* find(Context& c,unsigned kind) {
    for(unsigned i=c.depth;i;--i)if(c.scopes[i-1].kind==kind)return &c.scopes[i-1];
    return nullptr;
}
static bool force(Context* c) {
    if(!__atomic_load_n(&pair_ready,__ATOMIC_ACQUIRE) ||
       !__atomic_load_n(&capture_ready,__ATOMIC_ACQUIRE))return false;
    // A missing context cannot latch a batch. Fail natural rather than allowing
    // a UI change to alter an unidentified batch partway through generation.
    if(!c)return false;
    if(c->depth)return c->scopes[0].force;
    return mode.get();
}
// Conditional natural returns use separate fixed gateways. The original callee
// sees untouched argument/working registers and the original stack. Its output
// registers/flags are preserved; only the LR value created by BL is reconstructed.
extern "C" uint32_t pdb_gateway_dispatch(uint32_t kind,RawFrame* f) {
    if(kind<21)count(gateway_hits[kind]);
    if(kind==19 || kind==20) {
        const unsigned i=kind-19;
        f->r[5]=i?1:31;
        f->r[13]=base+site_offset(i)+4;
        return base+site_offset(i)+8;
    }
    if(kind<2) {
        Context* c=context();
        if(force(c)) { count(forced_checks[kind]);f->r[0]=1;f->r[5]=kind?1:31;return base+site_offset(kind)+8; }
        count(natural_checks[kind]);
        f->r[13]=uint32_t(uintptr_t(kind?pdb_gateway_20:pdb_gateway_19));
        return base+(kind?0x26fe08:0xe0da0);
    }
    if(kind<9) {
        __atomic_store_n(&last_comparison_tier,f->r[kind==2?5:6],__ATOMIC_RELAXED);
        Context* c=context();
        if(c && !c->quarantine) {
            Scope* s=find(*c,kind==2?9:10);
            if(s) {
                const unsigned threshold=f->r[kind==2?5:6];
                if(!s->attribution.known)s->attribution.begin(threshold);
                else if(s->attribution.threshold!=threshold)s->attribution.valid=false;
                s->attribution.compare(kind==2?f->r[4]:kind-1,f->r[0]&31);
            } else lost();
        }
        // Replay both displaced words. Carry/overflow are those of CMP, with Q
        // and GE inherited untouched. AND/MOV have no S bit.
        if(kind==2)f->r[0]&=31; else f->r[7]=kind-1;
        const uint32_t a=f->r[kind==2?5:6],b=f->r[0],result=a-b;
        const uint32_t nzcv=(result&0x80000000u)|(result==0?0x40000000u:0)|
            (a>=b?0x20000000u:0)|(((a^b)&(a^result)&0x80000000u)?0x10000000u:0);
        f->cpsr=(f->cpsr&0x0fffffffu)|nzcv;
        return base+hook(kind).site+8;
    }
    const auto original=visual.original(kind-2);
    Context* c=context();
    if(!c || !__atomic_load_n(&capture_ready,__ATOMIC_ACQUIRE))return original;
    if(c->depth==4) { c->quarantine=true;lost();return original; }
    const bool latched=force(c);
    auto& s=c->scopes[c->depth++];s={};s.kind=kind;s.caller=f->r[13];s.sp=f->caller_sp();s.force=latched;
    s.subject=f->r[0];
    if(kind==12) {
        s.epoch=++c->serial;s.ui=s.subject;
        c->last_ui=s.ui;
        Record r{};r.kind=1;r.ui=s.ui;r.epoch=s.epoch;c->records.publish(r);
    } else if(kind==10 || kind==13) {
        s.subject=f->r[kind==10?1:2];
        if(readable(s.subject,4))s.array=word(s.subject);
    } else if(kind==11) {
        if(readable(s.subject,4))s.array=word(s.subject);
        s.start=f->r[1];s.count=f->r[3];
        Scope* parent=find(*c,10);if(!parent)parent=find(*c,13);if(!parent)parent=find(*c,12);
        if(parent)s.attribution=parent->attribution;
    } else if(kind==14) {
        if(readable(f->r[1],8)) { s.array=word(f->r[1]);s.count=word(f->r[1]+4); }
        Scope* ui=find(*c,15);if(ui)s.ui=ui->subject;
    }
    f->r[13]=uint32_t(uintptr_t(pdb_gateway_after));
    return original;
}
extern "C" uint32_t pdb_gateway_leave(RawFrame* f) {
    Context* c=context();
    if(!c || !c->depth)__builtin_trap(); // Never invent a native return address.
    const Scope s=c->scopes[--c->depth];
    if(s.sp!=f->caller_sp())__builtin_trap();
    if(f->r[13]==uint32_t(uintptr_t(pdb_gateway_after)))f->r[13]=s.caller;
    if(c->quarantine) { if(!c->depth)c->quarantine=false;return s.caller; }
    if(s.kind==11)count(completed_generations);
    if(s.kind==9) {
        Scope* parent=find(*c,13);if(!parent)parent=find(*c,12);
        if(parent)parent->attribution=s.attribution;
    } else if(s.kind==11 && s.count<=8 && s.start==0 && s.array) {
        Scope* ui=find(*c,12);
        Record r{};r.epoch=ui?ui->epoch:0;r.ui=ui?ui->ui:0;r.tier=s.attribution.threshold;r.kind=2;
        r.rewards.epoch=r.epoch;r.rewards.array=s.array;r.rewards.count=s.count;
        r.rewards.mask=s.attribution.mask(s.count);
        if(ui && copy(s.array,r.rewards.items,s.count*4) && ui->pending_count<8) {
            // Exact traced native routes, keyed by native caller and slot offset.
            // No item-ID search, sorting guess or unverified copy is accepted.
            Scope* main=find(*c,13);Scope* secondary=find(*c,10);
            uint32_t target=0;
            if(ui && field(ui->subject,0x5c,16)) {
                if(main && (main->caller==base+0x3875bc || main->caller==base+0x3878e0))target=word(ui->subject+0x5c);
                else if(!main && !secondary && s.caller==base+0x387b00) {
                    const auto a=word(ui->subject+0x5c);if(a && uint64_t(a)+32<0x100000000ull)target=a+32;
                } else if(secondary && secondary->caller==base+0x388084) {
                    const auto a=word(ui->subject+0x64);if(a && uint64_t(a)+32<0x100000000ull)target=a+32;
                }
            }
            if(target) {r.rewards.array=target;ui->pending[ui->pending_count++]=r;}
            else if(r.rewards.mask)lost();
        } else lost();
    } else if(s.kind==12) {
        count(completed_batches);
        for(unsigned i=0;i<s.pending_count;++i) {
            Record r=s.pending[i];Reward check[8]{};
            if(copy(r.rewards.array,check,r.rewards.count*4)) {
                bool same=true;
                for(unsigned j=0;j<r.rewards.count;++j) same=same &&
                    check[j].item==r.rewards.items[j].item && check[j].amount==r.rewards.items[j].amount;
                if(same) {c->records.publish(r);count(published_rewards);}else lost();
            } else lost();
        }
    } else if(s.kind==14 && s.ui && s.array && field(s.subject,0x5c,4)) {
        // Native 0x623c08 copies source[i] to list.buffer[i], up to capacity.
        // The consumer follows that index mapping only after checking contents.
        Record r{};r.kind=5;r.ui=s.ui;r.epoch=s.array;
        r.rewards.array=s.subject+0x60;
        r.rewards.count=s.count<word(s.subject+0x5c)?s.count:word(s.subject+0x5c);
        if(r.rewards.count<=48 && uint64_t(s.subject)+0x60+r.rewards.count*4<=0x100000000ull &&
           readable(r.rewards.array,r.rewards.count*4))c->records.publish(r);else lost();
    } else if(s.kind==15) {
        if(field(s.subject,0x3c,4))__atomic_store_n(&last_ui_state,word(s.subject+0x3c),__ATOMIC_RELAXED);
        if(!field(s.subject,0x3c,4) || word(s.subject+0x3c)<2 || word(s.subject+0x3c)>5) {
            count(cleared_rewards);
            Record r{};r.kind=4;r.ui=s.subject;c->records.publish(r);
        }
    } else if(s.kind==16) {
        Record r{};r.kind=3;r.ui=s.subject;c->records.publish(r);
    }
    return s.caller;
}
void request_force(bool value) { mode.set(value); }
bool requested_force() { return mode.get(); }
bool forcing_available() { return __atomic_load_n(&pair_ready,__ATOMIC_ACQUIRE) &&
                                 __atomic_load_n(&capture_ready,__ATOMIC_ACQUIRE); }
void install() {
    if(initialized) {
        // Recheck owned signatures, without republishing or allocating. A
        // conflict cancels effective forcing and further attribution.
        const auto r=conditional.install(base,nullptr,0);
        const auto v=visual.report().state==State::Fresh?visual.report():visual.install(base,nullptr,0);
        if(r.state!=State::Applied || v.state!=State::Applied) {
            __atomic_store_n(&pair_ready,0,__ATOMIC_RELEASE);
            __atomic_store_n(&capture_ready,0,__ATOMIC_RELEASE);
        }
        return;
    }
    initialized=1;base=forge_mem_getMainTextAddr();
    Hook pair[2]={hook(0),hook(1)};
    const auto r=conditional.install(base,pair,2);
    forge_log_info("[please-do-better] r3 conditional state=%u owned=%llx unsafe=%llx",unsigned(r.state),r.owned,r.unsafe);
    if(r.state!=State::Applied)return;
    __atomic_store_n(&pair_ready,1,__ATOMIC_RELEASE);
    if(nnosAllocateTlsSlot(&tls,nullptr) || tls<0) {tls=-1;lost();return;}
    Hook taps[15];for(unsigned i=0;i<15;++i)taps[i]=hook(i+2);
    const auto v=visual.install(base,taps,15);
    if(v.state==State::Applied)__atomic_store_n(&capture_ready,1,__ATOMIC_RELEASE);
    forge_log_info("[please-do-better] r3 observation state=%u owned=%llx unsafe=%llx",unsigned(v.state),v.owned,v.unsafe);
}
static Record observed[8][8]{};
static Record displayed[8][8]{};
static uint32_t epochs[8]{}, owners[8]{}, latest_tier=0, bonus_count=0;
void update() {
    count(update_hits);
    uint32_t tier=0,bonuses=0;
    for(unsigned thread=0;thread<8;++thread) {
        auto& c=contexts[thread];Record r{};
        const uint32_t lost_before=c.records.overwritten;
        for(unsigned budget=0;budget<16 && c.records.read(r);++budget) {
            if(c.records.overwritten!=lost_before)break;
            if(r.kind==1 || ((r.kind==3 || r.kind==4) && r.ui==owners[thread])) {
                for(auto& record:observed[thread])record={};
                for(auto& record:displayed[thread])record={};
                owners[thread]=r.kind==1?r.ui:0;epochs[thread]=r.epoch;
            } else if(r.kind==2 && r.ui==owners[thread] && r.epoch==epochs[thread]) {
                bool stored=false;
                for(auto& record:observed[thread])if(!record.kind) {record=r;stored=true;break;}
                if(!stored)lost();
            } else if(r.kind==2) {
                lost(); // Nested/stale batches are never silently adopted.
            } else if(r.kind==5 && r.ui==owners[thread]) {
                for(auto& record:displayed[thread])record={};
                for(unsigned i=0;i<8;++i) {
                    const auto& source=observed[thread][i];
                    if(!source.kind || source.rewards.array<r.epoch)continue;
                    const uint32_t offset=source.rewards.array-r.epoch;
                    if((offset&3) || uint64_t(offset)+source.rewards.count*4>uint64_t(r.rewards.count)*4 ||
                       uint64_t(r.rewards.array)+offset+source.rewards.count*4>0x100000000ull)continue;
                    Record target=source;target.rewards.array=r.rewards.array+offset;
                    Reward contents[8]{};bool same=copy(target.rewards.array,contents,target.rewards.count*4);
                    for(unsigned j=0;j<target.rewards.count;++j)same=same &&
                        contents[j].item==target.rewards.items[j].item && contents[j].amount==target.rewards.items[j].amount;
                    if(same)displayed[thread][i]=target;else lost();
                }
            }
        }
        if(c.records.overwritten!=lost_before) {
            owners[thread]=0;
            for(auto& record:observed[thread])record={};
            for(auto& record:displayed[thread])record={};
            lost();
        }
        for(const auto& record:observed[thread])if(record.kind) {
            tier=record.tier;
            for(unsigned j=0;j<record.rewards.count;++j) {
                if(!(record.rewards.mask&(1u<<j)))continue;
                Reward current{};
                if(copy(record.rewards.array+4*j,&current,4) &&
                    record.rewards.matches(epochs[thread],record.rewards.array,j,current))++bonuses;
            }
        }
    }
    __atomic_store_n(&latest_tier,tier,__ATOMIC_RELEASE);
    __atomic_store_n(&bonus_count,bonuses,__ATOMIC_RELEASE);
}
void diagnostics() {
    const auto r=conditional.report(),v=visual.report();
    const auto tier=__atomic_load_n(&latest_tier,__ATOMIC_ACQUIRE);
    const char* name=tier==25?"Good Luck":tier==28?"Great Luck":tier==31?"Miraculous Luck":
                     tier==22?"Normal":tier==16?"Bad Luck":tier==8?"Horrible Luck":"Unavailable";
    igText("Observed tier: %s (%u); verified extra slots: %u",name,tier,__atomic_load_n(&bonus_count,__ATOMIC_ACQUIRE));
    igTextUnformatted("Highlights unavailable: final display transform verification pending.",nullptr);
    if(!igTreeNode_Str("Diagnostics###pdb_diagnostics"))return;
    igTextUnformatted("R3 execution diagnostics",nullptr);
    const char* states[]={"not installed","applied; flush/readback checked","rejected","rolled back","UNSAFE; residual/changed bytes"};
    igText("Conditional: %s; failure %u, site %u",states[unsigned(r.state)],unsigned(r.failure),r.site);
    igText("Observation: %s; failure %u, site %u",states[unsigned(v.state)],unsigned(v.failure),v.site);
    igText("Owned words: %llx / %llx; unsafe: %llx / %llx",r.owned,v.owned,r.unsafe,v.unsafe);
    igText("Dropped/incomplete observations: %u",__atomic_load_n(&drops,__ATOMIC_RELAXED));
    igText("Executed checks: reward %u / secondary %u",seen(gateway_hits[0]),seen(gateway_hits[1]));
    igText("Forced checks: %u / %u; natural checks: %u / %u",seen(forced_checks[0]),seen(forced_checks[1]),seen(natural_checks[0]),seen(natural_checks[1]));
    igText("Main/secondary counts: %u / %u; comparison taps: %u",seen(gateway_hits[9]),seen(gateway_hits[10]),
           seen(gateway_hits[2])+seen(gateway_hits[3])+seen(gateway_hits[4])+seen(gateway_hits[5])+seen(gateway_hits[6])+seen(gateway_hits[7])+seen(gateway_hits[8]));
    igText("Last comparison threshold: %u (22 normal, 31 Miraculous)",seen(last_comparison_tier));
    igText("Reward builds: entered %u / returned %u; generation returns: %u",seen(gateway_hits[12]),seen(completed_batches),seen(completed_generations));
    igText("Published reward records: %u; clearing events: %u",seen(published_rewards),seen(cleared_rewards));
    igText("UI update hits: %u; last state: %u; Forge updates: %u",seen(gateway_hits[15]),seen(last_ui_state),seen(update_hits));
    igTextUnformatted("Counters are cumulative for this process. Applied bytes alone do not prove gateway execution.",nullptr);
    igTextUnformatted("Successful cache calls do not verify emulator translation freshness.",nullptr);
    igTreePop();
}
void render() {
    // Research gate is closed: world quads alone do not establish the native
    // shader/viewport transform or every list-to-node route. Publish no border
    // from guessed coordinates. See RESEARCH.md for the remaining bindings.
}
}
