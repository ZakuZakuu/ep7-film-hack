# Original far-section fixture; forces CALL d32 (7 bytes)/CALLS d32 (6).
.text
.global _start
_start:
 mov 0x30000,a0
 mov a0,sp
 call far_leaf,[],4
after_call:
 calls far_simple
after_calls:
 mov sp,a0
 cmp 0x30000,a0
 bne failure
 mov 1,d0
 mov 0,d1
 syscall
failure:
 mov 1,d0
 mov 74,d1
 syscall
.section .far,"ax"
far_leaf:
 mov sp,a0
 add 4,a0
 mov (a0),d0
 mov after_call,d1
 cmp d1,d0
 beq 1f
 jmp failure
1:
 mov mdr,d0
 cmp d1,d0
 beq 2f
 jmp failure
2:
 ret [],4
far_simple:
 mov sp,a0
 mov (a0),d0
 mov after_calls,d1
 cmp d1,d0
 beq 3f
 jmp failure
3:
 rets
