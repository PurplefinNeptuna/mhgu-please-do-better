#include "log_policy.h"
#include "runtime.h"
#include "mode.h"
#include "attribution.h"
#include "quantity.h"
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
static uint32_t quantity_faults;
static uint32_t base, initialized, pair_ready, capture_ready, drops;
static uint32_t expected_refreshes, remapped_arrays, mapping_faults;
struct CopyFault { uint32_t index,expected,actual,route=0; };
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
struct QuantityPage { uint32_t array=0,count=0; };
struct Scope {
    uint32_t kind=0, caller=0, sp=0, subject=0, array=0, start=0, count=0;
    // Keep inactive contexts in BSS. Entry always assigns a latched 1..5 value
    // before this scope can be used; zero is only an inactive sentinel.
    bool force=false; uint8_t multiplier=0;
    bool quantity_ready=false, player_blank=false, quantity_done=false;
    QuantityPage quantity_pages[3]{};
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
    // A uUIResult owns one result generation. Its existing destructor hook
    // clears this latch before the address can be reused for another quest.
    // Mark even 1x and failed attempts: later settings/rebuilds cannot alter it.
    uint32_t quantity_ui=0;
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
// The builder owns this heap array until its paired return; no allocator runs
// during the mutation. The pinned Forge binary lacks the queryMemory export
// declared by its headers; reuse our existing checked SVC adapter for this gap.
static bool writable_rewards(uint32_t a,unsigned n) {
    MemoryInfo m{};uint32_t page=0;
    return a && n && uint64_t(a)+n<=0x100000000ull && !pdb_svc_query(&m,&page,a) &&
        (m.perm&3)==3 && m.addr<=a && m.addr<=0x100000000ull &&
        m.size<=0x100000000ull-m.addr && uint64_t(a)+n<=m.addr+m.size;
}
static void quantity_fault(QuantityFault reason) {
    if(reason!=QuantityFault::None)
        __atomic_fetch_or(&quantity_faults,1u<<unsigned(reason),__ATOMIC_RELAXED);
}
// Run at the original builder's paired return, before immutable observations
// are published. Pages 0/1/2 use UI+0x5C/+0x64/+0x6C respectively; page 3
// (+0x74) is companion gathering/plunder and is excluded from every write.
// The UI-object latch, cleared by the existing destructor, makes this a single
// attempt per result lifetime, including 1x and unsupported-data failures.
static void multiply_player_pages(Scope& s) {
    if(s.multiplier==1 || s.quantity_done)return;
    if(!__atomic_load_n(&capture_ready,__ATOMIC_ACQUIRE)) {
        quantity_fault(QuantityFault::Generation);return;
    }
    if(!s.quantity_ready || !field(s.ui,0x5c,32)) {
        quantity_fault(QuantityFault::Memory);return;
    }
    QuantityPage all[4]{};
    for(unsigned page=0;page<4;++page) {
        const unsigned offset=0x5c+page*8;
        all[page]={word(s.ui+offset),word(s.ui+offset+4)};
        const auto& q=all[page];
        const unsigned capacity=page<3?player_page_capacities[page]:palico_page_capacity;
        if(q.count>capacity || (q.count && (!q.array || q.array%4 ||
           uint64_t(q.array)+q.count*4>0x100000000ull)) ||
           (page<3 && (q.array!=s.quantity_pages[page].array ||
            q.count!=s.quantity_pages[page].count ||
            (q.count && !writable_rewards(q.array,q.count*4))))) {
            quantity_fault(QuantityFault::Memory);return;
        }
        // Native allocations are disjoint. Reject overlapping included pages
        // or any alias into the excluded Palico page, regardless of contents.
        for(unsigned previous=0;previous<page;++previous) {
            const auto& other=all[previous];
            if(q.count && other.count && q.array<uint64_t(other.array)+other.count*4 &&
               other.array<uint64_t(q.array)+q.count*4) {
                quantity_fault(QuantityFault::Memory);return;
            }
        }
    }
    // Constructors zero all player arrays. For a nonempty entry preimage,
    // require fresh observed native main/free-hunt counts and matching copies.
    // Lost observation/TLS must never authorize scaling previously built data.
    if(!s.player_blank && (!s.counted || s.counted!=s.copied)) {
        quantity_fault(QuantityFault::Generation);return;
    }
    Reward original[3][first_screen_capacity]{};
    for(unsigned page=0;page<3;++page) {
        const auto& q=all[page];
        if(q.count && !copy(q.array,original[page],q.count*4)) {
            quantity_fault(QuantityFault::Memory);return;
        }
        const auto fault=quantity_preflight(original[page],q.count,s.multiplier);
        if(fault!=QuantityFault::None) {quantity_fault(fault);return;}
    }
    // Match captured main/free-hunt snapshots to their original live page.
    // Validate every overlapping range before touching ANY player page. Luck
    // attribution, slot indices and item IDs remain attached to the same slots.
    int snapshot_page[8];
    if(s.pending_count>8) {quantity_fault(QuantityFault::Snapshot);return;}
    for(unsigned i=0;i<s.pending_count;++i) {
        snapshot_page[i]=-1;
        const auto& r=s.pending[i].rewards;
        for(unsigned page=0;page<3;++page) {
            const auto& q=all[page];
            const uint64_t end=uint64_t(r.array)+uint64_t(r.count)*4;
            if(!q.count || !r.count || r.array>=uint64_t(q.array)+q.count*4 || q.array>=end)continue;
            if(r.array<q.array || (r.array-q.array)%4 || r.count>8 ||
               end>uint64_t(q.array)+q.count*4) {
                quantity_fault(QuantityFault::Snapshot);return;
            }
            const unsigned start=(r.array-q.array)/4;
            for(unsigned j=0;j<r.count;++j)
                if(original[page][start+j].item!=r.items[j].item ||
                   original[page][start+j].amount!=r.items[j].amount) {
                    quantity_fault(QuantityFault::Snapshot);return;
                }
            snapshot_page[i]=int(page);
        }
    }
    // All checks passed for all three pages. Only occupied amount halfwords
    // change. Collection/appraisal therefore receives exactly the displayed
    // product, subject to native inventory and appraisal queue capacity.
    for(unsigned page=0;page<3;++page) {
        auto* live=reinterpret_cast<volatile Reward*>(all[page].array);
        for(unsigned i=0;i<all[page].count;++i)
            if(original[page][i].item)live[i].amount=original[page][i].amount*s.multiplier;
    }
    for(unsigned i=0;i<s.pending_count;++i)if(snapshot_page[i]>=0)
        for(unsigned j=0;j<s.pending[i].rewards.count;++j)
            s.pending[i].rewards.items[j].amount*=s.multiplier;
}
static Snapshot<Binding> bindings[64];
static Snapshot<Geometry> geometries[64];
static Snapshot<Presentation> presentation;
static uint32_t binding_count, highlight_ready, highlighted_count, render_faults, unsupported_draws;
static uint32_t live_fence=1, draw_cycle=1, present_pending, native_render;
// Gameplay producers publish only fixed atomic telemetry. Formatting stays in
// Forge callbacks, outside gateways and their live register/GE contracts.
enum GeometryGate { GEnter,GReady,GRegisters,GUnbound,GMatched,GList,GItem,GIdentity,
    GUncached,GTiled,GRenderer,GFrame,GLayout,GSubmission,GTarget,GTexture,GShader,
    GViewport,GBuffer,GInputs,GQuad,GClip,GEpoch,GPublished,GConflict,GOverflow,GCount };
enum PresentGate { PEnter,PDisabled,PContext,PFrame,PMetadata,PImage,PPublished,PConflict,PCount };
enum RenderGate { REnter,RDisabled,RPending,RSnapshot,RCycle,ROverflow,RIO,RDrawList,RTime,
    RSample,RFrame,RDimensions,RBinding,REpoch,RDrawn,RCount };
static uint32_t geometry_gates[GCount]{},present_gates[PCount]{},render_gates[RCount]{};
struct GeometryTrace {
    uint32_t gate,node,ctx,list,index,renderer,cache,flags,offset,stride,renderer_offset,
        draw_flags,frame,serial,parallel,cycle,fence,target,extent,model,global,buffer;
    float vertices[24]{},matrix[16]{},projection[4]{};
    uint32_t target_flags=0,clip_sentinel=0,clip_valid=0;
    int32_t viewport[4]{},raw_clip[4]{},sentinel_clip[4]{},effective_clip[4]{};
};
struct PresentTrace {
    uint32_t gate,sr,queue,window,index,expected_queue,expected_index,frame,serial,parallel,
        resource,cached_index,table,image;
};
static Snapshot<GeometryTrace> geometry_trace;
static Snapshot<PresentTrace> present_trace;
struct DrawRejection {
    uint32_t reason=0,node_flags=0,target=0,sentinel=0,presented=0,technique=0,uniform_count=0;
    uint32_t uniforms[9]{};
    uint32_t target_flags=0,extent=0;int32_t viewport[4]{};
    uint32_t fence=0,texture=0,image=0,index=0;
};
static Snapshot<DrawRejection> draw_rejection;
static uint32_t rejection_logged;
static void remember_rejection(DrawRejection d) {
    d.fence=seen(live_fence);DrawRejection prior{};
    // Keep the first rejection for this screen readable while image identities
    // alternate. A new screen fence permits a new coherent diagnostic.
    if(!draw_rejection.read(prior) || prior.fence!=d.fence)draw_rejection.publish(d);
    count(unsupported_draws);
}
static void reject_draw(uint32_t reason,uint32_t node,uint32_t renderer=0,uint32_t target=0,
                        uint32_t sentinel=0,uint32_t presented=0) {
    DrawRejection d{};d.reason=reason;
    if (mod_log::diagnostics) {
        d.node_flags=word(node+0x108);
        d.target=target;d.sentinel=sentinel;d.presented=presented;
        if(field(renderer,0x1ac,4)) {
            const uint32_t packet=word(renderer+0x1ac);
            if(readable(packet,0x5c)) {
                d.target_flags=word(packet+0x14);d.extent=word(packet+0x58);
                copy(packet+((d.target_flags&0x200)?0x28:0x18),d.viewport,16);
            }
        }
        if(field(renderer,0x1d8,4))d.technique=word(renderer+0x1d8);
        if(field(renderer,0x1a4,4)) {
            const uint32_t packet=word(renderer+0x1a4);
            const uint32_t program=field(packet,8,4)?word(packet+8):0;
            if(field(program,0x40,8)) {
                d.uniform_count=word(program+0x44);
                if(d.uniform_count && d.uniform_count<=9)
                    copy(word(program+0x40),d.uniforms,d.uniform_count*4);
            }
        }
    }
    remember_rejection(d);
}
static void report_draw_rejection() {
    DrawRejection d{};
    if(!draw_rejection.read(d) || !d.reason || d.reason>7 || d.fence!=seen(live_fence))return;
    // Formatting/logging runs only in Forge callbacks, outside the geometry
    // gateway and its live GE contract. One entry per class prevents floods.
    const uint32_t reason=d.reason;
    if(!(__atomic_fetch_or(&rejection_logged,1u<<reason,__ATOMIC_RELAXED)&(1u<<reason))) {
        static const char* const reasons[]={"unknown", "tiled or perspective geometry", "missing render target", "unsupported surface", "unsupported viewport", "unsupported shader", "unmapped texture", "unsupported clip"};
        forge_log_warn("[please-do-better] unsupported reward draw path (%u: %s); marker suppressed; restart if persistent", reason, reasons[reason]);
    }
}
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
static uint32_t surface_texture(uint32_t surface) {
    // BC0E98 supplies surface+0x10 -> +0x3C to NVN SetRenderTargets and
    // surface+0x14 as the texture view. Only the default view is supported.
    if(!field(surface,0x10,8) || word(surface+0x14))return 0;
    const uint32_t gpu=word(surface+0x10);
    return field(gpu,0x3c,4)?word(gpu+0x3c):0;
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
static uint32_t trace_word(uint32_t address,unsigned offset) {
    return field(address,offset,4)?word(address+offset):0;
}
// BC12D8..BC1364 intersects the selected scissor, normalizes inverted axes,
// then replaces an exact shared-sentinel match with the cached viewport.
// BC1314's PC-relative load resolves this relocated GOT entry. Never assume
// that the sentinel's current contents are zero.
static bool effective_clip(const int32_t viewport[4],const int32_t raw[4],int32_t out[4],
                           int32_t sentinel[4],uint32_t& sentinel_address) {
    if(!field(base,0x183f2b0,4))return false;
    sentinel_address=word(base+0x183f2b0);
    if(!copy(sentinel_address,sentinel,16))return false;
    for(unsigned i=0;i<4;++i)
        out[i]=i<2?(viewport[i]>raw[i]?viewport[i]:raw[i]):(viewport[i]<raw[i]?viewport[i]:raw[i]);
    if(out[2]<out[0])out[0]=out[2]=0;
    if(out[3]<out[1])out[1]=out[3]=0;
    bool match=true;for(unsigned i=0;i<4;++i)match=match && out[i]==sentinel[i];
    if(match)for(unsigned i=0;i<4;++i)out[i]=viewport[i];
    return true;
}
static void trace_geometry(unsigned gate,uint32_t node,uint32_t ctx,const Binding& b) {
    count(geometry_gates[gate]);if (!mod_log::diagnostics) return;GeometryTrace t{};
    t.gate=gate;t.node=node;t.ctx=ctx;t.list=b.list;t.index=b.index;
    t.renderer=trace_word(ctx,4);t.cache=trace_word(node,0xc0);t.flags=trace_word(node,0x108);
    t.offset=trace_word(node,0xbc);t.stride=trace_word(t.renderer,0x134);
    t.renderer_offset=trace_word(t.renderer,0x138);t.draw_flags=trace_word(t.renderer,0x54);
    const uint32_t sr=seen(native_render);
    t.frame=trace_word(sr,0x33f4c);t.serial=trace_word(sr,0x33f50);
    t.parallel=field(sr,0x1f,1)?*reinterpret_cast<volatile const uint8_t*>(sr+0x1f):UINT32_MAX;
    t.cycle=seen(draw_cycle);t.fence=seen(live_fence);
    t.target=trace_word(t.renderer,0x1ac);t.extent=trace_word(t.target,0x58);
    t.target_flags=trace_word(t.target,0x14);
    const unsigned alternate=(t.target_flags&0x200)?0x10:0;
    if(field(t.target,0x18+alternate,16) && field(t.target,0x38+alternate,16) &&
       copy(t.target+0x18+alternate,t.viewport,16) && copy(t.target+0x38+alternate,t.raw_clip,16)) {
        if(t.viewport[0]<0)t.viewport[0]=0;
        if(t.viewport[1]<0)t.viewport[1]=0;
        if(t.viewport[2]>int32_t(t.extent&65535))t.viewport[2]=t.extent&65535;
        if(t.viewport[3]>int32_t(t.extent>>16))t.viewport[3]=t.extent>>16;
        if(t.viewport[2]<t.viewport[0])t.viewport[0]=t.viewport[2]=0;
        if(t.viewport[3]<t.viewport[1])t.viewport[1]=t.viewport[3]=0;
        t.clip_valid=effective_clip(t.viewport,t.raw_clip,t.effective_clip,t.sentinel_clip,t.clip_sentinel);
    }
    t.model=trace_word(t.renderer,0x18bc);t.global=trace_word(t.renderer,0x18b4);
    t.buffer=trace_word(trace_word(base,0x212668c),0xb0);
    if(uint64_t(t.buffer)+t.offset<=UINT32_MAX)copy(t.buffer+t.offset,t.vertices,sizeof(t.vertices));
    copy(t.model,t.matrix,sizeof(t.matrix));copy(t.global,t.projection,sizeof(t.projection));
    geometry_trace.publish(t);
}
static void trace_present(unsigned gate,const RawFrame& f) {
    count(present_gates[gate]);if(!mod_log::diagnostics || !seen(binding_count))return;
    PresentTrace t{};t.gate=gate;t.sr=seen(native_render);
    const uint32_t owner=t.sr+0x34100;
    t.queue=f.r[12];t.window=f.r[1];t.index=f.r[2];
    t.expected_queue=trace_word(owner,0x46f8);t.expected_index=trace_word(owner,0x46fc);
    t.frame=trace_word(t.sr,0x33f4c);t.serial=trace_word(t.sr,0x33f50);
    t.parallel=field(t.sr,0x1f,1)?*reinterpret_cast<volatile const uint8_t*>(t.sr+0x1f):UINT32_MAX;
    t.resource=trace_word(owner,0x48cc);t.cached_index=trace_word(owner,0x48d0);
    t.table=t.index<3?trace_word(owner,0x48c0+t.index*4):0;t.image=trace_word(t.resource,0x3c);
    present_trace.publish(t);
}
static void capture_geometry(RawFrame& f) {
    count(geometry_gates[GEnter]);
    if(!seen(highlight_ready) || !seen(binding_count))return;
    count(geometry_gates[GReady]);
    const uint32_t node=f.r[5],ctx=f.r[4];
    if(uint64_t(node)+0xcc>UINT32_MAX || f.r[6]!=node+0xcc) {count(geometry_gates[GRegisters]);return;}
    Binding b{};unsigned slot=64;
    const uint32_t fence=seen(live_fence),cycle=seen(draw_cycle);
    for(unsigned i=0;i<seen(binding_count) && i<64;++i)
        if(bindings[i].read(b) && b.node==node && b.fence==fence) {slot=i;break;}
    if(slot==64) {count(geometry_gates[GUnbound]);return;}
    count(geometry_gates[GMatched]);
    // Native draw proves the node is alive. Its exact list identity is retained
    // until a UI exit/destructor invalidates the fence BEFORE native freeing.
    if(!field(b.list,0x4c,0x14) || word(b.list+0x4c)!=b.group || b.index>=word(b.list+0x5c) ||
       !field(b.list,0x60+b.index*4,4)) {trace_geometry(GList,node,ctx,b);return;}
    Reward current{};
    if(!copy(b.list+0x60+b.index*4,&current,4) || !current.item || !current.amount ||
       !compatible_refresh(b.item,current)) {trace_geometry(GItem,node,ctx,b);return;}
    if(!texture_node(node) || word(node+0x50)!=b.id ||
       !field(ctx,4,4)) {trace_geometry(GIdentity,node,ctx,b);return;}
    if(!(word(node+0xc0)&0x800000)) {trace_geometry(GUncached,node,ctx,b);return;}
    if(word(node+0x108)&0x30) {trace_geometry(GTiled,node,ctx,b);reject_draw(1,node);return;}
    const uint32_t renderer=word(ctx+4),sr=seen(native_render);
    if(!field(renderer,0x18bc,4) || !field(sr,0x389cc,4)) {trace_geometry(GRenderer,node,ctx,b);return;}
    if(!field(sr,0x1f,1) || !field(sr,0x33f50,4) ||
       *reinterpret_cast<volatile const uint8_t*>(sr+0x1f)>1 || word(sr+0x33f4c)>1) {trace_geometry(GFrame,node,ctx,b);return;}
    if(!field(renderer,0x138,4) || *reinterpret_cast<volatile const uint8_t*>(renderer+0x134)!=24 ||
       word(renderer+0x138)!=word(node+0xbc)) {trace_geometry(GLayout,node,ctx,b);return;}
    // The native draw-packet helper returns without enqueueing when these
    // renderer flags suppress submission, even though vertex construction
    // itself returns success. Such frames must receive no marker.
    const uint32_t draw_flags=word(renderer+0x54);
    if(!(draw_flags&0x100) && (draw_flags&0x50)) {trace_geometry(GSubmission,node,ctx,b);return;}
    const uint32_t target_packet=word(renderer+0x1ac);
    const uint32_t sentinel=indirect(word(sr+0x389c0),0x204);
    const uint32_t presented=indirect(word(sr+0x389cc),0x204);
    if(!readable(target_packet,0x5c)) {trace_geometry(GTarget,node,ctx,b);reject_draw(2,node,renderer);return;}
    const uint32_t surface=word(target_packet);
    // Validate the captured native surface/view, retaining its image for logs.
    // Overlay eligibility uses projected slot geometry, not texture equality.
    const uint32_t texture=surface==sentinel?0:surface_texture(surface);
    if(!surface || (surface!=sentinel && !texture)) {
        trace_geometry(GTexture,node,ctx,b);reject_draw(6,node,renderer,surface,sentinel,presented);return;
    }
    if(!shader_2d(renderer)) {trace_geometry(GShader,node,ctx,b);reject_draw(5,node,renderer,surface,sentinel,presented);return;}
    int32_t viewport[4]{},clip[4]{};
    const unsigned alternate=(word(target_packet+0x14)&0x200)?0x10:0;
    if(!copy(target_packet+0x18+alternate,viewport,16) ||
       !copy(target_packet+0x38+alternate,clip,16)) {trace_geometry(GViewport,node,ctx,b);return;}
    // BC0E98 selects these exact two banks, clamps viewport to surface size,
    // then intersects the scissor. Accept only its full, zero-origin result.
    const uint32_t extent=word(target_packet+0x58);
    const int32_t width=extent&65535,height=extent>>16;
    if(viewport[0]<0)viewport[0]=0;
    if(viewport[1]<0)viewport[1]=0;
    if(viewport[2]>width)viewport[2]=width;
    if(viewport[3]>height)viewport[3]=height;
    if(viewport[0] || viewport[1] || viewport[2]!=width || viewport[3]!=height ||
       width<=0 || height<=0 || width>16384 || height>16384) {
        trace_geometry(GViewport,node,ctx,b);reject_draw(4,node,renderer,surface,sentinel,presented);return;
    }
    int32_t resolved_clip[4]{},sentinel_clip[4]{};uint32_t clip_sentinel=0;
    if(!effective_clip(viewport,clip,resolved_clip,sentinel_clip,clip_sentinel)) {
        trace_geometry(GClip,node,ctx,b);return;
    }
    // The verified GUI shader projects into this full framebuffer viewport.
    // Offset/half-size targets are deliberately unsupported.
    const uint32_t gui=field(base,0x212668c,4)?word(base+0x212668c):0;
    if(!field(gui,0xb0,4)) {trace_geometry(GBuffer,node,ctx,b);return;}
    const uint32_t start=word(gui+0xb0),offset=word(node+0xbc);
    if(uint64_t(start)+offset+96>0x100000000ull) {trace_geometry(GBuffer,node,ctx,b);return;}
    float vertices[24]{},model[16]{},global[4]{};
    if(!copy(start+offset,vertices,96) || !copy(word(renderer+0x18bc),model,64) ||
       !field(renderer,0x18b4,4) || !copy(word(renderer+0x18b4),global,16)) {trace_geometry(GInputs,node,ctx,b);return;}
    Geometry g{};g.binding=b;g.cycle=cycle;g.frame=word(sr+0x33f4c);g.owner=sr+0x34100;g.serial=word(sr+0x33f50);
    g.surface=surface;g.texture=texture;
    g.width=float(viewport[2]);g.height=float(viewport[3]);
    if(!screen_quad(vertices,model,global,g.width,g.height,g.points)) {trace_geometry(GQuad,node,ctx,b);return;}
    for(unsigned i=0;i<4;++i)g.clip[i]=float(resolved_clip[i]);
    if(resolved_clip[2]<=resolved_clip[0] || resolved_clip[3]<=resolved_clip[1]) {trace_geometry(GClip,node,ctx,b);return;}
    if(seen(live_fence)!=fence || seen(draw_cycle)!=cycle) {trace_geometry(GEpoch,node,ctx,b);return;}
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
            trace_geometry(published?GPublished:GConflict,node,ctx,b);
            if(!published) {count(render_faults);mark_overflow(g.frame,g.serial);}
            return;
        }
        __atomic_store_n(&geometry_claims[i],0,__ATOMIC_RELEASE);
    }
    trace_geometry(GOverflow,node,ctx,b);count(render_faults);mark_overflow(g.frame,g.serial);
}
static void capture_present(RawFrame& f) {
    count(present_gates[PEnter]);
    if(!seen(highlight_ready)) {trace_present(PDisabled,f);return;}
    const uint32_t sr=seen(native_render),owner=sr+0x34100;
    if(!sr || !field(owner,0x46f8,8) || !field(sr,0x33f4c,8) || !field(sr,0x1f,1) ||
       f.r[1]!=owner+0x4740 || f.r[12]!=word(owner+0x46f8) || f.r[2]!=word(owner+0x46fc)) {trace_present(PContext,f);return;}
    const uint32_t parallel=*reinterpret_cast<volatile const uint8_t*>(sr+0x1f),frame=word(sr+0x33f4c);
    if(parallel>1 || frame>1) {trace_present(PFrame,f);return;}
    // 86A28C records the acquired RESOURCE and index. 869ECC builds the
    // NVN window texture array from each resource+0x3C, not the resource itself.
    const uint32_t index=f.r[2];
    if(index>=3 || !field(owner,0x48d0,4) || word(owner+0x48d0)!=index ||
       !field(owner,0x48c0+index*4,4) || !word(owner+0x48cc) ||
       word(owner+0x48cc)!=word(owner+0x48c0+index*4)) {
        if(seen(binding_count)) {DrawRejection d{};d.reason=7;d.index=index;remember_rejection(d);}
        trace_present(PMetadata,f);return;
    }
    // beginFrame latches parallel mode and increments the producer serial;
    // executeFrame uses producer index XOR parallel, i.e. one frame behind.
    const uint32_t resource=word(owner+0x48cc);
    const uint32_t image=field(resource,0x3c,4)?word(resource+0x3c):0;
    if(!image) {trace_present(PImage,f);DrawRejection d{};d.reason=7;d.index=index;remember_rejection(d);return;}
    Presentation p{seen(draw_cycle),frame^parallel,owner,f.r[12],f.r[1],f.r[2],word(sr+0x33f50)-parallel,
        image,surface_texture(indirect(resource,0x204))};
    if(presentation.publish(p)) {trace_present(PPublished,f);__atomic_store_n(&present_pending,1,__ATOMIC_RELEASE);}
    else {trace_present(PConflict,f);count(render_faults);mark_overflow(p.frame,p.serial);}
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
    const auto requested=mode.preferences();
    const bool latched=c->depth?force(c):requested.force && forcing_available();
    const uint8_t multiplier=c->depth?c->scopes[0].multiplier:requested.multiplier;
    auto& s=c->scopes[c->depth++];s={};s.kind=kind;s.caller=f->r[13];s.sp=f->caller_sp();s.force=latched;
    s.multiplier=multiplier;
    s.subject=f->r[0];
    if(kind==12) {
        s.quantity_done=c->quantity_ui==s.subject;
        if(s.multiplier!=1 && !s.quantity_done && field(s.subject,0x5c,24)) {
            s.quantity_ready=true;s.player_blank=true;
            for(unsigned page=0;page<3;++page) {
                const unsigned offset=0x5c+page*8;
                auto& q=s.quantity_pages[page];
                q={word(s.subject+offset),word(s.subject+offset+4)};
                Reward before[first_screen_capacity]{};
                if(q.count>player_page_capacities[page] || (q.count &&
                   (q.array%4 || !writable_rewards(q.array,q.count*4) || !copy(q.array,before,q.count*4)))) {
                    s.quantity_ready=false;break;
                }
                for(unsigned i=0;i<q.count;++i)
                    s.player_blank=s.player_blank && !before[i].item && !before[i].amount;
            }
        }
        invalidate_highlights();
        s.epoch=++c->serial;s.ui=s.subject;
        // State 1 resizes first, then calls this builder inside the SAME paired
        // update (native BL at 0x384fc0). Its empty pre-generation snapshot is
        // superseded by this newly verified batch, not a copy of old rewards.
        // Different UI objects retain their independent relocation checks.
        Scope* refresh=find(*c,15);
        if(refresh && refresh->subject==s.subject) {
            refresh->array=0;refresh->pending_count=0;refresh->incomplete=false;
        }
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
        if(c->quantity_ui==s.subject)c->quantity_ui=0;
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
    Scope s=c->scopes[--c->depth];
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
        multiply_player_pages(s);
        c->quantity_ui=s.ui;
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
            if(!valid)mapping_detail.publish({0,0,0,3});
            for(unsigned i=0;i<s.pending_count && valid;++i) {
                const auto& r=s.pending[i];Reward contents[8]{};
                const unsigned offset=r.epoch-s.array;
                valid=uint64_t(destination)+offset+r.rewards.count*4<=0x100000000ull &&
                    copy(destination+offset,contents,r.rewards.count*4);
                if(!valid)mapping_detail.publish({offset/4,0,0,3});
                for(unsigned j=0;j<r.rewards.count && valid;++j) {
                    valid=contents[j].item==r.rewards.items[j].item && contents[j].amount==r.rewards.items[j].amount;
                    if(!valid)mapping_detail.publish({offset/4+j,
                        uint32_t(r.rewards.items[j].item)|(uint32_t(r.rewards.items[j].amount)<<16),
                        uint32_t(contents[j].item)|(uint32_t(contents[j].amount)<<16),1});
                }
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
            mapping_detail.publish({0,0,0,3});
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
Preferences requested_preferences() { return mode.preferences(); }
void request_preferences(Preferences p) { mode.set(p); }
bool forcing_available() { return __atomic_load_n(&pair_ready,__ATOMIC_ACQUIRE) &&
                                 __atomic_load_n(&capture_ready,__ATOMIC_ACQUIRE); }
template<class ReportType> static void install_failure(const char* feature,const ReportType& r) {
    static const char* const reasons[]={"unavailable", "wrong game", "unreadable address", "signature or conflicting patch", "write failed", "cache synchronization failed", "readback failed", "external patch changed"};
    const unsigned reason=unsigned(r.failure);
    forge_log_warn("[please-do-better] %s unavailable: %s (%s); remove conflicting mods, verify game/Forge, then restart",feature,
                   reason<8?reasons[reason]:"native resource failure",r.state==State::Unsafe?"unsafe restore; arena retained":"safely disabled");
}
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
    if(r.state!=State::Applied) {install_failure("Luck hooks",r);return;}
    __atomic_store_n(&pair_ready,1,__ATOMIC_RELEASE);
    if(nnosAllocateTlsSlot(&tls,nullptr) || tls<0) {tls=-1;lost();forge_log_warn("[please-do-better] Reward capture TLS unavailable; reduce loaded plugins and restart");return;}
    Hook taps[20];for(unsigned i=0;i<20;++i)taps[i]=hook(i+2);
    const auto v=visual.install(base,taps,20);
    if(v.state==State::Applied)__atomic_store_n(&capture_ready,1,__ATOMIC_RELEASE);
    if(v.state!=State::Applied) {install_failure("Reward capture hooks",v);return;}
    Hook rendering[2]={highlight_boundary_recipe(),presentation_recipe()};
    const auto h=highlight.install(base,rendering,2);
    if(h.state==State::Applied)__atomic_store_n(&highlight_ready,1,__ATOMIC_RELEASE);
    else install_failure("Highlight hooks",h);
}
static Record observed[8][8]{};
static Record displayed[8][8]{};
static uint32_t epochs[8]{}, owners[8]{}, latest_tier=0, bonus_count=0;
static uint32_t generated_count, summary_status, summary_order, summary_records;
void update() {
    count(update_hits);
    static mod_log::Once quantity_reported;
    static const char* const reasons[]={"", "unwritable or unsupported reward array", "invalid item/amount record",
        "quantity exceeds the native signed limit", "no fresh first-screen generation", "reward snapshot changed", "invalid multiplier"};
    const unsigned faults=seen(quantity_faults);
    for(unsigned reason=1;reason<7;++reason)if((faults&(1u<<reason)) && quantity_reported.claim(reason))
        forge_log_warn("[please-do-better] Multiplier skipped: %s; quantities retained. Restart if persistent.",reasons[reason]);
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
                    else {
                        for(unsigned j=0;j<source.rewards.count;++j)
                            if(source.rewards.items[j].item!=r.rewards.items[offset/4+j].item ||
                               source.rewards.items[j].amount!=r.rewards.items[offset/4+j].amount) {
                                mapping_detail.publish({offset/4+j,
                                    uint32_t(source.rewards.items[j].item)|(uint32_t(source.rewards.items[j].amount)<<16),
                                    uint32_t(r.rewards.items[offset/4+j].item)|(uint32_t(r.rewards.items[offset/4+j].amount)<<16),2});break;
                            }
                        source={};lost();count(mapping_faults);
                    }
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
void diagnostics() {} // Kept for source compatibility; settings UI has no diagnostics.
const char* startup_status() {
    return forcing_available() ? (seen(highlight_ready) ? "forcing and highlights ready" : "forcing ready; highlights unavailable") : "forcing unavailable";
}

void render() {
    count(render_gates[REnter]);
    report_draw_rejection();
    static mod_log::Once failures;
    if(seen(mapping_faults) && failures.claim(0)) forge_log_warn("[please-do-better] Reward mapping incomplete; uncertain markers suppressed; restart if persistent");
    if(seen(render_faults) && failures.claim(1)) forge_log_warn("[please-do-better] Highlight capture incomplete; uncertain markers suppressed; restart if persistent");
    __atomic_store_n(&highlighted_count,0,__ATOMIC_RELAXED);
    const uint32_t cycle=__atomic_fetch_add(&draw_cycle,1,__ATOMIC_SEQ_CST);
    Presentation p{};
    if(!seen(highlight_ready)) {count(render_gates[RDisabled]);return;}
    if(!__atomic_exchange_n(&present_pending,0,__ATOMIC_ACQ_REL)) {count(render_gates[RPending]);return;}
    if(!presentation.read(p)) {count(render_gates[RSnapshot]);return;}
    if(p.cycle!=cycle) {count(render_gates[RCycle]);return;}
    if(seen(frame_overflow[p.frame])==p.serial+1) {count(render_gates[ROverflow]);return;}
    ImGuiIO* io=igGetIO_Nil();
    if(!io || io->DisplaySize.x<=0 || io->DisplaySize.y<=0) {count(render_gates[RIO]);return;}
    ImDrawList* draw=igGetBackgroundDrawList_Nil();if(!draw) {count(render_gates[RDrawList]);return;}
    // Triangle wave: two-second period, 0.45..0.75 alpha, no animation RNG.
    const float now=float(igGetTime());if(!std::isfinite(now) || now<0 || now>4294967296.f) {count(render_gates[RTime]);return;}
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
        if(!geometries[sample].read(g))continue;
        count(render_gates[RSample]);
        if(g.frame!=p.frame || g.owner!=p.owner || g.serial!=p.serial) {count(render_gates[RFrame]);continue;}
        if(std::fabs(g.width-io->DisplaySize.x)>.5f || std::fabs(g.height-io->DisplaySize.y)>.5f) {
            count(render_gates[RDimensions]);continue;
        }
        unsigned matched=64;
        for(unsigned i=0;i<bound;++i)if(valid[i] && !drawn[i] && current[i].node==g.binding.node &&
            !std::memcmp(&current[i],&g.binding,sizeof(Binding))) {matched=i;break;}
        if(matched==64) {count(render_gates[RBinding]);continue;}
        if(seen(live_fence)!=fence) {count(render_gates[REpoch]);return;}
        // This is our own Forge overlay, like Damage Numbers. The original
        // full-viewport GUI shader has already projected this exact live slot
        // into framebuffer pixels. Forge submits our primitive to the selected
        // acquired image; its identity need not equal the game's UI texture.
        // Batch/node/fence, executed frame, full viewport and clip remain guarded.
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
        ImDrawList_PopClipRect(draw);++rendered;count(render_gates[RDrawn]);
    }
    __atomic_store_n(&highlighted_count,rendered,__ATOMIC_RELAXED);
}
}
