# Original reference encodings only. Assemble/decode, never run as OEM code.
.text
.global _start
_start:
.irp r,a0,a1,a2,a3,d0,d1,d2,d3
 mov 872,\r
 mov 362,\r
 mov 62929,\r
 mov -2607,\r
 mov 17601,\r
 mov 24785,\r
.endr
.irp a,a0,a1,a2,a3
.irp d,d0,d1,d2,d3
 movbu (24785,\a),\d
 movbu \d,(24785,\a)
 movbu (24784,\a),\d
 movbu \d,(24784,\a)
.endr
.endr
