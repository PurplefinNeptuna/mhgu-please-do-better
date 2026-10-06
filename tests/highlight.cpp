#include "highlight.h"
#include <cassert>
#include <cstdio>
#include <thread>
#include <initializer_list>
using namespace pdb;
int main() {
    unsigned checks=0,fi=0,id=0;
    for(unsigned group:{1u,2u,5u,6u,7u})for(unsigned index=0;index<48;++index) {
        unsigned ir=group==2?43:group==5||group==6?66:19;
        unsigned br=group==2?44:group==5||group==6?65:12;
        bool allowed=index<(group==2?32:group==5||group==6?16:48);
        assert(frame_layout(group,ir,br,index,2+index/8*9+index%8,fi,id)==allowed);++checks;
        assert(!frame_layout(group,ir+1,br,index,2+index/8*9+index%8,fi,id));++checks;
        assert(!frame_layout(group,ir,br,index,3+index/8*9+index%8,fi,id));++checks;
    }
    float v[24]{},m[16]{},g[4]={2.f/1280,2.f/720,-1,1},out[8];
    m[0]=m[5]=m[10]=m[15]=1;m[12]=100;m[13]=-50;
    for(unsigned k=0;k<4;++k) {v[k*6]=(k&1)?36:0;v[k*6+1]=(k&2)?-36:0;}
    for(float scale:{.5f,1.f,2.f}) {
        assert(screen_quad(v,m,g,1280*scale,720*scale,out));
        for(unsigned k=0;k<4;++k) {assert(std::fabs(out[k*2]-(100+((k&1)?36:0))*scale)<.001f);assert(std::fabs(out[k*2+1]-(50+((k&2)?36:0))*scale)<.001f);}++checks;
    }
    v[0]=NAN;assert(!screen_quad(v,m,g,1280,720,out));++checks;v[0]=0;
    assert(!screen_quad(v,m,g,0,720,out));++checks;
    m[5]=0;assert(!screen_quad(v,m,g,1280,720,out));++checks;
    Snapshot<Binding> s;Binding b{};assert(!s.read(b));++checks;
    // A producer and consumer never expose a torn pair even with reordered
    // publication attempts. Atomic payload words avoid undefined data races.
    std::thread writer([&] {for(unsigned i=1;i<100000;++i){Binding value{};value.batch=i;value.index=~i;assert(s.publish(value));}});
    for(unsigned i=0;i<100000;++i)if(s.read(b)){assert(b.index==~b.batch);++checks;}
    writer.join();assert(s.read(b)&&b.batch==99999);++checks;
    printf("PASS: %u layout/transform/immutable-publication checks\n",checks);
}
