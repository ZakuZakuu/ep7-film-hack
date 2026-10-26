/* Original E142/1100 T25 v4. Reference method only: fishcu@539fcf1.
 * Image-owned requests keep v2 snapshot rules. Qualified compact headers
 * read one current profile byte. H/L comes from the native-publication mirror.
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
    /* A single uncached mirror cell holds both signed slider axes. */
    mov d0,d1
    asl 4,d0
    asl 5,d1
    add d1,d0
    mov ep7_mirror,a1
    add d0,a1
    mov (12,a2),a0
    add 706,a0
    mov 12,d2
copy_mirror:
    mov (a1),d1
    mov d1,d0
    exth d0
    add 7,d0
    add d0,d0
    mov hue_steps,a3
    movhu (d0,a3),d0
    movhu d0,(a0)
    asr 16,d1
    add 7,d1
    add d1,d1
    mov lightness_steps,a3
    movhu (d1,a3),d1
    movhu d1,(4,a0)
    inc4 a1
    add 24,a0
    add -1,d2
    bne copy_mirror
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

/* New CALL target, same ABI as the replaced native raw-set call. Ordinary
 * values tail-call stock untouched. Reserve the entire 455x high-word family. */
.global wifi_write
wifi_write:
    mov d1,d2
    lsr 16,d2
    mov d2,d3
    and 0xfff0,d3
    cmp 0x4550,d3
    beq marked_write
    call ep7_raw_set,[d2,d3],12
    mov 200,d0
    ret [d2,d3],12
marked_write:
    mov a2,d0
    add -12,sp
    mov d0,(4,sp)
    mov d1,(8,sp)
    call validate,[d2,d3,a2,a3],20
    cmp 0,d0
    bne write_bad
    mov (4,sp),d0
    mov d0,(ep7_pending)
    clr d0
    mov d0,(ep7_pending+4)
    mov (8,sp),d0
    mov d0,(ep7_pending+8)
    mov 0x041b0011,d0
    call ep7_post,[d2,d3,a2,a3],36
    exth d0
    cmp 0,d0
    bne write_bad
    mov 200,d0
    add 12,sp
    ret [d2,d3],12
write_bad:
    mov 520,d0
    add 12,sp
    ret [d2,d3],12

/* Validate d0=ID,d1=marked value. d0=0 if valid. Never performs a write.
 * d2=axis highword, d3=signed slider; a2=minimum translation (5/7).
 * Accept only native COLOR cells and per-profile tone/shading keys. */
validate:
    mov d0,a3
    mov d1,d2
    lsr 16,d2
    mov d1,d3
    exth d3
    cmp 0x4552,d2
    bhi invalid
    cmp 0x4550,d2
    bcs invalid
    mov 7,a2
    cmp -7,d3
    blt invalid
    cmp 7,d3
    bgt invalid
    mov a3,d0
    call cell_index,[],4
    cmp 48,d0
    bcs color_key
    cmp 0x4550,d2
    bne invalid
    mov a3,d0
    cmp 963,d0
    bcs invalid
    cmp 971,d0
    bls valid
    cmp 1672,d0
    bcs shading_key
    cmp 1674,d0
    bls valid
shading_key:
    cmp 1667,d0
    bcs invalid
    cmp 1670,d0
    bhi invalid
color_key:
    cmp 0x4550,d2
    bne valid
    mov 5,a2
    cmp -5,d3
    blt invalid
    cmp 5,d3
    bgt invalid
valid:
    clr d0
    ret [d2,d3,a2,a3],20
invalid:
    mov -1,d0
    ret [d2,d3,a2,a3],20

/* COLOR setting ID -> physical f6fa element 0..47; 48 means invalid. */
cell_index:
    add -927,d0
    cmp 35,d0
    bls index_done
    add -728,d0
    cmp 11,d0
    bhi index_bad
    add 36,d0
index_done:
    ret [],4
index_bad:
    mov 48,d0
    ret [],4

/* App-stage CALL replacement. Packed axes survive the native pending record
 * and event receiver as a signed 32-bit scalar. Revalidate at the trust edge. */
