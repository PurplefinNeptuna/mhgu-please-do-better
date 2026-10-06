#include "preferences.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <initializer_list>
using namespace pdb;
struct Files {
    PreferencesText files[2]{};
    bool available=true;
    unsigned mounts=0,writes=0,commits=0,fail_write=0,fail_commit=0;
    bool mount(){if(!available)return false;++mounts;return true;}
    void unmount(){assert(mounts==1);--mounts;}
    bool read(unsigned n,PreferencesText& out){out=files[n];return out.size!=0;}
    bool write(unsigned n,PreferencesText p){if(++writes==fail_write)return false;files[n]=p;return true;}
    bool commit(){return ++commits!=fail_commit;}
};
int main(){
    unsigned checks=0;
    for(bool force:{false,true}) {
        auto t=encode_preferences({force});Preferences p{};
        assert(decode_preferences(t.bytes,t.size,p)&&p.force==force);++checks;
        for(unsigned i=0;i<t.size;++i){t.bytes[i]^=2;assert(!decode_preferences(t.bytes,t.size,p));t.bytes[i]^=2;++checks;}
        assert(!decode_preferences(t.bytes,t.size-1,p));++checks;
    }
    {Files f;PreferenceStore<Files>s;Preferences p{};assert(!s.load(f,p)&&!p.force&&!s.pending&&!f.mounts);++checks;}
    {Files f;f.available=false;PreferenceStore<Files>s;Preferences p{};
     assert(!s.load(f,p)&&s.pending);s.changed();f.available=true;f.files[0]=encode_preferences({true});
     assert(!s.load(f,p)&&!p.force);++checks;}
    for(unsigned source=0;source<2;++source){Files f;f.files[source]=encode_preferences({true});PreferenceStore<Files>s;Preferences p{};
     assert(s.load(f,p)&&p.force&&!s.pending&&!f.mounts);++checks;}
    for(unsigned failure=0;failure<5;++failure){Files f;f.files[0]=encode_preferences({false});PreferenceStore<Files>s;
     if(failure==1)f.available=false;
     if(failure==2)f.fail_write=1;
     if(failure==3)f.fail_write=2;
     if(failure==4)f.fail_commit=2;
     const bool ok=s.save(f,{true});assert(ok==(failure==0));assert(!f.mounts&&!s.pending);
     Preferences p{};assert(decode_preferences(f.files[0].bytes,f.files[0].size,p)&&p.force==ok);++checks;}
    {Files f;PreferenceStore<Files>s;assert(s.save(f,{true}));Preferences p{};
     assert(decode_preferences(f.files[1].bytes,f.files[1].size,p)&&!p.force&&f.commits==2);++checks;}
    {Files f;f.files[1]=encode_preferences({true});PreferenceStore<Files>s;f.fail_write=2;
     assert(!s.save(f,{false}));Preferences p{};assert(decode_preferences(f.files[0].bytes,f.files[0].size,p)&&p.force);++checks;}
    {Files f;f.files[0]=encode_preferences({false});PreferenceStore<Files>s;f.fail_commit=2;f.fail_write=3;
     assert(!s.save(f,{true})&&!f.mounts);assert(strstr(s.status,"recovery uncertain"));++checks;}
    printf("PASS: %u settings format, delayed-load and recovery checks\n",checks);
}
