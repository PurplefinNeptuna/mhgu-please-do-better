#pragma once
#include <cstdint>
#include <cstring>
#include <type_traits>

namespace pdb {
// One producer per native TLS context and one render consumer. Every payload
// word is atomic: overwrite during a read cannot create a C++ data race.
// Sequential consistency makes the two ticket checks detect a torn snapshot.
// There is no wait, lock or retry in publish/read; overflow discards oldest.
template<class T, unsigned Capacity> class Mailbox {
    static_assert(Capacity > 0 && Capacity < 0x40000000u);
    static_assert((Capacity & (Capacity-1)) == 0, "Power-of-two capacity keeps wrap indexing continuous");
    static_assert(std::is_trivially_copyable<T>::value);
    static_assert(__atomic_always_lock_free(4, nullptr));
    static constexpr unsigned words = (sizeof(T)+3)/4;
    struct Slot { uint32_t ticket = 0, data[words]{}; };
    Slot slots[Capacity]{};
    uint32_t sequence = 0, published = 0, cursor = 0;
public:
    uint32_t overwritten = 0; // consumer-owned diagnostics
    constexpr explicit Mailbox(uint32_t initial = 0)
        : sequence(initial), published(initial), cursor(initial) {}
    void publish(const T& value) {
        const uint32_t next = sequence+1;
        uint32_t bits[words]{};
        std::memcpy(bits, &value, sizeof(value));
        Slot& s = slots[(next-1)%Capacity];
        __atomic_store_n(&s.ticket, (next<<1)|1, __ATOMIC_SEQ_CST);
        for (unsigned i=0; i<words; ++i)
            __atomic_store_n(&s.data[i], bits[i], __ATOMIC_SEQ_CST);
        __atomic_store_n(&s.ticket, next<<1, __ATOMIC_SEQ_CST);
        sequence = next;
        __atomic_store_n(&published, next, __ATOMIC_SEQ_CST);
    }
    bool read(T& out) {
        const uint32_t head = __atomic_load_n(&published, __ATOMIC_SEQ_CST);
        if (head == cursor) return false;
        if (head-cursor > Capacity) {
            overwritten += head-cursor-Capacity;
            cursor = head-Capacity;
        }
        const uint32_t next = cursor+1, expected = next<<1;
        Slot& s = slots[(next-1)%Capacity];
        const uint32_t ticket = __atomic_load_n(&s.ticket, __ATOMIC_SEQ_CST);
        cursor = next;
        if (ticket != expected) { ++overwritten; return false; }
        uint32_t bits[words];
        for (unsigned i=0; i<words; ++i)
            bits[i] = __atomic_load_n(&s.data[i], __ATOMIC_SEQ_CST);
        if (__atomic_load_n(&s.ticket, __ATOMIC_SEQ_CST) != expected) {
            ++overwritten; return false;
        }
        std::memcpy(&out, bits, sizeof(out));
        return true;
    }
};
} // namespace pdb