.global app_edit
app_edit:
    mov d1,d2
    lsr 16,d2
    mov d2,d3
    and 0xfff0,d3
    cmp 0x4550,d3
    beq edit_marked
    jmp ep7_normal_edit
edit_marked:
    add -20,sp
    mov d0,(4,sp)
    mov d1,(8,sp)
    call validate,[d2,d3,a2,a3],20
    cmp 0,d0
    bne edit_bad
    call ep7_inhibit,[],0
    extbu d0
    cmp 1,d0
    beq edit_bad
    mov (4,sp),d2
    mov (8,sp),d3
    mov d3,d0
    lsr 16,d0
    mov d0,(12,sp)
    cmp 0x4550,d0
    beq scalar_edit
    mov d2,d0
    mov 1,d1
    call ep7_part_read,[d2],8
    call decode_cell,[d2,d3,a2,a3],20
    mov d0,d1
    mov (12,sp),d0
    mov (8,sp),d3
    and 15,d3
    cmp 0x4551,d0
    bne replace_l
    and 0xf0,d1
    or d3,d1
    bra pack_cell
replace_l:
    asl 4,d3
    and 15,d1
    or d3,d1
pack_cell:
    mov d1,d0
    xor 255,d0
    asl 8,d0
    or d1,d0
    or 0xe7410000,d0
    mov d0,a0
    mov 1,d1
    mov d2,d0
    call ep7_part_write,[d2],8
    /* Same current signed S. The registered
     * current/staged/filter/notification path remains the stock mechanism. */
    mov d2,d0
    call ep7_raw_get,[],4
    exth d0
    mov d0,d1
    bra normal_apply
scalar_edit:
    mov (8,sp),d1
    exth d1
normal_apply:
    mov d2,d0
    call ep7_normal_edit,[d2,d3],16
    add 20,sp
    ret [d2,d3],16
edit_bad:
    mov 1,d0
    add 20,sp
    ret [d2,d3],16

/* Encoded u32 -> valid packed slider nibbles, otherwise zero. */
decode_cell:
    mov d0,d1
    lsr 16,d1
    cmp 0xe741,d1
    bne decode_bad
    mov d0,d2
    and 255,d2
    lsr 8,d0
    and 255,d0
    xor 255,d0
    cmp d2,d0
    bne decode_bad
    mov d2,d0
    and 15,d0
    cmp 8,d0
    beq decode_bad
    mov d2,d0
    lsr 4,d0
    cmp 8,d0
    beq decode_bad
    mov d2,d0
    ret [d2,d3,a2,a3],20
decode_bad:
    clr d0
    ret [d2,d3,a2,a3],20

/* Actual typed COLOR record writer CALL replacement. Publish exactly one H/L
 * cell only AFTER the original S element write, also used by boot/recall loop.
 * Other record types use the original target directly. The mirror is uncached
 * and each complete H/L pair is one aligned 32-bit publication. */
.global publish
publish:
    cmp 0xf6fa,d0
    beq publish_color
    jmp ep7_typed_write
publish_color:
    add -36,sp
    mov d1,(32,sp)
    call ep7_typed_write,[d2,d3,a2,a3],40
    mov d0,(4,sp)
    mov d1,(8,sp)
    mov a0,(12,sp)
    mov a1,(16,sp)
    mov psw,d0
    mov d0,(20,sp)
    mov mdr,d0
    mov d0,(24,sp)
    mov (32,sp),d3
    cmp 47,d3
    bhi publish_finish
    mov d3,d0
    cmp 36,d0
    bcs publish_first
    add 692,d0
publish_first:
    add 927,d0
    /* Read-only equivalent of the qualified part getter's address formula.
     * Avoid its multiply side effect on MDRQ; writes still use native API.
     * Only the exact registered E142 ACTIVE base is admitted. */
    mov (ep7_active_pointer),d1
    cmp 0x6250ba00,d1
    bne publish_neutral
    or 0x40000000,d1
    mov d1,a0
    add 1769,d0
    asl2 d0
    mov (d0,a0),d0
    bra publish_decode
publish_neutral:
    clr d0
