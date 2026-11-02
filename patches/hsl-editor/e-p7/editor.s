/* Original E142/1100 scoped virtual H/L properties. No persistent store of
 * its own; writes call the unchanged v4 app helper after native GUI admission. */
.section .ep7_ui6,"ax"
.balign 4
.global v5_api_override
v5_api_override:
    mov a0,(4,sp)
    mov a1,(8,sp)
    mov d0,a2
    mov d1,a3
    /* If resident state was reset while a virtual child survived, reject
     * its stale H/L enumeration rather than commit it as unmarked S. */
    cmp 5,d2
    bne api_owned
    mov (v5_state+4),d0
    cmp 1,d0
    beq api_owned
    cmp 2,d0
    beq api_owned
    cmp 0x60de5d69,d3
    bne not_ours
    mov a2,d0
    add -927,d0
    cmp 35,d0
    bls stale_color
    mov a2,d0
    add -1655,d0
    cmp 11,d0
    bhi not_ours
stale_color:
    mov (88,sp),a0
    movhu (88,a0),d0
    cmp 15,d0
    beq out_bad
    bra not_ours
api_owned:
    mov (v5_state),d0
    cmp 0,d0
    beq not_ours
    mov (v5_state+12),d0
    mov a2,d1
    sub d0,d1
    cmp 11,d1
    bhi not_ours
    cmp 0,d2
    bne scope_count
    cmp 0x60de36ce,d3
    beq getter
    cmp 0x60de5be6,d3
    beq getter
    cmp 0x60e27425,d3
    beq getter
    bra not_ours
scope_count:
    cmp 1,d2
    bne scope_enum
    cmp 0x60de368a,d3
    bne not_ours
    mov 15,d0
    bra handled
scope_enum:
    cmp 2,d2
    bne scope_valid
    cmp 0x60de388d,d3
    beq enum_value
    cmp 0x60de392b,d3
    beq enum_value
    bra not_ours
scope_valid:
    cmp 3,d2
    bne scope_default
    cmp 0x60de38c8,d3
    beq valid_value
    cmp 0x60de3975,d3
    beq valid_value
    bra not_ours
scope_default:
    cmp 4,d2
    bne scope_set
    cmp 0x60de98ae,d3
    bne not_ours
    clr d0
    bra out_value
scope_set:
    cmp 5,d2
    bne not_ours
    cmp 0x60de5d69,d3
    bne not_ours
    mov a3,d0
    cmp 0,d0
    bne not_ours
    jmp set_value
not_ours:
    clr d1
    ret [d2,d3,a2,a3],20
handled:
    mov 1,d1
    ret [d2,d3,a2,a3],20

enum_value:
    mov a3,d0
    cmp 14,d0
    bhi enum_bad
    add -7,d0
    mov (8,sp),a1
    cmp 0,a1
    beq handled
    mov d0,(a1)
    bra handled
enum_bad:
    mov -1,d0
    bra handled
valid_value:
    mov a3,d0
    cmp -7,d0
    blt value_invalid
    cmp 7,d0
    bgt value_invalid
    mov (4,sp),a0
    mov a2,d0
    clr d1
    call ep7_valid,[],0
    bra handled
value_invalid:
    clr d0
    bra handled
getter:
    mov a2,d0
    mov (v5_state+4),d1
    cmp 1,d1
    bne get_hue
    or 0xc000,d0
    bra get_axis
get_hue:
    or 0x8000,d0
get_axis:
    call ep7_v4_read,[],4
    cmp -7,d0
    blt get_neutral
    cmp 7,d0
    ble out_value
get_neutral:
    clr d0
out_value:
    mov (8,sp),a1
    cmp 0,a1
    beq out_bad
    mov d0,(a1)
    clr d0
    bra handled
out_bad:
    mov 0xf0000016,d0
    bra handled
set_value:
    mov (8,sp),d0
    cmp -7,d0
    blt out_bad
    cmp 7,d0
    bgt out_bad
    exthu d0
    mov (v5_state+4),d1
    cmp 1,d1
    bne tag_hue
    or 0x45520000,d0
    bra tag_ready
tag_hue:
    or 0x45510000,d0
tag_ready:
    mov d0,a1
    mov (4,sp),a0
    mov a2,d0
    clr d1
    /* The tagged scalar lives on the ORIGINAL GUI stack across admission
     * and coordination. No volatile global transaction can be mis-associated. */
    call ep7_set,[],0
    bra handled

/* The v4 helper consumes the same tagged scalar as its Wi-Fi app entry. */
.section .ep7_apply,"ax"
.global v5_apply_axis
v5_apply_axis:
    add -12,sp
    mov d2,(4,sp)
    mov d0,d2
    mov (ep7_gui_in_progress),d0
    cmp 1,d0
    bne apply_reject
    mov d2,d0
    call ep7_v4_edit,[d2,d3],16
    bra apply_status
