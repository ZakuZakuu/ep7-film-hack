/* Original reference shapes, never derived OEM code and never executed. */
.ifndef panel_slot
.set panel_slot,820
.endif
.text
.global _start
_start:
.irp base,a0,a1,a2,a3
.irp target,a0,a1,a2,a3
mov (panel_slot,\base),\target
calls (\target)
.endr
.endr
