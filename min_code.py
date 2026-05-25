# min_code.py

import struct, io 

try:
    _test = const(0)
except:
    def const(a): return a

VERSION = const(0)

STRS = const(0x00)    
BINS = const(0x10)
BSL1 = const(0x0E)
BSL4 = const(0x0F)
STRE = const(0x1F)

IXS  = const(0x20)  

I16  = const(0x30)
BPOS = const(0x31)
BNEG = const(0x32)
F32  = const(0x33)
LIST = const(0x34)
DICT = const(0x35)
POP  = const(0x36)
NONE = const(0x37)
TRUE = const(0x38)
FALSE= const(0x39)

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
        t = type(x)
        if t is int:
            if -0x40 <= x <= 0x7f:                wb(x+0x80)  # TINT + 64
            elif -0x400 <= x <= 0xbff:            x += 0x400; wb(IXS | (x >> 8)); wb(x & 0xff)
            elif -0x4000 <= x <= 0xbfff:          wb(I16); x += 0x4000; wb(x >> 8); wb(x & 0xff)
            else: 
              if x < 0: x = -x; wb(BNEG)
              else: wb(BPOS)
              while x > 0x7f: wb(x & 0x7f); x >>= 7
              wb(x | 0x80)
        elif t is float:                          wb(F32); wp(">f", x)
        elif x is None:                           wb(NONE)
        elif x is True:                           wb(TRUE)
        elif x is False:                          wb(FALSE)
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
            v = r(l)
            push(v.decode() if b < BINS else v)
        elif b < I16: 
            push((((b & 0xF) << 8) + r(1)[0]) - 0x400)
        elif b == I16:          l = r(2); push( ((l[0]<<8)|l[1]) - 0x4000)
        elif b == BPOS or b == BNEG:
          v = l = 0
          while True:
            b2 = r(1)[0]
            v |= (b2 & 0x7f) << l
            l += 7
            if b2 & 0x80: break
          push(-v if b == BNEG else v)
        elif b == F32:          push(u(">f", r(4))[0])
        elif b == NONE:         push(None)
        elif b == TRUE:         push(True)
        elif b == FALSE:        push(False)
        elif b == LIST:         stack.append([LIST, []])
        elif b == DICT:         stack.append([DICT, {}, flag])
        elif b == POP:          push(stack.pop()[1])
        elif b == END:          return out
        else:                   break  # unknown code
    raise flag
            
  
