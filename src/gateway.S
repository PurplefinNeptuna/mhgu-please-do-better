.syntax unified
.arm
.fpu crypto-neon-fp-armv8
.hidden pdb_gateway_dispatch
.hidden pdb_gateway_leave

/* Save before executing any flag-changing instruction. The 328-byte frame
 * keeps native stack arguments at their original address and 8-byte alignment.
 * All d0-d31 are saved because taps can occur inside hard-VFP native routines.
 */
.macro SAVE
    push {r0-r12, lr}
    vpush {d0-d15}
    vpush {d16-d31}
    mrs r2, cpsr
    vmrs r3, fpscr
    push {r2, r3}
    sub sp, sp, #8
.endm
.macro RESTORE
    str r0, [sp]
    ldr r2, [sp, #8]
    ldr r3, [sp, #12]
    /* Helpers and their complete callees must leave GE unchanged. Restore
     * NZCVQ only; the compiled binary audit rejects every GE-writing opcode. */
    msr APSR_nzcvq, r2
    vmsr fpscr, r3
    add sp, sp, #16
    vpop {d16-d31}
    vpop {d0-d15}
    pop {r0-r12, lr}
    ldr pc, [sp, #-328]
.endm
.macro ENTRY id, helper
    .section .text.pdb_gateway_\id,"ax",%progbits
    .balign 4
    .global pdb_gateway_\id
    .hidden pdb_gateway_\id
    .type pdb_gateway_\id,%function
pdb_gateway_\id:
    SAVE
    mov r0, #\id
    mov r1, sp
    mov r4, sp
    bic sp, sp, #7
    bl \helper
    mov sp, r4
    RESTORE
    .size pdb_gateway_\id, .-pdb_gateway_\id
.endm
ENTRY 0, pdb_gateway_dispatch
ENTRY 1, pdb_gateway_dispatch
ENTRY 2, pdb_gateway_dispatch
ENTRY 3, pdb_gateway_dispatch
ENTRY 4, pdb_gateway_dispatch
ENTRY 5, pdb_gateway_dispatch
ENTRY 6, pdb_gateway_dispatch
ENTRY 7, pdb_gateway_dispatch
ENTRY 8, pdb_gateway_dispatch
ENTRY 9, pdb_gateway_dispatch
ENTRY 10, pdb_gateway_dispatch
ENTRY 11, pdb_gateway_dispatch
ENTRY 12, pdb_gateway_dispatch
ENTRY 13, pdb_gateway_dispatch
ENTRY 14, pdb_gateway_dispatch
ENTRY 15, pdb_gateway_dispatch
ENTRY 16, pdb_gateway_dispatch
ENTRY 19, pdb_gateway_dispatch
ENTRY 20, pdb_gateway_dispatch
ENTRY 21, pdb_gateway_dispatch
ENTRY 22, pdb_gateway_dispatch
ENTRY 23, pdb_gateway_dispatch
ENTRY 24, pdb_gateway_dispatch
ENTRY 25, pdb_gateway_dispatch
ENTRY 26, pdb_gateway_dispatch
ENTRY 27, pdb_gateway_dispatch
.section .text.pdb_gateway_after,"ax",%progbits
.balign 4
.global pdb_gateway_after
.hidden pdb_gateway_after
.type pdb_gateway_after,%function
pdb_gateway_after:
 SAVE
 mov r0, sp
 mov r4, sp
 bic sp, sp, #7
 bl pdb_gateway_leave
 mov sp, r4
 RESTORE
.size pdb_gateway_after, .-pdb_gateway_after
.section .note.GNU-stack,"",%progbits
