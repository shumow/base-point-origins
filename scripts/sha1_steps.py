"""Step-level SHA-1 with forward and backward step functions (hash-angle.md §2, deliverable 4).

Demonstrates, by computation, the two facts the hash angle rests on:
  (1) each SHA-1 step is a permutation of the 160-bit working state given the message word W_t, so the whole 80-step
      computation can be run backwards from the final working state (Stevens 2013 Alg. 2-1 step (c), Stevens–Shumow
      2017 Alg. 1 step (iii));
  (2) the Davies–Meyer feed-forward H_out = E_M(IV) + IV is what stops this from inverting the compression function: the
      final working state is H_out - H_in word-wise, so it is known only when H_in is known — which, for a single-block
      message, it is (the standard IV).
Run as a script for a self-test: forwards to the digest (checked against hashlib), backwards from H_out - IV to the IV.
"""
import hashlib, struct

MASK = 0xFFFFFFFF
IV = (0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0)
def rol(x, n): return ((x << n) | (x >> (32 - n))) & MASK
def ror(x, n): return rol(x, 32 - n)

def f_K(t, b, c, d):
    if t < 20: return (d ^ (b & (c ^ d))), 0x5A827999
    if t < 40: return (b ^ c ^ d), 0x6ED9EBA1
    if t < 60: return ((b & c) | (b & d) | (c & d)), 0x8F1BBCDC
    return (b ^ c ^ d), 0xCA62C1D6

def expand(block):
    W = list(struct.unpack(">16I", block))
    for t in range(16, 80): W.append(rol(W[t-3] ^ W[t-8] ^ W[t-14] ^ W[t-16], 1))
    return W

def step_fwd(t, state, Wt):
    a, b, c, d, e = state; f, K = f_K(t, b, c, d)
    T = (rol(a, 5) + f + e + K + Wt) & MASK
    return (T, a, rol(b, 30), c, d)

def step_bwd(t, state, Wt):
    """Inverse of step_fwd: from (A,B,C,D,E) after step t and W_t, recover the state before step t."""
    T, a, b30, c, d = state; b = ror(b30, 30); f, K = f_K(t, b, c, d)
    e = (T - rol(a, 5) - f - K - Wt) & MASK
    return (a, b, c, d, e)

def pad(msg: bytes) -> bytes:
    ml = 8 * len(msg); m = msg + b"\x80"
    m += b"\x00" * ((56 - len(m) % 64) % 64)
    return m + struct.pack(">Q", ml)

def compress(h_in, block, trace=False):
    W = expand(block); s = h_in; states = [s]
    for t in range(80):
        s = step_fwd(t, s, W[t]); states.append(s)
    h_out = tuple((x + y) & MASK for x, y in zip(h_in, s))
    return (h_out, states) if trace else h_out

def sha1(msg: bytes) -> bytes:
    p = pad(msg); h = IV
    for i in range(0, len(p), 64): h = compress(h, p[i:i+64])
    return struct.pack(">5I", *h)

def final_state_from_digest(h_out, h_in=IV):
    """E_M(h_in) = h_out - h_in word-wise. Needs h_in; for a one-block message that is the standard IV."""
    return tuple((x - y) & MASK for x, y in zip(h_out, h_in))

def run_backwards(final_state, block):
    W = expand(block); s = final_state
    for t in range(79, -1, -1): s = step_bwd(t, s, W[t])
    return s

if __name__ == "__main__":
    for msg in (b"", b"abc", b"Certicom", b"Give Bob and Jerry a raise", b"x" * 55):
        d = sha1(msg); assert d == hashlib.sha1(msg).digest(), msg
        block = pad(msg); assert len(block) == 64            # single block for len <= 55
        h_out = struct.unpack(">5I", d)
        final = final_state_from_digest(h_out)              # known because H_in = IV is known
        assert run_backwards(final, block) == IV, msg       # 80 inverse steps recover the IV
        # and a wrong block does not: the consistency check per candidate
        wrong = pad(msg + b"!")
        if len(wrong) == 64: assert run_backwards(final, wrong) != IV
    print("ok: forward matches hashlib; backward from H_out - IV recovers IV for every one-block message tested")
