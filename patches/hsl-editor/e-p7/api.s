/* Original E142/1100 v5a API adapters. Design reference only: fishcu@539fcf1.
 * Resident in the qualified settings-code section; no dependency on an
 * unloaded editor component while the axis is S.
 * S and unrelated call sites execute the untouched original implementations.
 */
.section .ep7_api,"ax"
.balign 4
.macro API_STUB name, kind, stock
.global \name
\name:
    add -4,sp
    mov d2,(0,sp)
    mov (v5_state+4),d2
    cmp 1,d2
    bcs 1f
    cmp 2,d2
    bhi 1f
    mov \kind,d2
    jmp api_active
1:
.if \kind == 5
    mov mdr,d2
    cmp 0x60de5d69,d2
    bne 2f
    mov 5,d2
    jmp api_active
2:
.endif
    mov (0,sp),d2
    add 4,sp
    jmp \stock
.endm
API_STUB v5_get,0,ep7_get
API_STUB v5_count,1,ep7_count
API_STUB v5_enum,2,ep7_enum
API_STUB v5_valid,3,ep7_valid
API_STUB v5_default,4,ep7_default
API_STUB v5_set,5,ep7_set

api_active:
    add -44,sp
    mov d0,(4,sp)
    mov d1,(8,sp)
    mov a0,(12,sp)
    mov a1,(16,sp)
    mov d3,(24,sp)
    mov mdr,d3
    mov d3,(20,sp)
    mov a2,(28,sp)
    mov a3,(32,sp)
    mov d2,(36,sp)
    call v5_api_override,[d2,d3,a2,a3],20
    mov psw,d2
    mov d2,(40,sp)
    cmp 1,d1
    beq api_handled
    mov (36,sp),d2
    asl2 d2
    mov api_originals,a2
    mov (d2,a2),a2
    mov (4,sp),d0
    mov (8,sp),d1
    mov (12,sp),a0
    mov (16,sp),a1
    calls (a2)
api_passthrough_return:
    mov psw,d2
    mov d2,(40,sp)
    mov mdr,d2
    cmp api_passthrough_return,d2
    bne api_restore
api_handled:
    mov (20,sp),d2
    mov d2,mdr
api_restore:
    mov (40,sp),d2
    mov d2,psw
    mov (24,sp),d3
    mov (28,sp),a2
    mov (32,sp),a3
    mov (44,sp),d2
    add 48,sp
    rets
.balign 4
api_originals:
    .long ep7_get,ep7_count,ep7_enum,ep7_valid,ep7_default,ep7_set

/* One existing explicit-value CALL site, after unmodified GUI admission.
 * Keep all ordinary S calls in this resident section. */
.global v5_apply_detour
v5_apply_detour:
    add -8,sp
    mov d0,(0,sp)
    mov d1,(4,sp)
    lsr 16,d1
    cmp 0x4551,d1
    beq apply_axis
    cmp 0x4552,d1
    bne apply_stock
apply_axis:
    mov (0,sp),d0
    mov (4,sp),d1
    add 8,sp
    call v5_apply_axis,[],4
apply_axis_return:
    cmp 0,d0
    beq apply_return
    /* Same implicit frame as the replaced native value adapter. Rejection
     * reaches its original GUI caller, which clears edit-in-progress. */
    clr d0
    ret [d2,d3,a2],16
apply_stock:
    mov (0,sp),d0
    mov (4,sp),d1
    add 8,sp
    call ep7_gui_value_apply,[],4
apply_return:
    add -8,sp
    mov d1,(0,sp)
    mov psw,d1
    mov d1,(4,sp)
    mov mdr,d1
    cmp apply_return,d1
    beq apply_set_mdr
    cmp apply_axis_return,d1
    bne apply_mdr_done
apply_set_mdr:
    mov ep7_gui_apply_resume,d1
    mov d1,mdr
apply_mdr_done:
    mov (4,sp),d1
    mov d1,psw
    mov (0,sp),d1
    add 8,sp
    jmp ep7_gui_apply_resume

/* The lifecycle code shares only the already-qualified v4 owned gap. */
.section .ep7_lifecycle,"ax"
/* Entry/exit clear volatile axis identity, never a camera setting. */
.global v5_enter,v5_exit
v5_enter:
    call v5_clear,[d2],8
    jmp ep7_editor_enter
v5_exit:
    call v5_clear,[d2],8
    jmp ep7_editor_exit
v5_clear:
    clr d2
    mov d2,(v5_state)
    mov d2,(v5_state+4)
    mov d2,(v5_state+8)
    mov d2,(v5_state+12)
    ret [d2],8
