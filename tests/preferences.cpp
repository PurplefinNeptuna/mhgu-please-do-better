#include "preferences.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <initializer_list>
using namespace pdb;
struct Files {
    PreferencesText primary{};
    const char* legacy_backup="legacy backup stays untouched";
    bool available=true,fail_write=false,fail_commit=false,fail_verify=false;
    unsigned mounts=0,writes=0,commits=0,reads=0;
    bool mount(){if(!available)return false;++mounts;return true;}
    void unmount(){assert(mounts==1);--mounts;}
    bool read(unsigned n,PreferencesText& out){assert(n==0);++reads;out=primary;return out.size!=0;}
    bool write(unsigned n,PreferencesText p){assert(n==0);++writes;if(fail_write){primary.size=1;primary.bytes[0]='!';return false;}primary=p;return !fail_verify;}
    bool commit(){++commits;return !fail_commit;}
};
int main(){
    unsigned checks=0;
    for(bool force:{false,true}) {
        auto t=encode_preferences({force});Preferences p{};
        assert(!strstr(t.bytes,"version="));++checks;
        assert(decode_preferences(t.bytes,t.size,p)&&p.force==force);++checks;
        for(unsigned i=0;i<t.size;++i){t.bytes[i]^=2;assert(!decode_preferences(t.bytes,t.size,p));t.bytes[i]^=2;++checks;}
        assert(!decode_preferences(t.bytes,t.size-1,p));++checks;
        char legacy[64];snprintf(legacy,sizeof(legacy),"version=2\nforce_miraculous=%u\n",unsigned(force));
        assert(decode_preferences(legacy,unsigned(strlen(legacy)),p)&&p.force==force);++checks;
        legacy[8]='1';assert(!decode_preferences(legacy,unsigned(strlen(legacy)),p));++checks;
        assert(!decode_preferences(t.bytes,sizeof(t.bytes),p));++checks;
    }
    {Files f;PreferenceStore<Files>s;Preferences p{};assert(!s.load(f,p)&&!p.force&&!s.pending&&!f.mounts);assert(f.writes==0);++checks;}
    {Files f;f.available=false;PreferenceStore<Files>s;Preferences p{};
     assert(!s.load(f,p)&&s.pending);s.changed();f.available=true;f.primary=encode_preferences({true});
     assert(!s.load(f,p)&&!p.force);++checks;}
    {Files f;f.primary=encode_preferences({true});PreferenceStore<Files>s;Preferences p{};
     assert(s.load(f,p)&&p.force&&!s.pending&&!f.mounts);++checks;}
    for(bool force:{false,true}) {Files f;PreferenceStore<Files>s;Preferences p{};
     snprintf(f.primary.bytes,sizeof(f.primary.bytes),"version=2\nforce_miraculous=%u\n",unsigned(force));
     f.primary.size=strlen(f.primary.bytes);
     assert(s.load(f,p)&&p.force==force&&!f.mounts);++checks;
     assert(s.save(f,p)&&!strstr(f.primary.bytes,"version=")&&!f.mounts);++checks;
     PreferenceStore<Files> restart;Preferences loaded{};
     assert(restart.load(f,loaded)&&loaded.force==force&&!f.mounts);++checks;}
    {Files f;f.primary.size=1;f.primary.bytes[0]='!';PreferenceStore<Files>s;Preferences p{};
     assert(!s.load(f,p)&&!p.force&&f.reads==1&&f.writes==0);++checks;}
    for(unsigned failure=0;failure<5;++failure){Files f;f.primary=encode_preferences({false});PreferenceStore<Files>s;
     if(failure==1)f.available=false;
     if(failure==2)f.fail_write=true;
     if(failure==3)f.fail_verify=true;
     if(failure==4)f.fail_commit=true;
     const bool ok=s.save(f,{true});assert(ok==(failure==0));assert(!f.mounts&&!s.pending);
     assert(f.writes==(failure==1?0:1));assert(strcmp(f.legacy_backup,"legacy backup stays untouched")==0);
     assert(ok||strstr(s.status,"session choice retained"));++checks;}
    {Files f;PreferenceStore<Files>s;assert(s.save(f,{true})&&s.save(f,{false}));Preferences p{};
     assert(decode_preferences(f.primary.bytes,f.primary.size,p)&&!p.force&&f.commits==2&&f.writes==2);++checks;}
    printf("PASS: %u primary-only format, delayed-load and failure checks\n",checks);
}