publish_decode:
    call decode_cell,[d2,d3,a2,a3],20
    mov d0,d1
    and 15,d0
    asl 28,d0
    asr 28,d0
    lsr 4,d1
    asl 28,d1
    asr 12,d1
    exthu d0
    or d1,d0
    asl2 d3
    mov ep7_mirror,a0
    mov d0,(d3,a0)
publish_finish:
    mov (24,sp),d0
    mov d0,mdr
    mov (20,sp),d0
    mov d0,psw
    mov (4,sp),d0
    mov (8,sp),d1
    mov (12,sp),a0
    mov (16,sp),a1
    add 36,sp
    ret [d2,d3,a2,a3],40

/* Read extension is fail-closed for both reserved axis namespaces.
 * Stock parser already constrains the ID to unsigned 16 bits. */
.global wifi_read
wifi_read:
    cmp 0xffff,d0
    beq capability
    mov d0,d1
    and 0xc000,d1
    cmp 0,d1
    bne axis_read
    jmp ep7_raw_get
capability:
    mov 0x45503731,d0
    ret [],4
axis_read:
    add -8,sp
    mov d1,(4,sp)
    and 0x3fff,d0
    call cell_index,[],4
    cmp 48,d0
    bcc read_bad
    asl2 d0
    mov ep7_mirror,a0
    mov (d0,a0),d0
    mov (4,sp),d1
    cmp 0x8000,d1
    beq read_h
    cmp 0xc000,d1
    bne read_bad
    asr 16,d0
    bra read_done
read_h:
    exth d0
read_done:
    add 8,sp
    ret [],4
read_bad:
    mov 0x80000000,d0
    bra read_done

.balign 2
lightness_steps:
    .hword -300,-250,-200,-150,-100,-50,-25,0,25,50,100,150,200,250,300

/* Keep the native numeric conversion. Carry an invalid-ID bit above u16 so
 * only marked requests reject it; the unmarked native EXTHU is unchanged. */
.global id_parse
id_parse:
    add -4,sp
    mov a0,a2
    mov d0,d3
    call ep7_hex_parse,[d2,d3,a2,a3],16
    mov d0,d2
    mov a2,a0
    mov d3,d0
    mov 4,d1
    call canonical_hex,[],4
    cmp 0,d0
    beq id_ready
    or 0x10000,d2
id_ready:
    mov d2,d0
    add 4,sp
    ret [d2,d3,a2,a3],16

.global value_parse
value_parse:
    add -4,sp
    mov a0,a2
    mov d0,d3
    call ep7_hex_parse,[d2,d3,a2,a3],16
    mov d0,d2
    and 0xfff00000,d0
    cmp 0x45500000,d0
    beq marked_text
    cmp 8,d3
    bcs value_ready
    movbu (a2),d0
    cmp 52,d0
    bne value_ready
    movbu (1,a2),d0
    cmp 53,d0
    bne value_ready
    movbu (2,a2),d0
    cmp 53,d0
    bne value_ready
marked_text:
    cmp 8,d3
    bne malformed_value
    mov a2,a0
    mov d3,d0
    mov 8,d1
    call canonical_hex,[],4
    cmp 0,d0
    beq value_ready
malformed_value:
    mov 0x455f0000,d2
value_ready:
    mov d2,d0
    add 4,sp
    ret [d2,d3,a2,a3],16

canonical_hex:
    cmp d1,d0
    bhi text_bad
    cmp 0,d0
    beq text_bad
    mov a0,a1
    add d0,a1
hex_character:
    movbu (a0),d1
    cmp 48,d1
    bcs text_bad
    cmp 57,d1
    bls hex_next
    cmp 65,d1
    bcs text_bad
    cmp 70,d1
    bls hex_next
    cmp 97,d1
    bcs text_bad
    cmp 102,d1
    bhi text_bad
hex_next:
    inc a0
    cmp a1,a0
    bne hex_character
    clr d0
    ret [],4
text_bad:
    mov -1,d0
    ret [],4

.balign 2
hue_steps:
    .hword 7000,6000,5000,4000,3000,2000,1000,0,-1000,-2000,-3000,-4000,-5000,-6000,-7000