apply_reject:
    mov 1,d0
apply_status:
    mov d0,(8,sp)
    mov d2,d0
    call ep7_raw_get,[],4
    exth d0
    mov d0,d3
    mov (8,sp),d0
    mov (4,sp),d2
    add 12,sp
    ret [],4

.section .ep7_state,"aw"
.balign 4
.global v5_state_ram
v5_state_ram:
    .space 16
.global v5_state
.set v5_state,v5_state_ram+0x40000000

.section .ep7_ui6,"ax"
/* This changes the lookup query only. The native FSM retains and delivers
 * original event 9016. Other states/properties retain "not found" exactly. */
.global v5_lookup_detour
v5_lookup_detour:
    cmp 0x9016,d0
    bne lookup_stock
    movbu (a0),d1
    cmp 2,d1
    bne lookup_stock
    movbu (1,a0),d1
    cmp 2,d1
    bne lookup_stock
    mov (4,a0),a1
    mov a1,d1
    cmp 0x611317c4,d1
    bne lookup_stock
    movhu (0x61fc43cc),d1
    cmp 0x13b3,d1
    bcs lookup_stock
    cmp 0x13b5,d1
    bls lookup_color
    cmp 0x140c,d1
    bne lookup_stock
lookup_color:
    mov 0x9004,d0
lookup_stock:
    call ep7_event_lookup,[d2,d3,a2,a3],20
lookup_return:
    add -8,sp
    mov d1,(0,sp)
    mov psw,d1
    mov d1,(4,sp)
    mov mdr,d1
    cmp lookup_return,d1
    bne lookup_mdr_done
    mov ep7_lookup_resume,d1
    mov d1,mdr
lookup_mdr_done:
    mov (4,sp),d1
    mov d1,psw
    mov (0,sp),d1
    add 8,sp
    jmp ep7_lookup_resume

/* Native type-26 parent identity; no insertion in its original layout. */
v5_bind:
    movhu (120,a0),d0
    cmp 13,d0
    bne bind_bad
    movhu (100,a0),d1
    cmp 0x13b3,d1
    beq bind_one
    cmp 0x13b4,d1
    beq bind_two
    cmp 0x13b5,d1
    beq bind_three
    cmp 0x140c,d1
    bne bind_bad
    mov 1655,d0
    bra bind_ready
bind_one:
    mov 927,d0
    bra bind_ready
bind_two:
    mov 939,d0
    bra bind_ready
bind_three:
    mov 951,d0
bind_ready:
    mov (v5_state),a1
    cmp a0,a1
    beq bind_done
    mov a0,(v5_state)
    mov d1,(v5_state+8)
    mov d0,(v5_state+12)
    clr d1
    mov d1,(v5_state+4)
bind_done:
    rets
bind_bad:
    clr d0
    rets

.global v5_parent
v5_parent:
    movm [d2,d3,a2,a3],(sp)
    add -12,sp
    mov d0,d2
    mov d1,(4,sp)
    mov a0,a2
    call v5_bind,[],0
    cmp 0,d0
    beq parent_stock
    cmp 0x9016,d2
    bne parent_sync
    mov (v5_state+4),d0
    inc d0
    cmp 3,d0
    bcs axis_ready
    clr d0
axis_ready:
    mov d0,(v5_state+4)
    mov 1,d3
axis_rebuild:
    mov d3,d0
    asl2 d0
    add 124,d0
    mov (d0,a2),a0
    call ep7_enum_ctor,[d2,d3,a2,a3],60
    inc d3
    cmp 12,d3
    bls axis_rebuild
    cmp 0x9016,d2
    bne parent_stock
    mov 1,d0
    bra parent_done
parent_sync:
    mov (v5_state+4),d0
    cmp 0,d0
    bne parent_sync_axis
    mov (128,a2),a0
    movhu (88,a0),d0
    cmp 15,d0
    bne parent_stock
    mov 1,d3
    bra axis_rebuild
parent_sync_axis:
    cmp 2,d0
    bhi parent_stock
    mov 1,d3
sync_loop:
    mov (v5_state+12),d0
    add d3,d0
    add -1,d0
    call v5_axis_value,[d2,d3,a2,a3],20
    mov 7,d1
    sub d0,d1
    mov d3,d0
    asl2 d0
    add 124,d0
    mov (d0,a2),a0
    movhu d1,(90,a0)
    inc d3
    cmp 12,d3
    bls sync_loop
parent_stock:
    mov a2,a0
    mov d2,d0
    mov (4,sp),d1
    call ep7_parent_event,[],0
parent_done:
    ret [d2,d3,a2,a3],28

v5_axis_value:
    mov (v5_state+4),d1
    cmp 1,d1
    bne axis_value_h
    or 0xc000,d0
    bra axis_value_read
