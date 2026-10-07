#include "runtime.h"
#include "mode.h"
#include "attribution.h"
#include "gateway.h"
#include "signatures.h"
#include "native_platform.h"
#include "sdk_tls.h"
#include "mailbox.h"
#include "highlight_gate.h"
#include "highlight.h"
#include <forge/singleton.h>
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
static Hooks<NativePlatform> conditional(platform), visual(platform), highlight(platform);
static Mode mode;
static uint32_t base, initialized, pair_ready, capture_ready, drops;
static uint32_t expected_refreshes, remapped_arrays, mapping_faults;
struct CopyFault { uint32_t index,expected,actual; };
static Snapshot<CopyFault> mapping_detail;
// Execution evidence is distinct from successful instruction publication.
// Only scalar atomics cross from gameplay producers to the ImGui reader.
static uint32_t gateway_hits[26]{}, forced_checks[2]{}, natural_checks[2]{};
static uint32_t update_hits, completed_batches, completed_generations, published_rewards;
static uint32_t cleared_rewards, last_ui_state, last_comparison_tier;
static void count(uint32_t& value) { __atomic_fetch_add(&value,1,__ATOMIC_RELAXED); }
static uint32_t seen(const uint32_t& value) { return __atomic_load_n(&value,__ATOMIC_RELAXED); }
static TlsSlot tls=-1;
static uint32_t claimed[8]{};
struct Record { uint32_t ui=0, epoch=0, tier=0, kind=0, generated=0, coverage=0; Provenance rewards{}; };
struct CountSnapshot {
    Attribution attribution{0,0,false,false};
    uint32_t slots=0;
    bool ready=false;
};
struct Scope {
    uint32_t kind=0, caller=0, sp=0, subject=0, array=0, start=0, count=0;
    bool force=false;
    // Unknown scopes are zero-initialized BSS. begin() supplies the threshold
    // and stop sentinel only when a real comparison is observed.
    Attribution attribution{0,0,false,false};
    uint32_t epoch=0, ui=0;
    Record pending[8]{};
    unsigned pending_count=0;
    CountSnapshot counts[3]{};
    uint32_t counted=0, copied=0;
    bool incomplete=false;
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
static Snapshot<Binding> bindings[64];
static Snapshot<Geometry> geometries[64];
static Snapshot<Presentation> presentation;
static uint32_t binding_count, highlight_ready, highlighted_count, render_faults, unsupported_draws;
static uint32_t live_fence=1, draw_cycle=1, present_pending, native_render;
static uint32_t frame_overflow[2]{},geometry_claims[64]{};
static void mark_overflow(unsigned frame,uint32_t serial) {
    const uint32_t value=serial+1;uint32_t prior=seen(frame_overflow[frame]);
    // Out-of-order older producers cannot clear a newer frame's failure tag.
    while(!prior || (uint32_t(value-prior)>0 && uint32_t(value-prior)<0x80000000u))
        if(__atomic_compare_exchange_n(&frame_overflow[frame],&prior,value,false,__ATOMIC_SEQ_CST,__ATOMIC_SEQ_CST))break;
}
static void invalidate_highlights() { __atomic_add_fetch(&live_fence,1,__ATOMIC_SEQ_CST); }
static uint32_t indirect(uint32_t address,unsigned offset) {
    if(!field(address,offset,4))return 0;
    const uint32_t p=word(address+offset);
    return readable(p,4)?word(p):0;
}
static uint32_t gui_node(uint32_t holder,unsigned root_index,unsigned node_index) {
    if(root_index>=128 || node_index>=128 || !field(holder,0x298,4))return 0;
    const uint32_t split=word(holder+0x298);
    if(split>128)return 0;
    unsigned adjusted=root_index;
    const unsigned offset=root_index<split?0xf8:0x294;
    if(root_index>=split)adjusted-=split;
    if(!field(holder,offset,4))return 0;
    uint32_t table=word(holder+offset);
    if(!field(table,adjusted*4,4))return 0;
    const uint32_t root=word(table+adjusted*4);
    if(!field(root,0xd8,4))return 0;
    table=word(root+0xd8);
    if(!field(table,node_index*4,4))return 0;
    return word(table+node_index*4);
}
static bool texture_node(uint32_t node) {
    if(!readable(node,0x130))return false;
    const uint32_t vft=word(node);
    // Festa's subclass inherits the texture layout and draw/vertex methods.
    // Both exact vtables are verified against the pinned original executable.
    return vft==base+0x178fcc8 || vft==base+0x176c7c4;
}
static bool shader_2d(uint32_t renderer) {
    if(!field(renderer,0x1d8,4) || word(renderer+0x1d8)!=0xd7376b18 || !field(renderer,0x1a4,4))return false;
    const uint32_t packet=word(renderer+0x1a4);
    if(!field(packet,8,4))return false;
    const uint32_t program=word(packet+8);
    if(!readable(program,72))return false;
    const uint32_t uniforms=word(program+0x40),n=word(program+0x44);
    if(n<3 || n>9 || !readable(uniforms,n*4))return false;
    // Six exact uniform sequences cover the twelve verified 2D programs.
    // The 3D blend variant shares the first three IDs, so prefix matching alone
    // would incorrectly adopt its perspective transform.
    static const uint32_t patterns[6][8]={
        {0x2d7,0x2d6,0x16f,0x2db,0x2d9,0x2de,0x3ca},
        {0x2d7,0x2d6,0x16f,0x2db,0x2de,0x3ca},
        {0x2d7,0x2d6,0x16f,0x2db,0x2d8,0x2d9,0x2de,0x3ca},
        {0x2d7,0x2d6,0x16f},
        {0x2d7,0x2d6,0x16f,0x2db,0x2d8,0x2de,0x3ca},
        {0x2d7,0x2d6,0x16f,0x2d9}};
    static const unsigned lengths[6]={7,6,8,3,7,4};
    for(unsigned j=0;j<6;++j)if(n==lengths[j]) {
        bool equal=true;for(unsigned i=0;i<n;++i)equal=equal && word(uniforms+i*4)==patterns[j][i];
        if(equal)return true;
    }
    return false;
}
static void capture_geometry(RawFrame& f) {
    if(!seen(highlight_ready) || !seen(binding_count))return;
    const uint32_t node=f.r[5],ctx=f.r[4];
    if(uint64_t(node)+0xcc>UINT32_MAX || f.r[6]!=node+0xcc)return;
    Binding b{};unsigned slot=64;
    const uint32_t fence=seen(live_fence),cycle=seen(draw_cycle);
    for(unsigned i=0;i<seen(binding_count) && i<64;++i)
        if(bindings[i].read(b) && b.node==node && b.fence==fence) {slot=i;break;}
    if(slot==64)return;
    // Native draw proves the node is alive. Its exact list identity is retained
    // until a UI exit/destructor invalidates the fence BEFORE native freeing.
    if(!field(b.list,0x4c,0x14) || word(b.list+0x4c)!=b.group || b.index>=word(b.list+0x5c) ||
       !field(b.list,0x60+b.index*4,4))return;
    Reward current{};
    if(!copy(b.list+0x60+b.index*4,&current,4) || !current.item || !current.amount ||
       !compatible_refresh(b.item,current))return;
    if(!texture_node(node) || word(node+0x50)!=b.id ||
       !field(ctx,4,4))return;
    if(!(word(node+0xc0)&0x800000))return;
    if(word(node+0x108)&0x30) {count(unsupported_draws);return;}
    const uint32_t renderer=word(ctx+4),sr=seen(native_render);
    if(!field(renderer,0x18bc,4) || !field(sr,0x389cc,4))return;
    if(!field(sr,0x1f,1) || !field(sr,0x33f50,4) ||
       *reinterpret_cast<volatile const uint8_t*>(sr+0x1f)>1 || word(sr+0x33f4c)>1)return;
    if(!field(renderer,0x138,4) || *reinterpret_cast<volatile const uint8_t*>(renderer+0x134)!=24 ||
       word(renderer+0x138)!=word(node+0xbc))return;
    // The native draw-packet helper returns without enqueueing when these
    // renderer flags suppress submission, even though vertex construction
    // itself returns success. Such frames must receive no marker.
    const uint32_t draw_flags=word(renderer+0x54);
    if(!(draw_flags&0x100) && (draw_flags&0x50))return;
    const uint32_t target_packet=word(renderer+0x1ac);
    if(!readable(target_packet,0x5c) || word(target_packet)!=indirect(word(sr+0x389c0),0x204) ||
       (word(target_packet+0x14)&0x200) || !shader_2d(renderer)) {count(unsupported_draws);return;}
    int32_t viewport[4]{},clip[4]{};
    if(!copy(target_packet+0x18,viewport,16) || !copy(renderer+0xe4,clip,16) ||
       viewport[0] || viewport[1] || viewport[2]<=0 || viewport[3]<=0 ||
       viewport[2]>16384 || viewport[3]>16384)return;
    // Full viewport is the same NVN viewport as Forge's selected texture.
    // Offset/half-size targets are deliberately unsupported.
    const uint32_t gui=field(base,0x212668c,4)?word(base+0x212668c):0;
    if(!field(gui,0xb0,4))return;
    const uint32_t start=word(gui+0xb0),offset=word(node+0xbc);
    if(uint64_t(start)+offset+96>0x100000000ull)return;
    float vertices[24]{},model[16]{},global[4]{};
    if(!copy(start+offset,vertices,96) || !copy(word(renderer+0x18bc),model,64) ||
       !field(renderer,0x18b4,4) || !copy(word(renderer+0x18b4),global,16))return;
    Geometry g{};g.binding=b;g.cycle=cycle;g.frame=word(sr+0x33f4c);g.owner=sr+0x34100;g.serial=word(sr+0x33f50);
    g.width=float(viewport[2]);g.height=float(viewport[3]);
    if(!screen_quad(vertices,model,global,g.width,g.height,g.points))return;
    for(unsigned i=0;i<4;++i)g.clip[i]=float(clip[i]);
    if(clip[2]<=clip[0] || clip[3]<=clip[1])return;
    if(seen(live_fence)!=fence || seen(draw_cycle)!=cycle)return;
    // Retain current AND previous producer frames for the native ping-pong
    // executor. Sixty-four samples total; competing producers never wait.
    // Prefer updating the same node/frame, then reuse only older samples.
    for(unsigned pass=0;pass<2;++pass)for(unsigned i=0;i<64;++i) {
        uint32_t expected=0;
        if(!__atomic_compare_exchange_n(&geometry_claims[i],&expected,1,false,__ATOMIC_ACQUIRE,__ATOMIC_RELAXED))continue;
        Geometry old{};const bool exists=geometries[i].read(old);
        const bool same=exists && old.serial==g.serial && old.owner==g.owner &&
            old.binding.node==g.binding.node && old.binding.fence==g.binding.fence;
        const bool reusable=!exists || old.binding.fence!=fence || old.owner!=g.owner ||
            (uint32_t(g.serial-old.serial)>1 && uint32_t(g.serial-old.serial)<0x80000000u);
        if((pass==0 && same) || (pass==1 && reusable)) {
            const bool published=geometries[i].publish(g);
            __atomic_store_n(&geometry_claims[i],0,__ATOMIC_RELEASE);
            if(!published) {count(render_faults);mark_overflow(g.frame,g.serial);}
            return;
        }
        __atomic_store_n(&geometry_claims[i],0,__ATOMIC_RELEASE);
    }
    count(render_faults);mark_overflow(g.frame,g.serial);
}
static void capture_present(RawFrame& f) {
    if(!seen(highlight_ready))return;
    const uint32_t sr=seen(native_render),owner=sr+0x34100;
    if(!sr || !field(owner,0x46f8,8) || !field(sr,0x33f4c,8) || !field(sr,0x1f,1) ||
       f.r[1]!=owner+0x4740 || f.r[12]!=word(owner+0x46f8) || f.r[2]!=word(owner+0x46fc))return;
    const uint32_t parallel=*reinterpret_cast<volatile const uint8_t*>(sr+0x1f),frame=word(sr+0x33f4c);
    if(parallel>1 || frame>1)return;
    // beginFrame latches parallel mode and increments the producer serial;
    // executeFrame uses producer index XOR parallel, i.e. one frame behind.
    Presentation p{seen(draw_cycle),frame^parallel,owner,f.r[12],f.r[1],f.r[2],word(sr+0x33f50)-parallel};
    if(presentation.publish(p))__atomic_store_n(&present_pending,1,__ATOMIC_RELEASE);
    else {count(render_faults);mark_overflow(p.frame,p.serial);}
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
            if(!c.tls_lost) { c.tls_lost=true;lost();Record r{};r.kind=4;r.ui=c.last_ui;r.coverage=1;c.records.publish(r); }
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
static void comparison_flags(RawFrame& f,uint32_t a,uint32_t b) {
    const uint32_t result=a-b;
    const uint32_t nzcv=(result&0x80000000u)|(result==0?0x40000000u:0)|
        (a>=b?0x20000000u:0)|(((a^b)&(a^result)&0x80000000u)?0x10000000u:0);
    f.cpsr=(f.cpsr&0x0fffffffu)|nzcv;
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
    if(kind==26) {
        capture_geometry(*f);
        f->r[0]=word(f->r[6])&15;
        return base+0xa4fe58;
    }
    if(kind==27) {
        capture_present(*f);f->r[0]=f->r[12];return f->r[3];
    }
    if(kind<26)count(gateway_hits[kind]);
    if(kind==25) {
        Context* c=context();Scope* s=c && !c->quarantine?find(*c,9):nullptr;
        if(s)s->attribution.begin(f->r[0],f->r[4]);else lost();
        f->r[5]=f->r[0];comparison_flags(*f,f->r[4],7);
        return base+0x3820bc;
    }
    if(kind>=21 && kind<=24) {
        // Actual native copy boundary, after generation and before freeing its
        // temporary. Never depend on execution of the generator-entry detour.
        const unsigned index=kind<23?0:kind-22;
        const uint32_t object=f->r[4],source=f->r[kind<23?7:kind==23?6:5];
        const unsigned offset=kind==24?0x64:0x5c;
        Context* c=context();Scope* ui=c && !c->quarantine?find(*c,12):nullptr;
        if(ui && ui->subject==object && ui->counts[index].ready) {
            const CountSnapshot selected=ui->counts[index];ui->counts[index].ready=false;
            Record r{};r.kind=2;r.ui=object;r.epoch=ui->epoch;r.tier=selected.attribution.threshold;
            r.rewards.epoch=r.epoch;r.rewards.count=8;r.generated=selected.slots;r.coverage=1u<<index;
            bool valid=selected.slots<=8 && field(object,offset,4) && copy(source,r.rewards.items,32);
            if(valid) {
                const uint32_t destination=word(object+offset);
                const unsigned start=kind<23?0:32;
                valid=destination && uint64_t(destination)+start+32<=0x100000000ull;
                r.rewards.array=destination+start;
                bool empty=true;
                for(unsigned j=0;j<8;++j)empty=empty && !r.rewards.items[j].item && !r.rewards.items[j].amount;
                if(empty)r.generated=0; // Count ran but absent table produced no items.
                else for(unsigned j=0;j<8;++j) {
                    const auto item=r.rewards.items[j];
                    valid=valid && (j<selected.slots ? item.item && item.amount : !item.item && !item.amount);
                }
                const bool complete=empty || selected.attribution.complete(selected.slots);
                if(!complete) {r.coverage|=0x80000000u;lost();}
                r.rewards.mask=complete?selected.attribution.mask(r.generated):0;
            }
            if(valid && ui->pending_count<8) {ui->pending[ui->pending_count++]=r;ui->copied|=1u<<index;}
            else {ui->incomplete=true;lost();}
        } else if(ui) {ui->incomplete=true;lost();}
        // Replay LDR r0,[r4,#field] / LDRH r1,[source]. Neither writes flags.
        f->r[0]=word(object+offset);
        f->r[1]=*reinterpret_cast<volatile const uint16_t*>(source);
        return base+hook(kind-4).site+8;
    }
    if(kind==19 || kind==20) {
        const unsigned i=kind-19;
        f->r[5]=i?1:31;
        f->r[13]=base+site_offset(i)+4;
        return base+site_offset(i)+8;
    }
    if(kind<2) {
        Context* c=context();
        if(force(c)) {
            count(forced_checks[kind]);
            if(!kind && c && !c->quarantine) {
                Scope* selected=find(*c,9);if(!selected)selected=find(*c,10);
                if(selected)selected->attribution.begin(31,selected->kind==10?2:UINT32_MAX);
            }
            f->r[0]=1;f->r[5]=kind?1:31;return base+site_offset(kind)+8;
        }
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
                if(!s->attribution.known) {
                    s->attribution.begin(threshold,kind==2?UINT32_MAX:2);
                    if(kind==2)s->attribution.valid=false; // Missing initial-count tap.
                }
                else if(s->attribution.threshold!=threshold)s->attribution.valid=false;
                if(kind==2 && s->attribution.first_slots==UINT32_MAX)s->attribution.valid=false;
                s->attribution.compare(kind==2?f->r[4]:kind-1,f->r[0]&31);
            } else lost();
        }
        // Replay both displaced words. Carry/overflow are those of CMP, with Q
        // and GE inherited untouched. AND/MOV have no S bit.
        if(kind==2)f->r[0]&=31; else f->r[7]=kind-1;
        comparison_flags(*f,f->r[kind==2?5:6],f->r[0]);
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
        invalidate_highlights();
        s.epoch=++c->serial;s.ui=s.subject;
        c->last_ui=s.ui;
        Record r{};r.kind=1;r.ui=s.ui;r.epoch=s.epoch;c->records.publish(r);
    } else if(kind==9) {
        s.subject=f->r[1]; // Native main A/B category, not an item pointer.
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
    } else if(kind==16) {
        invalidate_highlights();
    } else if(kind==15 && field(s.subject,0x3c,4) && word(s.subject+0x3c)==1) {
        // State 1 may reallocate the main array before opening the grid.
        // Snapshot BEFORE native frees it. Observe through the existing paired
        // update hook; no additional arena, TLS slot or game writes are needed.
        s.epoch=c->serial;
        if(field(s.subject,0x5c,8)) {
            s.array=word(s.subject+0x5c);s.count=word(s.subject+0x60);
            if(s.count<=48 && s.array) {
                for(unsigned start=0;start<s.count;start+=8) {
                    Record r{};r.kind=7;r.ui=s.subject;r.epoch=s.array+start*4;r.tier=s.epoch;
                    r.rewards.count=s.count-start<8?s.count-start:8;
                    if(uint64_t(s.array)+start*4+r.rewards.count*4>0x100000000ull ||
                       !copy(r.epoch,r.rewards.items,r.rewards.count*4)) {s.incomplete=true;break;}
                    s.pending[s.pending_count++]=r;
                }
            } else s.incomplete=true;
        } else s.incomplete=true;
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
        Scope* ui=find(*c,12);
        if(ui) {
            const int index=s.caller==base+0x381dc4 && s.subject==0 ? 0 :
                            s.caller==base+0x387a98 && s.subject==1 ? 1 : -1;
            if(index>=0 && f->r[0]<=8 && !ui->counts[index].ready) {
                ui->counts[index]={s.attribution,f->r[0],true};ui->counted|=1u<<index;
            } else {ui->incomplete=true;lost();}
        }
    } else if(s.kind==10) {
        Scope* ui=find(*c,12);
        if(ui) {
            // This native routine returns void: r0 is NOT its slot count.
            // Use its observed comparisons, then validate the generated prefix.
            const uint32_t slots=s.attribution.comparisons ?
                s.attribution.last_slots+(s.attribution.last_roll<s.attribution.threshold?1:0):0;
            if(s.caller==base+0x388084 && slots<=8 && !ui->counts[2].ready) {
                ui->counts[2]={s.attribution,slots,true};ui->counted|=4;
            } else {ui->incomplete=true;lost();}
        }
    } else if(s.kind==12) {
        const uint32_t order=__atomic_add_fetch(&completed_batches,1,__ATOMIC_RELAXED);
        for(unsigned i=0;i<s.pending_count;++i) {
            Record r=s.pending[i];Reward check[8]{};
            if(copy(r.rewards.array,check,r.rewards.count*4)) {
                bool same=true;
                for(unsigned j=0;j<r.rewards.count;++j) same=same &&
                    check[j].item==r.rewards.items[j].item && check[j].amount==r.rewards.items[j].amount;
                if(same) {c->records.publish(r);count(published_rewards);}else {lost();}
            } else lost();
        }
        Record end{};end.kind=6;end.ui=s.ui;end.epoch=s.epoch;
        end.coverage=s.counted && s.counted==s.copied && !s.incomplete ? 1:2;
        end.generated=s.pending_count;end.tier=order;c->records.publish(end);
    } else if(s.kind==14 && s.ui && s.array && field(s.subject,0x5c,4)) {
        // Native 0x623c08 copies source[i] to list.buffer[i], up to capacity.
        // The consumer follows that index mapping only after checking contents.
        const auto clear_copy=[&]() {
            Record r{};r.kind=5;r.ui=s.ui;r.tier=s.subject;r.coverage=1;
            r.rewards.epoch=c->serial;c->records.publish(r);
        };
        const unsigned total=s.count<word(s.subject+0x5c)?s.count:word(s.subject+0x5c);
        if(total<=48 && uint64_t(s.subject)+0x60+total*4<=0x100000000ull &&
           uint64_t(s.array)+total*4<=0x100000000ull) {
            // Immutable eight-entry chunks fit the existing mailbox payload.
            // Capture now, before a later list refresh or a render-thread drain.
            for(unsigned start=0;start<total || !start;start+=8) {
                Record r{};r.kind=5;r.ui=s.ui;r.epoch=s.array+start*4;r.tier=s.subject;
                r.coverage=start==0;r.rewards.epoch=c->serial;r.rewards.array=s.subject+0x60+start*4;
                r.rewards.count=total-start<8?total-start:8;
                if(copy(r.rewards.array,r.rewards.items,r.rewards.count*4))c->records.publish(r);
                else {clear_copy();lost();break;}
                if(!total)break;
            }
        } else {clear_copy();lost();}
    } else if(s.kind==15) {
        if(s.array && s.pending_count) {
            bool valid=!s.incomplete && field(s.subject,0x5c,8);
            const uint32_t destination=valid?word(s.subject+0x5c):0;
            valid=valid && destination && word(s.subject+0x60)>=s.count && word(s.subject+0x60)<=48;
            for(unsigned i=0;i<s.pending_count && valid;++i) {
                const auto& r=s.pending[i];Reward contents[8]{};
                const unsigned offset=r.epoch-s.array;
                valid=uint64_t(destination)+offset+r.rewards.count*4<=0x100000000ull &&
                    copy(destination+offset,contents,r.rewards.count*4);
                for(unsigned j=0;j<r.rewards.count;++j)valid=valid &&
                    contents[j].item==r.rewards.items[j].item && contents[j].amount==r.rewards.items[j].amount;
            }
            if(valid) {
                for(unsigned i=0;i<s.pending_count;++i) {
                    Record r=s.pending[i];r.rewards.array=destination+(r.epoch-s.array);c->records.publish(r);
                }
                if(destination!=s.array)count(remapped_arrays);
            } else {
                lost();count(mapping_faults);
                Record r{};r.kind=4;r.ui=s.subject;r.coverage=2;c->records.publish(r);
            }
        } else if(s.incomplete) {
            lost();count(mapping_faults);
            Record r{};r.kind=4;r.ui=s.subject;r.coverage=2;c->records.publish(r);
        }
        if(field(s.subject,0x3c,4))__atomic_store_n(&last_ui_state,word(s.subject+0x3c),__ATOMIC_RELAXED);
        if(!field(s.subject,0x3c,4) || word(s.subject+0x3c)<2 || word(s.subject+0x3c)>5) {
            invalidate_highlights();
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
    static_assert(highlight_rendering_accepted,"Native frame, shader and presentation fixtures required");
    if(initialized) {
        // Recheck owned signatures, without republishing or allocating. A
        // conflict cancels effective forcing and further attribution.
        const auto r=conditional.install(base,nullptr,0);
        if(highlight.report().state==State::Applied && highlight.install(base,nullptr,0).state!=State::Applied)
            __atomic_store_n(&highlight_ready,0,__ATOMIC_RELEASE);
        const auto v=visual.report().state==State::Fresh?visual.report():visual.install(base,nullptr,0);
        if(r.state!=State::Applied || v.state!=State::Applied) {
            __atomic_store_n(&pair_ready,0,__ATOMIC_RELEASE);
            __atomic_store_n(&capture_ready,0,__ATOMIC_RELEASE);
            __atomic_store_n(&highlight_ready,0,__ATOMIC_RELEASE);
            invalidate_highlights();
        }
        return;
    }
    initialized=1;base=forge_mem_getMainTextAddr();
    Hook pair[2]={hook(0),hook(1)};
    const auto r=conditional.install(base,pair,2);
    forge_log_info("[please-do-better] r7 conditional state=%u owned=%llx unsafe=%llx",unsigned(r.state),r.owned,r.unsafe);
    if(r.state!=State::Applied)return;
    __atomic_store_n(&pair_ready,1,__ATOMIC_RELEASE);
    if(nnosAllocateTlsSlot(&tls,nullptr) || tls<0) {tls=-1;lost();return;}
    Hook taps[20];for(unsigned i=0;i<20;++i)taps[i]=hook(i+2);
    const auto v=visual.install(base,taps,20);
    if(v.state==State::Applied)__atomic_store_n(&capture_ready,1,__ATOMIC_RELEASE);
    forge_log_info("[please-do-better] r7 observation state=%u owned=%llx unsafe=%llx",unsigned(v.state),v.owned,v.unsafe);
    if(v.state!=State::Applied)return;
    Hook rendering[2]={highlight_boundary_recipe(),presentation_recipe()};
    const auto h=highlight.install(base,rendering,2);
    if(h.state==State::Applied)__atomic_store_n(&highlight_ready,1,__ATOMIC_RELEASE);
    forge_log_info("[please-do-better] r7 highlights state=%u owned=%llx unsafe=%llx",unsigned(h.state),h.owned,h.unsafe);
}
static Record observed[8][8]{};
static Record displayed[8][8]{};
static uint32_t epochs[8]{}, owners[8]{}, latest_tier=0, bonus_count=0;
static uint32_t generated_count, summary_status, summary_order, summary_records;
void update() {
    count(update_hits);
    if(!seen(native_render)) {
        const uint32_t sr=uint32_t(uintptr_t(forge_singleton_getInstanceByName("sFestaRender")));
        if(field(sr,0x389cc,4))__atomic_store_n(&native_render,sr,__ATOMIC_RELEASE);
    }
    for(unsigned thread=0;thread<8;++thread) {
        auto& c=contexts[thread];Record r{};
        const uint32_t lost_before=c.records.overwritten;
        for(unsigned budget=0;budget<16 && c.records.read(r);++budget) {
            if(c.records.overwritten!=lost_before)break;
            if(r.kind==1 || ((r.kind==3 || r.kind==4) && r.ui==owners[thread])) {
                if(r.kind==4 && r.coverage==1)__atomic_store_n(&summary_status,2,__ATOMIC_RELEASE);
                for(auto& record:observed[thread])record={};
                for(auto& record:displayed[thread])record={};
                owners[thread]=r.kind==1?r.ui:0;epochs[thread]=r.epoch;
            } else if(r.kind==2 && r.ui==owners[thread] && r.epoch==epochs[thread]) {
                bool stored=false;
                for(auto& record:observed[thread])if(!record.kind) {record=r;stored=true;break;}
                if(!stored)lost();
            } else if(r.kind==2) {
                lost(); // Nested/stale batches are never silently adopted.
            } else if(r.kind==6 && r.ui==owners[thread] && r.epoch==epochs[thread] &&
                      uint32_t(r.tier-summary_order)>0 && uint32_t(r.tier-summary_order)<0x80000000u) {
                uint32_t records=0,tier=0,bonuses=0,generated=0;
                bool complete=r.coverage==1;
                for(const auto& record:observed[thread])if(record.kind) {
                    ++records;
                    if(record.tier)tier=!tier || tier==record.tier?record.tier:UINT32_MAX;
                    generated+=record.generated;
                    complete=complete && !(record.coverage&0x80000000u);
                    for(unsigned j=0;j<8;++j)bonuses+=(record.rewards.mask>>j)&1u;
                }
                summary_order=r.tier;
                __atomic_store_n(&latest_tier,tier,__ATOMIC_RELEASE);
                __atomic_store_n(&bonus_count,bonuses,__ATOMIC_RELEASE);
                __atomic_store_n(&generated_count,generated,__ATOMIC_RELEASE);
                __atomic_store_n(&summary_records,records,__ATOMIC_RELEASE);
                __atomic_store_n(&summary_status,records && records==r.generated && complete?1:2,__ATOMIC_RELEASE);
            } else if(r.kind==7 && r.ui==owners[thread] && r.tier==epochs[thread]) {
                for(auto& source:observed[thread]) {
                    if(!source.kind || source.rewards.array<r.epoch)continue;
                    const uint32_t offset=source.rewards.array-r.epoch;
                    if((offset&3) || uint64_t(offset)+source.rewards.count*4>uint64_t(r.rewards.count)*4)continue;
                    bool same=true;
                    for(unsigned j=0;j<source.rewards.count;++j)same=same &&
                        source.rewards.items[j].item==r.rewards.items[offset/4+j].item &&
                        source.rewards.items[j].amount==r.rewards.items[offset/4+j].amount;
                    if(same)source.rewards.array=r.rewards.array+offset;
                    else {source={};lost();count(mapping_faults);}
                }
            } else if(r.kind==5 && r.ui==owners[thread] && r.rewards.epoch==epochs[thread]) {
                if(r.coverage)for(auto& record:displayed[thread])
                    if(record.generated==r.tier)record={};
                for(unsigned i=0;i<8;++i) {
                    const auto& source=observed[thread][i];
                    if(!source.kind || source.rewards.array<r.epoch)continue;
                    const uint32_t offset=source.rewards.array-r.epoch;
                    if((offset&3) || uint64_t(offset)+source.rewards.count*4>uint64_t(r.rewards.count)*4 ||
                       uint64_t(r.rewards.array)+offset+source.rewards.count*4>0x100000000ull)continue;
                    Record target=source;target.generated=r.tier;target.rewards.array=r.rewards.array+offset;
                    Reward contents[8]{};bool same=true;
                    for(unsigned j=0;j<target.rewards.count;++j)contents[j]=r.rewards.items[offset/4+j];
                    bool changed=false;
                    for(unsigned j=0;j<target.rewards.count;++j) {
                        if(!compatible_refresh(target.rewards.items[j],contents[j])) {
                            same=false;
                            mapping_detail.publish({offset/4+j,
                                uint32_t(target.rewards.items[j].item)|(uint32_t(target.rewards.items[j].amount)<<16),
                                uint32_t(contents[j].item)|(uint32_t(contents[j].amount)<<16)});
                        }
                        changed=changed || contents[j].item!=target.rewards.items[j].item ||
                            contents[j].amount!=target.rewards.items[j].amount;
                        if(!contents[j].item)target.rewards.mask&=~(1u<<j);
                    }
                    if(same) {
                        bool stored=false;
                        for(auto& record:displayed[thread])if(!record.kind) {record=target;stored=true;break;}
                        if(!stored)lost();
                        if(changed)count(expected_refreshes);
                    }
                    else {lost();count(mapping_faults);}
                }
            }
        }
        if(c.records.overwritten!=lost_before) {
            owners[thread]=0;
            for(auto& record:observed[thread])record={};
            for(auto& record:displayed[thread])record={};
            lost();
            __atomic_store_n(&summary_status,2,__ATOMIC_RELEASE);
        }
    }
    unsigned bound=0;
    const uint32_t fence=seen(live_fence);
    for(const auto& thread:displayed)for(const auto& record:thread)if(record.kind && record.generated) {
        const uint32_t list=record.generated;
        if(record.rewards.array<list+0x60 || !field(list,0x4c,4) || !field(list,0x24,4))continue;
        const unsigned first=(record.rewards.array-list-0x60)/4,group=word(list+0x4c);
        if(group>7 || first>=48 || !field(list,0x160+group*0x28,20))continue;
        const uint32_t holder=word(list+0x24),ir=word(list+0x160+group*0x28),br=word(list+0x164+group*0x28);
        const uint32_t ids=word(list+0x16c+group*0x28);
        for(unsigned j=0;j<record.rewards.count;++j)if((record.rewards.mask>>j)&1u) {
            const unsigned index=first+j;
            if(index>=48 || !field(ids,index*4,4))continue;
            const unsigned icon_index=word(ids+index*4);unsigned frame_index=0,id=0;
            if(!frame_layout(group,ir,br,index,icon_index,frame_index,id))continue;
            const uint32_t icon=gui_node(holder,ir,icon_index),node=gui_node(holder,br,frame_index);
            if(!texture_node(icon) || !texture_node(node) || word(node+0x50)!=id)continue;
            if(bound==64) {count(render_faults);const uint32_t sr=seen(native_render);
                if(sr)for(unsigned frame=0;frame<2;++frame) {
                    const uint32_t serial=word(sr+0x33f50)-(word(sr+0x33f4c)!=frame);
                    mark_overflow(frame,serial);
                }bound=0;goto bindings_done;}
            Binding b{fence,record.ui,record.epoch,list,group,index,node,icon,id,record.rewards.items[j]};
            if(!bindings[bound++].publish(b)) {count(render_faults);bound=0;goto bindings_done;}
        }
    }
 bindings_done:
    __atomic_store_n(&binding_count,bound,__ATOMIC_RELEASE);

}
void diagnostics() {
    const auto r=conditional.report(),v=visual.report();
    const auto tier=__atomic_load_n(&latest_tier,__ATOMIC_ACQUIRE);
    const char* name=tier==25?"Good Luck":tier==28?"Great Luck":tier==31?"Miraculous Luck":
                     tier==22?"Normal":tier==16?"Bad Luck":tier==8?"Horrible Luck":tier==UINT32_MAX?"Mixed luck":"Unavailable";
    const uint32_t status=seen(summary_status);
    if(!status)igTextUnformatted("No completed reward observation yet; extra slots unavailable.",nullptr);
    else {
        if(status==1)igText("Last rewards: %s; %u generated, %u extra slots",name,seen(generated_count),seen(bonus_count));
        else igTextUnformatted("Extra-slot total unavailable: observation incomplete.",nullptr);
    }
    if(seen(highlight_ready))igTextUnformatted("Gold highlights: enabled for verified extra slots.",nullptr);
    else igTextUnformatted("Gold highlights unavailable: startup rendering checks failed.",nullptr);
    if(!igTreeNode_Str("Diagnostics###pdb_diagnostics"))return;
    const char* states[]={"not installed","safe startup checks passed","rejected","rolled back","UNSAFE; residual/changed bytes"};
    igText("Conditional: %s",states[unsigned(r.state)]);
    igText("Observation: %s",states[unsigned(v.state)]);
    if(r.failure!=Failure::None || r.unsafe)igText("Conditional failure %u at site %u; cache result 0x%X. Full restart required.",unsigned(r.failure),r.site,r.cache);
    if(v.failure!=Failure::None || v.unsafe)igText("Observation failure %u at site %u; cache result 0x%X. Full restart required.",unsigned(v.failure),v.site,v.cache);
    igTextUnformatted(status==1?"Observation coverage: verified traced routes.":status?"Observation coverage: incomplete.":"Observation coverage: awaiting rewards.",nullptr);
    igText("Currently highlighted slots: %u; bound extra slots: %u",seen(highlighted_count),seen(binding_count));
    if(seen(render_faults))igText("Highlight capture faults: %u",seen(render_faults));
    if(seen(unsupported_draws))igTextUnformatted("Some draw paths are unsupported; their markers are suppressed.",nullptr);
    const auto h=highlight.report();
    if(h.failure!=Failure::None || h.unsafe)igText("Highlight failure %u at site %u; full restart required.",unsigned(h.failure),h.site);
    igText("Capture faults: %u; incompatible display copies: %u",seen(drops),seen(mapping_faults));
    CopyFault fault{};
    if(seen(mapping_faults) && mapping_detail.read(fault))igText("Last copy mismatch: index %u, item/quantity %u/%u -> %u/%u",
        fault.index,fault.expected&65535,fault.expected>>16,fault.actual&65535,fault.actual>>16);
    igTextUnformatted("Extra slots compare with normal luck; no rare-drop guarantee. Last reward totals remain after collection.",nullptr);
    igTextUnformatted("Disable the legacy Great Luck cheat. Plugin removal requires a full restart.",nullptr);
    igTreePop();
}
void render() {
    __atomic_store_n(&highlighted_count,0,__ATOMIC_RELAXED);
    const uint32_t cycle=__atomic_fetch_add(&draw_cycle,1,__ATOMIC_SEQ_CST);
    Presentation p{};
    if(!seen(highlight_ready) || !__atomic_exchange_n(&present_pending,0,__ATOMIC_ACQ_REL) ||
       !presentation.read(p) || p.cycle!=cycle || seen(frame_overflow[p.frame])==p.serial+1)return;
    ImGuiIO* io=igGetIO_Nil();
    if(!io || io->DisplaySize.x<=0 || io->DisplaySize.y<=0)return;
    ImDrawList* draw=igGetBackgroundDrawList_Nil();if(!draw)return;
    // Triangle wave: two-second period, 0.45..0.75 alpha, no animation RNG.
    const float now=float(igGetTime());if(!std::isfinite(now) || now<0 || now>4294967296.f)return;
    const float phase=now*.5f-float(uint32_t(now*.5f));
    const float alpha=.45f+.30f*float(1-std::fabs(phase*2-1));
    const uint32_t gold=(uint32_t(alpha*255)<<24)|0x0054c5f2u;
    const float scale=io->DisplaySize.y/720,thickness=1.5f*scale;
    const uint32_t fence=seen(live_fence);unsigned rendered=0;
    // Read each atomic snapshot once. A fixed stack copy avoids repeatedly
    // loading 64 geometry payloads for every slot at the presentation boundary.
    Binding current[64]{};bool valid[64]{},drawn[64]{};
    const unsigned bound=seen(binding_count)<64?seen(binding_count):64;
    for(unsigned i=0;i<bound;++i)valid[i]=bindings[i].read(current[i]) && current[i].fence==fence;
    for(unsigned sample=0;sample<64;++sample) {
        Geometry g{};
        if(!geometries[sample].read(g) || g.frame!=p.frame || g.owner!=p.owner || g.serial!=p.serial ||
           std::fabs(g.width-io->DisplaySize.x)>.5f || std::fabs(g.height-io->DisplaySize.y)>.5f)continue;
        unsigned matched=64;
        for(unsigned i=0;i<bound;++i)if(valid[i] && !drawn[i] && current[i].node==g.binding.node &&
            !std::memcmp(&current[i],&g.binding,sizeof(Binding))) {matched=i;break;}
        if(matched==64)continue;
        if(seen(live_fence)!=fence)return;
        drawn[matched]=true;
        ImVec2 corners[4];for(unsigned k=0;k<4;++k)corners[k]={g.points[k*2],g.points[k*2+1]};
        ImDrawList_PushClipRect(draw,{g.clip[0],g.clip[1]},{g.clip[2],g.clip[3]},true);
        // Native texture strip order is TL,TR,BL,BR. Walk the perimeter rather
        // than crossing its diagonals; mirrored/rotated frames keep that order.
        const unsigned order[4]={0,1,3,2};
        for(unsigned k=0;k<4;++k)ImDrawList_AddLine(draw,corners[order[k]],corners[order[(k+1)%4]],gold,thickness);
        const ImVec2 anchor=corners[0];
        const float radius=3.0f*scale;
        const ImVec2 spark[8]={{anchor.x,anchor.y-radius},{anchor.x+.7f*scale,anchor.y-.7f*scale},
          {anchor.x+radius,anchor.y},{anchor.x+.7f*scale,anchor.y+.7f*scale},
          {anchor.x,anchor.y+radius},{anchor.x-.7f*scale,anchor.y+.7f*scale},
          {anchor.x-radius,anchor.y},{anchor.x-.7f*scale,anchor.y-.7f*scale}};
        for(unsigned k=0;k<8;++k)ImDrawList_AddLine(draw,spark[k],spark[(k+1)%8],gold,scale);
        ImDrawList_PopClipRect(draw);++rendered;
    }
    __atomic_store_n(&highlighted_count,rendered,__ATOMIC_RELAXED);
}
}
