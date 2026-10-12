# Original synthetic cached-prefix fidelity control. No OEM execution or edits.
# Hardware's cached MOV still loads 7 on iteration two; GNU may refetch 9.
.text
.global _start
_start:
 mov 0x30000,a0
 mov a0,sp
 mov -2,d2
 setlb
cached:
 mov 7,d0
 nop
 nop
 # Change only this temporary synthetic program's immediate after caching.
 mov 9,d1
 mov cached+1,a0
 movbu d1,(a0)
 inc d2
 lne
 # Exit with the last observed value; runner records 7 vs 9, never assumes.
 mov d0,d1
 mov 1,d0
 syscall
