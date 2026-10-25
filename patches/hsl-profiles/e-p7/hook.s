/* Original E-P7 1.1 T24 candidate. No settings writes or writable globals.
 * Method reference: fishcu/oly_fw_analysis@539fcf1 (not copied source).
 * Native owner graph and offsets independently checked on E142 build 1100.
 * Entry replaces the CALL of the COLOR/preset selector, not the T20 CALL.
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
    /* The stock selector handles all branches first. Only default COLOR
     * with the ordinary embedded request is eligible for this extension. */
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
    /* Accept any of the sixteen actual operation records (56 bytes each). */
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
    bne finish
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
    add -1,d0
    cmp 3,d0
    bhi finish
    /* 48 bytes per row, physically ordered pairs of native H and L. */
    mov d0,d1
    asl 4,d0
    asl 5,d1
    add d1,d0
    mov profile_hl,a1
    add d0,a1
    mov (12,a2),a0
    add 706,a0
    mov 12,d2
copy_pair:
    movhu (a1),d0
    movhu d0,(a0)
    movhu (2,a1),d0
    movhu d0,(4,a0)
    add 4,a1
    add 24,a0
    add -1,d2
    bne copy_pair
finish:
    /* Restore the original CALL return slot, which is caller-owned again. */
    mov ep7_resume,d0
    mov d0,(32,sp)
    /* Leaf selector exits can leave the entering CALL address in MDR. */
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
.global profile_hl
profile_hl:
    /* Record order: yellow, red, magenta, blue, cyan, green,
     * orange, rose, violet, azure, teal, lime. 12 pairs in every row. */
    .hword -3000,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0
    .hword 0,0, 0,0, 0,0, 0,-200, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0
    .hword 0,0, 3000,0, 0,0, 0,0, 0,0, 0,100, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0
    .hword 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0, 0,0
