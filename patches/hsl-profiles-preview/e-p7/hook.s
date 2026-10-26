/* Original E142/1100 T24.1 v3. Reference method only: fishcu@539fcf1.
 * Image-owned requests keep v2 snapshot rules. Qualified compact headers
 * read one current profile byte; no settings writes or writable globals.
 */
.text
.balign 4
.global _start
_start:
    call ep7_selector,[d2,d3,a2,a3],20
selector_done:
    add -32,sp
    mov d0,(0,sp)
    mov d1,(4,sp)
    mov d2,(8,sp)
    mov a0,(12,sp)
    mov a1,(16,sp)
    mov a2,(20,sp)
    mov a3,(24,sp)
    mov psw,d0
    mov d0,(28,sp)
    mov d3,a2
    mov (4,a2),a3
    mov (8,a3),d0
    cmp 0x000b0000,d0
    bne finish
    mov (1524,a3),d0
    cmp 0,d0
    bne finish
    movhu (12,a3),d0
    cmp 0xf00d,d0
    beq finish
    mov (a3),d0
    cmp ep7_request_callback,d0
    bne finish
    mov (4,a3),a0
    cmp 0,a0
    beq finish
    mov (a0),a1
    mov a1,d0
    add 11364,d0
    cmp a3,d0
    bne finish
    mov a1,d0
    add 14576,d0
    mov 16,d2
record_check:
    cmp a0,d0
    beq record_ok
    add 56,d0
    add -1,d2
    bne record_check
    bra finish
record_ok:
    mov (4,a1),d0
    cmp ep7_owner_callback,d0
    beq owner_ok
    cmp ep7_alternate_owner_callback,d0
    beq owner_ok
    cmp ep7_compact_callback,d0
    beq compact
    cmp ep7_compact_secondary_callback,d0
    beq compact
    cmp 0,d0
    bne finish
    /* The third native compact constructor has a zeroed callback/owner. */
    mov (8,a1),d0
    cmp 0,d0
    bne finish
compact:
    movbu (ep7_current_profile),d0
    bra profile_ready
owner_ok:
    mov (8,a1),a0
    cmp 0,a0
    beq finish
    mov (28,a0),a0
    cmp 0,a0
    beq finish
    movbu (24053,a0),d0
    cmp 11,d0
    bne finish
    movbu (24083,a0),d0
profile_ready:
    add -1,d0
    cmp 3,d0
    bhi finish
    /* Clear every H/L halfword first, preserving native S and all LUTs.
     * Sparse 8-byte rows encode exactly the same 96 values as v2. */
    asl 3,d0
    mov profile_writes,a1
    add d0,a1
    mov (12,a2),a0
    add 706,a0
    clr d0
    mov 12,d2
clear_pair:
    movhu d0,(a0)
    movhu d0,(4,a0)
    add 24,a0
    add -1,d2
    bne clear_pair
    mov (12,a2),a0
    movhu (a1),d0
    movhu (2,a1),d1
    movhu d1,(d0,a0)
    movhu (4,a1),d0
    movhu (6,a1),d1
    movhu d1,(d0,a0)
finish:
    mov ep7_resume,d0
    mov d0,(32,sp)
    mov mdr,d1
    cmp selector_done,d1
    bne mdr_ready
    mov d0,mdr
mdr_ready:
    mov (28,sp),d0
    mov d0,psw
    mov (0,sp),d0
    mov (4,sp),d1
    mov (8,sp),d2
    mov (12,sp),a0
    mov (16,sp),a1
    mov (20,sp),a2
    mov (24,sp),a3
    add 32,sp
    jmp ep7_resume
.balign 2
.global profile_writes
profile_writes:
    .hword 706,-3000, 706,-3000
    .hword 782,-200, 782,-200
    .hword 730,3000, 830,100
    .hword 706,0, 706,0
