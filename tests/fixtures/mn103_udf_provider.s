# Original provider-specific arithmetic check; no OEM-derived program.
.text
.global _start
_start:
 mov 0x30000,a0
 mov a0,sp
 mov 17,d0
 udfu01 6,d0
 cmp 102,d0
 bne failure
 mov 0x80000000,d0
 udfu01 6,d0
 cmp 0,d0
 bne failure
 mov 2,d0
 udfu01 255,d0
 cmp 510,d0
 beq unsigned_observation
 # Pinned provider treats imm8=255 as -1 here; preserve this counterexample.
 cmp -2,d0
 bne failure
 mov 91,d1
 jmp done
unsigned_observation:
 clr d1
 jmp done
failure:
 mov 73,d1
done:
 mov 1,d0
 clr d2
 clr d3
 syscall
