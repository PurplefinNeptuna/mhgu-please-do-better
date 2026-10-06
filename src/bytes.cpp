#include <stddef.h>
// Gateway callbacks must have an auditable GE-preserving call graph. Keep the
// compiler's aggregate copies local rather than calling a platform libc body.
extern "C" void* memcpy(void* out,const void* in,size_t n) {
    auto* d=static_cast<volatile unsigned char*>(out);
    auto* s=static_cast<volatile const unsigned char*>(in);
    for(size_t i=0;i<n;++i)d[i]=s[i];
    return out;
}
extern "C" void* memset(void* out,int value,size_t n) {
    auto* d=static_cast<volatile unsigned char*>(out);
    for(size_t i=0;i<n;++i)d[i]=static_cast<unsigned char>(value);
    return out;
}
