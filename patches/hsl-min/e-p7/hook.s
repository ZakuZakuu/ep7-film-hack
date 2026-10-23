/* Original E-P7 1.1 minimal COLOR experiment; no UI or persistent state.
 * Reference method: fishcu/oly_fw_analysis@539fcf1, not copied assembly.
 * Bind ep7_builder / ep7_resume at link time, not numeric displacements.
 */
.text
.balign 4
.global _start
_start:
    call ep7_builder,[d2,d3,a2,a3],96
    /* SP-immediate ADD and MOV leave PSW unchanged in the pinned GNU core.
     * No subsequent CALL, arithmetic or loop modifies MDR/LIR/LAR.
     * The stock caller's A2 still owns the output pointer at +12.
     */
    add -8,sp
    mov d0,(0,sp)
    mov a0,(4,sp)
    mov (12,a2),a0
    /* record 0: yellow H slider +3 => -3000, high halfword of word +16 */
    mov -3000,d0
    movhu d0,(706,a0)
    /* record 3: blue L slider -5 => -200, high halfword of word +20 */
    mov -200,d0
    movhu d0,(782,a0)
    mov (0,sp),d0
    mov (4,sp),a0
    add 8,sp
    jmp ep7_resume
