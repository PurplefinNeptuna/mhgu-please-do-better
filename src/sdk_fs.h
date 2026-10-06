#pragma once
#include <cstdint>
// Pinned ARM32 SDK exports: FileHandle is one 32-bit pointer, Result is r0,
// file offsets are aligned 64-bit arguments, byte counts are 32-bit size_t.
// The generic nnheaders copy describes ARM64 handles and is unsuitable here.
extern "C" {
void pdb_fs_disable_abort(uint32_t*) asm("_ZN2nn2fs23ScopedAutoAbortDisablerC1Ev");
void pdb_fs_restore_context(uint32_t) asm("_ZN2nn2fs25SetCurrentThreadFsContextEPKNS0_9FsContextE");
uint32_t pdb_fs_commit(const char*) asm("_ZN2nn2fs14CommitSaveDataEPKc");
uint32_t pdb_fs_open(uint32_t*,const char*,int) asm("_ZN2nn2fs8OpenFileEPNS0_10FileHandleEPKci");
void pdb_fs_close(uint32_t) asm("_ZN2nn2fs9CloseFileENS0_10FileHandleE");
uint32_t pdb_fs_size(int64_t*,uint32_t) asm("_ZN2nn2fs11GetFileSizeEPxNS0_10FileHandleE");
uint32_t pdb_fs_read(uint32_t,int64_t,void*,uint32_t) asm("_ZN2nn2fs8ReadFileENS0_10FileHandleExPvj");
uint32_t pdb_fs_write(uint32_t,int64_t,const void*,uint32_t,const uint32_t*) asm("_ZN2nn2fs9WriteFileENS0_10FileHandleExPKvjRKNS0_11WriteOptionE");
uint32_t pdb_fs_flush(uint32_t) asm("_ZN2nn2fs9FlushFileENS0_10FileHandleE");
uint32_t pdb_fs_resize(uint32_t,int64_t) asm("_ZN2nn2fs11SetFileSizeENS0_10FileHandleEx");
uint32_t pdb_fs_create(const char*,int64_t) asm("_ZN2nn2fs10CreateFileEPKcx");
}
namespace pdb {
class FsAbortGuard {
    uint32_t previous=0;
public:
    FsAbortGuard() { pdb_fs_disable_abort(&previous); }
    ~FsAbortGuard() { pdb_fs_restore_context(previous); }
    FsAbortGuard(const FsAbortGuard&)=delete;
    FsAbortGuard& operator=(const FsAbortGuard&)=delete;
};
}
