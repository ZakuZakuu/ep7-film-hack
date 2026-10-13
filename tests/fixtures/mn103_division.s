# Original arithmetic only: zero upper word, positive divisor, fitting quotient.
# No OEM function, parameter record, device or input is reconstructed/executed.
.text
.global _start
_start:
 mov 0x30000,a0
 mov a0,sp
 mov 1000,d0
 mov 137042,d1
 clr d2
 mov d2,mdr
 divu d0,d1
 cmp 137,d1
 bne failure
 mov mdr,d2
 cmp 42,d2
 bne failure
 mov 0x7fffffff,d1
 clr d2
 mov d2,mdr
 divu d0,d1
 cmp 2147483,d1
 bne failure
 mov mdr,d2
 cmp 647,d2
 bne failure
 clr d1
 clr d2
 mov d2,mdr
 divu d0,d1
 cmp 0,d1
 bne failure
 mov mdr,d2
 cmp 0,d2
 bne failure
 clr d1
 jmp done
failure:
 mov 73,d1
done:
 mov 1,d0
 clr d2
 clr d3
 syscall
