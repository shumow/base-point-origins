"""MD4, MD2, SHA-0, RIPEMD-128, Snefru-lite not in hashlib; implement MD4, SHA-0, RIPEMD-128 in pure Python (all 1990s candidates)."""
import struct, hashlib

def _rol(x, n): return ((x << n) | (x >> (32 - n))) & 0xffffffff

def md4(msg: bytes) -> bytes:
    F = lambda x, y, z: (x & y) | (~x & z); G = lambda x, y, z: (x & y) | (x & z) | (y & z); H = lambda x, y, z: x ^ y ^ z
    ml = len(msg) * 8; msg += b'\x80'; msg += b'\x00' * ((56 - len(msg) % 64) % 64); msg += struct.pack('<Q', ml)
    h = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476]
    for off in range(0, len(msg), 64):
        X = list(struct.unpack('<16I', msg[off:off+64])); a, b, c, d = h
        for i in range(16):
            k = i; s = [3, 7, 11, 19][i % 4]
            a, b, c, d = d, _rol((a + F(b, c, d) + X[k]) & 0xffffffff, s), b, c
        for i in range(16):
            k = (i % 4) * 4 + i // 4; s = [3, 5, 9, 13][i % 4]
            a, b, c, d = d, _rol((a + G(b, c, d) + X[k] + 0x5a827999) & 0xffffffff, s), b, c
        for i in range(16):
            k = [0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15][i]; s = [3, 9, 11, 15][i % 4]
            a, b, c, d = d, _rol((a + H(b, c, d) + X[k] + 0x6ed9eba1) & 0xffffffff, s), b, c
        h = [(x + y) & 0xffffffff for x, y in zip(h, [a, b, c, d])]
    return struct.pack('<4I', *h)

def sha0(msg: bytes) -> bytes:
    ml = len(msg) * 8; msg += b'\x80'; msg += b'\x00' * ((56 - len(msg) % 64) % 64); msg += struct.pack('>Q', ml)
    h = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]
    for off in range(0, len(msg), 64):
        w = list(struct.unpack('>16I', msg[off:off+64]))
        for i in range(16, 80): w.append(w[i-3] ^ w[i-8] ^ w[i-14] ^ w[i-16])   # SHA-0: no rotate
        a, b, c, d, e = h
        for i in range(80):
            if i < 20: f, k = (b & c) | (~b & d), 0x5A827999
            elif i < 40: f, k = b ^ c ^ d, 0x6ED9EBA1
            elif i < 60: f, k = (b & c) | (b & d) | (c & d), 0x8F1BBCDC
            else: f, k = b ^ c ^ d, 0xCA62C1D6
            a, b, c, d, e = (_rol(a, 5) + f + e + k + w[i]) & 0xffffffff, a, _rol(b, 30), c, d
        h = [(x + y) & 0xffffffff for x, y in zip(h, [a, b, c, d, e])]
    return struct.pack('>5I', *h)

def ripemd128(msg: bytes) -> bytes:
    f = [lambda x,y,z: x^y^z, lambda x,y,z: (x&y)|(~x&z), lambda x,y,z: (x|~y)^z, lambda x,y,z: (x&z)|(y&~z)]
    K = [0x00000000, 0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC]; Kp = [0x50A28BE6, 0x5C4DD124, 0x6D703EF3, 0x00000000]
    r = [list(range(16)), [7,4,13,1,10,6,15,3,12,0,9,5,2,14,11,8], [3,10,14,4,9,15,8,1,2,7,0,6,13,11,5,12], [1,9,11,10,0,8,12,4,13,3,7,15,14,5,6,2]]
    rp = [[5,14,7,0,9,2,11,4,13,6,15,8,1,10,3,12], [6,11,3,7,0,13,5,10,14,15,8,12,4,9,1,2], [15,5,1,3,7,14,6,9,11,8,12,2,10,0,4,13], [8,6,4,1,3,11,15,0,5,12,2,13,9,7,10,14]]
    s = [[11,14,15,12,5,8,7,9,11,13,14,15,6,7,9,8], [7,6,8,13,11,9,7,15,7,12,15,9,11,7,13,12], [11,13,6,7,14,9,13,15,14,8,13,6,5,12,7,5], [11,12,14,15,14,15,9,8,9,14,5,6,8,6,5,12]]
    sp = [[8,9,9,11,13,15,15,5,7,7,8,11,14,14,12,6], [9,13,15,7,12,8,9,11,7,7,12,7,6,15,13,11], [9,7,15,11,8,6,6,14,12,13,5,14,13,13,7,5], [15,5,8,11,14,14,6,14,6,9,12,9,12,5,15,8]]
    ml = len(msg) * 8; msg += b'\x80'; msg += b'\x00' * ((56 - len(msg) % 64) % 64); msg += struct.pack('<Q', ml)
    h = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476]
    for off in range(0, len(msg), 64):
        X = struct.unpack('<16I', msg[off:off+64]); A, B, C, D = h; Ap, Bp, Cp, Dp = h
        for j in range(4):
            for i in range(16):
                T = _rol((A + f[j](B, C, D) + X[r[j][i]] + K[j]) & 0xffffffff, s[j][i]); A, D, C, B = D, C, B, T
                T = _rol((Ap + f[3-j](Bp, Cp, Dp) + X[rp[j][i]] + Kp[j]) & 0xffffffff, sp[j][i]); Ap, Dp, Cp, Bp = Dp, Cp, Bp, T
        T = (h[1] + C + Dp) & 0xffffffff; h = [T, (h[2] + D + Ap) & 0xffffffff, (h[3] + A + Bp) & 0xffffffff, (h[0] + B + Cp) & 0xffffffff]
    return struct.pack('<4I', *h)

if __name__ == "__main__":
    assert md4(b"abc").hex() == "a448017aaf21d8525fc10ae87aa6729d"
    assert sha0(b"abc").hex() == "0164b8a914cd2a5e74c4f7ff082c4d97f1edf880"
    assert ripemd128(b"abc").hex() == "c14a12199c66e4ba84636b0f69144c77"
    print("test vectors ok")
