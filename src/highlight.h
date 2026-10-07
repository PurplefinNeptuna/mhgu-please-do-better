#pragma once
#include <cstdint>
#include <cstring>
#include <cmath>
#include "attribution.h"
namespace pdb {
// Bounded immutable copies. Payload words are atomic, including during a
// rejected concurrent publication; no producer waits for another game thread.
template<class T> class Snapshot {
    uint32_t ticket=0, data[(sizeof(T)+3)/4]{};
public:
    bool publish(const T& value) {
        uint32_t prior=__atomic_load_n(&ticket,__ATOMIC_SEQ_CST);
        if((prior&1) || !__atomic_compare_exchange_n(&ticket,&prior,prior+1,false,__ATOMIC_SEQ_CST,__ATOMIC_SEQ_CST))return false;
        uint32_t bits[(sizeof(T)+3)/4]{};std::memcpy(bits,&value,sizeof(T));
        for(unsigned i=0;i<(sizeof(T)+3)/4;++i)__atomic_store_n(&data[i],bits[i],__ATOMIC_SEQ_CST);
        __atomic_store_n(&ticket,prior+2,__ATOMIC_SEQ_CST);return true;
    }
    bool read(T& value) const {
        const uint32_t before=__atomic_load_n(&ticket,__ATOMIC_SEQ_CST);
        if(!before || (before&1))return false;
        uint32_t bits[(sizeof(T)+3)/4]{};
        for(unsigned i=0;i<(sizeof(T)+3)/4;++i)bits[i]=__atomic_load_n(&data[i],__ATOMIC_SEQ_CST);
        if(before!=__atomic_load_n(&ticket,__ATOMIC_SEQ_CST))return false;
        std::memcpy(&value,bits,sizeof(T));return true;
    }
};
struct Binding {
    uint32_t fence=0,ui=0,batch=0,list=0,group=0,index=0,node=0,icon=0,id=0;
    Reward item{};
};
struct Geometry {
    Binding binding{};
    uint32_t cycle=0,frame=0,owner=0,serial=0;
    float width=0,height=0,points[8]{},clip[4]{};
    uint32_t surface=0,texture=0; // Zero texture denotes the default sentinel.
};
struct Presentation { uint32_t cycle=0,frame=0,owner=0,queue=0,window=0,index=0,serial=0,texture=0,default_texture=0; };
inline bool frame_layout(uint32_t group,uint32_t icon_root,uint32_t background_root,
                         unsigned index,unsigned icon_index,unsigned& frame_index,unsigned& frame_id) {
    if(index>=48)return false;
    const unsigned row=index/8,column=index%8;
    if((group==1 || group==7) && icon_root==19 && background_root==12 && icon_index==2+9*row+column) {
        frame_index=4+9*row+column;frame_id=8+9*row+column;return true;
    }
    if(group==2 && icon_root==43 && background_root==44 && index<32 && icon_index==2+9*row+column) {
        frame_index=6+9*row+column;frame_id=(row==0?64:row==1?17:row==2?35:44)+column;return true;
    }
    if((group==5 || group==6) && icon_root==66 && background_root==65 && index<16 && icon_index==2+9*row+column) {
        frame_index=4+9*row+column;frame_id=(row?17:64)+column;return true;
    }
    return false;
}
// Exact XY path of the pinned FGUICalcPosition2D vertex programs. z is retained
// in the model transform; their depth projection has no influence on XY/W=1.
inline bool screen_quad(const float vertices[24],const float model[16],const float global[4],
                        float width,float height,float out[8]) {
    if(!std::isfinite(width) || !std::isfinite(height) || width<=0 || height<=0 || width>16384 || height>16384)return false;
    for(unsigned i=0;i<16;++i)if(!std::isfinite(model[i]))return false;
    for(unsigned i=0;i<4;++i)if(!std::isfinite(global[i]))return false;
    for(unsigned i=0;i<4;++i) {
        const float x=vertices[i*6],y=vertices[i*6+1],z=vertices[i*6+2];
        if(!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z))return false;
        const float cx=(model[0]*x+model[4]*y+model[8]*z+model[12])*global[0]+global[2];
        const float cy=(model[1]*x+model[5]*y+model[9]*z+model[13])*global[1]+global[3];
        out[i*2]=(cx+1)*width*.5f;out[i*2+1]=(1-cy)*height*.5f;
        if(!std::isfinite(out[i*2]) || !std::isfinite(out[i*2+1]) ||
           std::fabs(out[i*2])>65536 || std::fabs(out[i*2+1])>65536)return false;
    }
    const float area=(out[2]-out[0])*(out[5]-out[1])-(out[3]-out[1])*(out[4]-out[0]);
    return std::isfinite(area) && std::fabs(area)>1;
}
}
