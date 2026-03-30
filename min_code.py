# min_code.py
#
# shea m puckett - 2026
# mit license

import struct, io 

VERSION = const(0)

STRS = const(0x00)    
BINS = const(0x10)
BSL1 = const(0x0E)
BSL4 = const(0x0F)
STRE = const(0x1F)

IXS  = const(0x20)  
I16  = const(0x28)  
I32  = const(0x29)
F32  = const(0x2a)
NONE = const(0x2b)

LIST = const(0x30)
DICT = const(0x31)
POP  = const(0x32)

VER  = const(0x3E)
END  = const(0x3F)

TINT = const(0x40)

# ---------- ENCODE ----------

def encode(v, stream=None):
    fab = stream is None
    if fab: stream = io.BytesIO()
    w = stream.write

    def wb(x): w(bytes([x]))
    def wp(f,s): w(struct.pack(f,s))
        
    w(bytes([VER, VERSION]))

    def _bytes(b, is_str):
        l = len(b)
        if l <= 13:                 wb(is_str | l)
        elif l <= 255:              wb(is_str | BSL1); wb(l)
        else:                       wb(is_str | BSL4); wp(">I", l)
        w(b)

    def enc(x):
        if x is True: x = 1
        elif x is False: x = 0
                        
        t = type(x)
        if t is int:
            if -0x40 <= x <= 0x7f:                wb(x+0x80)  # TINT + 64
            elif -0x400 <= x <= 0x3ff:            wb(IXS | ((x & 0x700) >> 8)); wb(x & 0xff)
            elif -0x8000 <= x <= 0x7fff:          wb(I16); wp(">h", x)
            elif -0x80000000 <= x <= 0x7fffffff:  wb(I32); wp(">i", x)
            else: raise ValueError()
        elif t is float:                          wb(F32); wp(">f", x)
        elif x is None:                           wb(NONE)
        elif t is str:                            _bytes(x.encode(), STRS)
        elif t is bytes or t is bytearray:        _bytes(x, BINS)
        elif t is list or t is tuple:
            wb(LIST)
            for i in x: enc(i)
            wb(POP)
        elif t is dict:
            wb(DICT)
            for k in x: enc(k); enc(x[k])
            wb(POP)
        else: raise TypeError()

    enc(v); wb(END)

    if fab: return stream.getvalue()


# ---------- DECODE ----------

def decode(src):
    if not hasattr(src, "read"): src = io.BytesIO(src)
    r = src.read; u = struct.unpack

    flag = ValueError() # also a unique object to test against

    if r(2) != bytes([VER,VERSION]): raise flag

    stack = []
    out = None  

    def push(v):
        nonlocal out
        if not stack:           out = v; return
        t = stack[-1]
        if t[0] == LIST:        t[1].append(v)
        else:
            if t[2] is flag:    t[2] = v
            else:               t[1][t[2]] = v; t[2] = flag
    
    while True:
        b = r(1)[0]
        if b >= TINT:           push(b - 0x80)
        elif b <= STRE: 
            l = b & 0x0f
            if l == BSL1:       l = r(1)[0]
            elif l == BSL4:     l = u(">I",r(4))[0]
            d = r(l)
            push(d.decode() if b < BINS else d)
        elif b < I16: 
            v = ((b & 7) << 8) + r(1)[0]
            push(v - 0x800 if v & 0x400 else v)
        elif b == I16:          push(u(">h", r(2))[0])
        elif b == I32:          push(u(">i", r(4))[0])
        elif b == F32:          push(u(">f", r(4))[0])
        elif b == NONE:         push(None)
        elif b == LIST:         stack.append([LIST, []])
        elif b == DICT:         stack.append([DICT, {}, flag])
        elif b == POP:          push(stack.pop()[1])
        elif b == END:          return out
        else:                   break  # unknown code
    raise flag
            
