#include "log_policy.h"
#include <atomic>
#include <thread>
#include <cassert>
int main() {
    mod_log::Once once;
    for(unsigned reason=0;reason<32;++reason) {
        assert(once.claim(reason));
        for(unsigned i=0;i<1000;++i) assert(!once.claim(reason));
    }
    assert(!once.claim(32) && !once.claim(0xffffffffu));
    mod_log::Once concurrent;std::atomic<unsigned> reports{0};std::thread threads[16];
    for(auto& thread:threads)thread=std::thread([&] {
        for(unsigned i=0;i<1000;++i)for(unsigned reason=0;reason<32;++reason)
            if(concurrent.claim(reason))++reports;
    });
    for(auto& thread:threads)thread.join();
    assert(reports==32);
}
