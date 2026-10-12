# Original synthetic self-checks; no OEM bytes or architecture-specific device IO.
# Only the GNU simulator's exit service is used (not a camera syscall claim).
.text
.global _start
.macro eq reg, value
 cmp \value,\reg
 beq 1f
 jmp failure
1:
.endm
.macro yes branch
 \branch 1f
 jmp failure
1:
.endm
_start:
 mov 0x30000,a0
 mov a0,sp
 mov 11,d2
 mov 22,d3
 mov 33,a2
 mov 44,a3
 call leaf,[d2,d3,a2,a3],20
after_call:
 eq d2,11
 eq d3,22
 eq a2,33
 eq a3,44
 mov sp,a0
 eq a0,0x30000
 call fast_leaf,[],4
after_fast:
 mov sp,a0
 eq a0,0x30000
 calls simple_leaf
after_calls:
 mov sp,a0
 eq a0,0x30000
 mov indirect_leaf,a0
 calls (a0)
after_indirect:
 mov sp,a0
 eq a0,0x30000
 # Nested CALLS requires a distinct return slot, not implicit SP movement.
 calls nested
after_nested:
 mov sp,a0
 eq a0,0x30000
 # Memory widths and sign/zero extension, with canaries outside the stores.
 mov 0x20000,a0
 mov 0x12345678,d0
 mov d0,(a0)
 mov 0x89abcdef,d1
 movbu d1,(a0)
 mov (a0),d2
 eq d2,0x123456ef
 mov 0xfedcba98,d1
 movhu d1,(2,a0)
 mov (a0),d2
 eq d2,0xba9856ef
 movbu (a0),d2
 eq d2,239
 movbu (a0),d2
 extb d2
 eq d2,-17
 movhu (2,a0),d2
 eq d2,0xba98
 movhu (2,a0),d2
 exth d2
 eq d2,0xffffba98
 mov 0x123480ff,d2
 extbu d2
 eq d2,255
 mov 0x123480ff,d2
 extb d2
 eq d2,-1
 mov 0x123480ff,d2
 exthu d2
 eq d2,0x80ff
 mov 0x123480ff,d2
 exth d2
 eq d2,0xffff80ff
 # AND/OR flags and conditional branches use forwarded arithmetic flags.
 mov 0x804000,d0
 and 0x4000,d0
 yes bne
 eq d0,0x4000
 or 0x800000,d0
 eq d0,0x804000
 and -16385,d0
 eq d0,0x800000
 and 0,d0
 yes beq
 mov 0x7fffffff,d0
 inc d0
 yes bge
 # Signed overflow sets N and V together: 0x80000000 result is NOT signed <.
 cmp 1,d0
 yes blt
 yes bcc
 mov -1,d0
 cmp 1,d0
 yes blt
 yes bhi
 mov 0,d0
 cmp 1,d0
 yes blt
 yes bcs
 mov 4,d0
 cmp 3,d0
 yes bgt
 yes bge
 yes bcc
 mov 3,d0
 cmp 3,d0
 yes beq
 yes ble
 yes bls
 # Address increments and loads/stores do not replace the counter's flags.
 mov -1,d3
 inc d3
 inc4 a0
 movbu (a0),d0
 yes beq
 # A fresh, separate, synthetic 32-byte word-copy case.
 mov 0x21000,a0
 mov 0x22000,a1
 mov -8,d3
 setlb
 mov (a0),d2
 inc4 a0
 mov d2,(a1)
 inc4 a1
 inc d3
 lne
 yes beq
 yes bcs
 eq a0,0x21020
 eq a1,0x22020
 eq d3,0
 mov 0x22000,a0
 mov (a0),d0
 eq d0,0x11223344
 mov (28,a0),d0
 eq d0,0x89abcdef
 mov (32,a0),d0
 eq d0,0x5a5a5a5a
 mov 1,d0
 mov 0,d1
 syscall
leaf:
 mov sp,a0
 eq a0,0x2ffec
 add 20,a0
 mov (a0),d0
 mov after_call,d1
 cmp d1,d0
 yes beq
 mov mdr,d0
 cmp d1,d0
 yes beq
 mov (4,sp),d0
 eq d0,44
 mov (16,sp),d0
 eq d0,11
 mov -1,d2
 mov -2,d3
 mov -3,a2
 mov -4,a3
 ret [d2,d3,a2,a3],20
fast_leaf:
 mov mdr,d0
 mov after_fast,d1
 cmp d1,d0
 yes beq
 retf [],4
simple_leaf:
 mov sp,a0
 eq a0,0x30000
 mov (a0),d0
 mov after_calls,d1
 cmp d1,d0
 yes beq
 rets
indirect_leaf:
 mov mdr,d0
 mov after_indirect,d1
 cmp d1,d0
 yes beq
 rets
nested:
 add -4,sp
 calls nested_leaf
 add 4,sp
 rets
nested_leaf:
 mov sp,a0
 eq a0,0x2fffc
 rets
failure:
 mov 1,d0
 mov 73,d1
 syscall
.section .input,"aw"
.long 0x11223344,0x22334455,0x33445566,0x44556677
.long 0x55667788,0x66778899,0x778899aa,0x89abcdef
.section .output,"aw"
.space 32,0xa5
.long 0x5a5a5a5a
