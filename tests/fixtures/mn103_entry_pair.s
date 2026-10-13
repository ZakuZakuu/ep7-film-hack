# Original demonstration of two entry contracts, not an OEM routine.
.text
.global _start
.macro eq reg,value
 cmp \value,\reg
 beq 1f
 jmp failure
1:
.endm
_start:
 mov 0x30000,a0
 mov a0,sp
 mov 55,a2
 call body,[a2],8
 eq a2,55
 mov sp,a0
 eq a0,0x30000
 mov full,a0
 calls (a0)
 eq a2,55
 mov sp,a0
 eq a0,0x30000
 mov 1,d0
 clr d1
 syscall
.type full,@function
full:
 movm [a2],(sp)
 add -4,sp
body:
 mov sp,a0
 eq a0,0x2fff8
 mov (4,sp),d0
 eq d0,55
 mov 99,a2
 ret [a2],8
failure:
 mov 1,d0
 mov 73,d1
 syscall
