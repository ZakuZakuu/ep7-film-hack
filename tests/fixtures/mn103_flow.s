# Original synthetic GNU assembler fixture. No camera code or parameters.
        .text
        .global _start
_start:
        mov 7,d0
        cmp 3,d0
        beq small
        call helper,[],0
        ret [],0
small:
        mov 1,d0
        ret [],0
helper:
        movbu (30,a0),d1
        movhu (16,a0),d0
        and 16384,d0
        ret [],0
