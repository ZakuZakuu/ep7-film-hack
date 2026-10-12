"""T17's single bounded two-key operation; fragments are NOT handler discovery.

Reuse GNU decoding. No function-ordinal mapping, recursive analysis, strings,
other address views, OEM execution, or user-selected full-image search.
"""
import struct
try:
    from .inspect_olympus_oe import FormatError
    from .probe_oe_executable import disassemble
except ImportError:
    from inspect_olympus_oe import FormatError
    from probe_oe_executable import disassemble

SCOPE = (0x74e534,0x7e2516)  # T7's measured name-resolver call span ONLY.
KEYS = (0x0201e6,0x031b0c)


def qualify(rows,key):
    # Tightened to the immediate adjacent CALL actually observed in all four
    # nominated fragments; no unknown/intervening value propagation.
    if len(rows)<2 or rows[0].mnemonic!='mov': return None
    try:
        literal,destination = rows[0].operands.split(',')
        identity = int(literal,0)&0xffffff
    except ValueError:
        return None
    if destination!='d0' or identity!=key: return None
    call=rows[1]
    if call.mnemonic!='call' or call.direct_target()!=0x75068f: return None
    return {'literal':hex(rows[0].address),'resolver_call':hex(call.address)}


def roots(data,objdump):
    lo,hi=SCOPE
    if len(data)<hi: raise FormatError('T17 scope outside decoded sample')
    # A separately guarded existing positive control, not another image query.
    control=disassemble(objdump,data[0x7dcf5c:0x7dcf6b],0x7dcf5c)
    if qualify(control,0x020165) is None:
        raise FormatError('known identity/resolver control failed')
    result=[]
    for key in KEYS:
        needle=struct.pack('<I',key)[:3];cursor=lo;hits=[];accepted=[]
        while (cursor:=data.find(needle,cursor,hi))>=0:
            hits.append(cursor);cursor+=1
            if len(hits)>16: raise FormatError('registered identity bound exceeded')
        for hit in hits:
            start=hit-2
            if start<lo or start+96>hi:
                raise FormatError('candidate context outside registered scope')
            rows=disassemble(objdump,data[start:start+96],start)
            qualified=qualify(rows,key)
            if qualified is not None:accepted.append(qualified)
        result.append({'identity':hex(key),'raw_matches':[hex(h) for h in hits],
                       'qualified_fragments':accepted})
    return {'scope':[hex(lo),hex(hi)],'results':result,
            'qualification':'literal-to-name-resolver fragment, NOT GUI caller, registration handler or ART parameter proof'}
