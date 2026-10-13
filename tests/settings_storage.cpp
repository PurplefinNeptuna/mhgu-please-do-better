// Execute production persistence against a recording filesystem, without game saves.
#include <cassert>
#include <string>
#include <cstring>
#include <cstdio>
#include <cstdarg>
#include "../src/settings.cpp"
static std::string primary, backup="untouched legacy backup";
static bool exists=false, available=true;
static unsigned failure=0, mounts=0, handles=0, guards=0, accesses=0, commits=0;
bool forge_fs_mountSaveData(){if(!available)return false;++mounts;return true;}
void forge_fs_unmountSaveData(){assert(mounts==1);--mounts;}
void forge_log_warn(const char*,...){}
void forge_log_info(const char*,...){}
extern "C" {
void pdb_fs_disable_abort(uint32_t* p){*p=42;++guards;}
void pdb_fs_restore_context(uint32_t p){assert(p==42&&guards==1);--guards;}
uint32_t pdb_fs_open(uint32_t* h,const char* p,int mode){assert(std::strcmp(p,"savedata:/please_do_better.ini")==0);++accesses;if(!exists)return 1;assert(!handles);*h=++handles;if(mode==1&&failure==7){--handles;return 1;}return 0;}
void pdb_fs_close(uint32_t h){assert(h==1&&handles==1);--handles;}
uint32_t pdb_fs_size(int64_t* n,uint32_t){*n=primary.size();return failure==8;}
uint32_t pdb_fs_read(uint32_t,int64_t,void* p,uint32_t n){std::memcpy(p,primary.data(),n);if(failure==5&&n)static_cast<char*>(p)[0]='!';return failure==4;}
uint32_t pdb_fs_create(const char* p,int64_t n){assert(std::strcmp(p,"savedata:/please_do_better.ini")==0);++accesses;if(failure==9)return 1;exists=true;primary.resize(n);return 0;}
uint32_t pdb_fs_resize(uint32_t,int64_t n){primary.resize(n);return failure==1;}
uint32_t pdb_fs_write(uint32_t,int64_t,const void* p,uint32_t n,const uint32_t* f){assert(*f==1);primary.assign(static_cast<const char*>(p),failure==2?1:n);return failure==2;}
uint32_t pdb_fs_flush(uint32_t){return failure==3;}
uint32_t pdb_fs_commit(const char* p){assert(std::strcmp(p,"savedata")==0);++commits;return failure==6;}
}
static void balanced(){assert(!mounts&&!handles&&!guards&&backup=="untouched legacy backup");}
int main(){using namespace pdb;
 Preferences session{true,5};assert(save_preferences(session));balanced();assert(exists&&primary.find("version=")==std::string::npos);
 Preferences restarted{};store.pending=true;assert(load_preferences(restarted)&&restarted.force&&restarted.multiplier==5);balanced();
 for(unsigned bits=0;bits<10;++bits) {
  Preferences wanted{bool(bits&1),uint8_t(bits/2+1)},loaded{};
  assert(save_preferences(wanted));store.pending=true;
  assert(load_preferences(loaded)&&loaded.force==wanted.force&&loaded.multiplier==wanted.multiplier);balanced();
 }
 for(const char* old:{"version=2\nforce_miraculous=1\n","force_miraculous=1\ndouble_quantity=1\n",
                     "force_miraculous=1\nreward_multiplier=5\n"}) {
  primary=old;Preferences defaults{};store.pending=true;
  assert(!load_preferences(defaults)&&!defaults.force&&defaults.multiplier==1&&primary==old);balanced();
 }
 session.force=false;assert(save_preferences(session)&&save_preferences(session));balanced();
 for(failure=1;failure<=9;++failure){exists=failure!=9;assert(!save_preferences(session));balanced();assert(!session.force&&session.multiplier==5&&std::strstr(preferences_status(),"session"));}
 failure=0;available=false;assert(!save_preferences(session));balanced();available=true;
 exists=true;primary="invalid primary";Preferences defaults{};store.pending=true;assert(!load_preferences(defaults)&&!defaults.force);balanced();
 exists=false;store.pending=true;assert(!load_preferences(defaults));balanced();
 assert(save_preferences({true}));Preferences again{};store.pending=true;assert(load_preferences(again)&&again.force);balanced();
 std::printf("PASS: production primary-only persistence, versionless restart/repeated saves, ignored legacy settings, ignored backup, invalid primary and nine storage failures (%u accesses, %u commits)\n",accesses,commits);
}