axis_value_h:
    or 0x8000,d0
axis_value_read:
    call ep7_v4_read,[],4
    cmp -7,d0
    blt axis_neutral
    cmp 7,d0
    ble axis_value_done
axis_neutral:
    clr d0
axis_value_done:
    ret [d2,d3,a2,a3],20

.global v5_upper,v5_lower
.global v5_upper_detour,v5_lower_detour
v5_upper_detour:
    call v5_upper,[d2,d3,a2,a3],36
    mov 1,d3
    jmp ep7_upper_resume
v5_lower_detour:
    call v5_lower,[d2,d3,a2,a3],36
    mov 1,d3
    jmp ep7_lower_resume
v5_upper:
    mov 7,d3
    bra bound_axis
v5_lower:
    mov -7,d3
bound_axis:
    mov (v5_state+4),d1
    cmp 0,d1
    beq bound_stock
    mov (v5_state+12),d2
    cmp 927,d2
    beq bound_mode1
    cmp 939,d2
    beq bound_mode2
    cmp 951,d2
    beq bound_mode3
    cmp 1655,d2
    bne bound_stock
    mov 64,d1
    bra bound_check
bound_mode1:
    mov 54,d1
    bra bound_check
bound_mode2:
    mov 55,d1
    bra bound_check
bound_mode3:
    mov 56,d1
bound_check:
    cmp d1,d0
    bne bound_stock
    mov 12,a2
bound_loop:
    mov d2,d0
    call v5_axis_value,[d2,d3,a2,a3],20
    cmp d3,d0
    beq bound_yes
    inc d2
    add -1,a2
    bne bound_loop
    clr d0
    bra bound_done
bound_yes:
    mov 1,d0
bound_done:
    ret [d2,d3,a2,a3],36
bound_stock:
    cmp 7,d3
    beq bound_stock_upper
    jmp ep7_bound_lower
bound_stock_upper:
    jmp ep7_bound_upper

.global v5_numeric_detour
v5_numeric_detour:
    add -8,sp
    mov a0,(4,sp)
    call ep7_numeric,[d2,d3,a2,a3],44
    mov (4,sp),a0
    call v5_caption,[d2,d3,a2,a3],20
    add 8,sp
    jmp ep7_numeric_resume

v5_caption:
    mov a0,(4,sp)
    mov (384,a0),a0
    call v5_bind,[],0
    cmp 0,d0
    beq caption_done
    mov d0,d2
    mov (4,sp),a3
    inc4 a3
    mov (v5_state+4),d3
    mov 83,d0
    cmp 0,d3
    beq axis_letter
    mov 76,d0
    cmp 1,d3
    beq axis_letter
    mov 72,d0
axis_letter:
    movhu d0,(8,a3)
    mov 32,d0
    movhu d0,(10,a3)
    mov 5,d0
    movhu d0,(a3)
    mov 6,d0
    movhu d0,(6,a3)
    mov 1,d0
    movbu d0,(74,a3)
    cmp 0,d3
    beq caption_visibility
    clr d0
    movbu d0,(165,a3)
    movbu d0,(166,a3)
caption_visibility:
    movbu (167,a3),d0
    cmp 0,d0
    beq caption_single
    mov 65,d0
    movhu d0,(12,a3)
    mov 76,d0
    movhu d0,(14,a3)
    movhu d0,(16,a3)
    clr d0
    movhu d0,(18,a3)
    bra caption_done
caption_single:
    mov (4,sp),a0
    mov (384,a0),a0
    mov (124,a0),a0
    movhu (84,a0),d0
    mov (ep7_api_pointer),a0
    mov sp,a1
    add 12,a1
    call ep7_get,[],0
    mov (12,sp),d0
    add -1,d0
    cmp 11,d0
    bhi caption_unknown
    add d2,d0
    cmp 0,d3
    beq caption_stock_value
    call v5_axis_value,[d2,d3,a2,a3],20
    bra caption_value
caption_stock_value:
    mov (ep7_api_pointer),a0
    mov sp,a1
    add 12,a1
    call ep7_get,[],0
    mov (12,sp),d0
caption_value:
    cmp -7,d0
    blt caption_unknown
    cmp 7,d0
    bgt caption_unknown
    mov 43,d1
    cmp 0,d0
    bge caption_sign
    mov 45,d1
    xor -1,d0
    inc d0
caption_sign:
    movhu d1,(12,a3)
    add 48,d0
    movhu d0,(14,a3)
    clr d0
    movhu d0,(16,a3)
    bra caption_done
caption_unknown:
    mov 63,d0
    movhu d0,(12,a3)
    clr d0
    movhu d0,(14,a3)
caption_done:
    ret [d2,d3,a2,a3],20
