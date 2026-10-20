"""GF(2^m) binary curve y^2 + xy = x^3 + a x^2 + b. Check n*G = O, compute G/2, scan k*G and G/k for short coordinates."""
import sys
def gf_mul(a,b,poly,m):
    r=0
    while b:
        if b&1: r^=a
        b>>=1; a<<=1
        if a>>m: a^=poly
    return r
def gf_inv(a,poly,m):
    # a^(2^m-2) by square-and-multiply (Fermat); ~2m multiplications, fast enough here
    r=1; e=(1<<m)-2; b=a
    while e:
        if e&1: r=gf_mul(r,b,poly,m)
        b=gf_mul(b,b,poly,m); e>>=1
    return r
class Curve:
    def __init__(s,m,poly,a,b,n,h): s.m,s.poly,s.a,s.b,s.n,s.h=m,poly,a,b,n,h
    def on(s,P):
        x,y=P; L=gf_mul(y,y,s.poly,s.m)^gf_mul(x,y,s.poly,s.m)
        R=gf_mul(gf_mul(x,x,s.poly,s.m),x,s.poly,s.m)^gf_mul(s.a,gf_mul(x,x,s.poly,s.m),s.poly,s.m)^s.b
        return L==R
    def neg(s,P): return None if P is None else (P[0],P[0]^P[1])
    def add(s,P,Q):
        if P is None: return Q
        if Q is None: return P
        x1,y1=P; x2,y2=Q; mul=lambda a,b: gf_mul(a,b,s.poly,s.m)
        if x1==x2:
            if y1^y2==x1 or x1==0: return None   # P = -Q
            lam=x1^mul(y1,gf_inv(x1,s.poly,s.m)); x3=mul(lam,lam)^lam^s.a
            y3=mul(x1,x1)^mul(lam^1,x3); return (x3,y3)
        lam=mul(y1^y2,gf_inv(x1^x2,s.poly,s.m)); x3=mul(lam,lam)^lam^x1^x2^s.a
        y3=mul(lam,x1^x3)^x3^y1; return (x3,y3)
    def mul(s,k,P):
        R=None
        while k:
            if k&1: R=s.add(R,P)
            P=s.add(P,P); k>>=1
        return R
def poly_from(m,taps): 
    p=1<<m
    for t in taps: p|=1<<t
    return p
CURVES={}
def run(name,C,G,K=2**16,out=None):
    assert C.on(G), name+" G not on curve"
    assert C.mul(C.n,G) is None, name+" n*G != O"
    half=C.mul((C.n+1)//2,G); assert C.add(half,half)==G
    m=C.m; thr=m-32; best=(m+1,""); found=[]
    def rec(k,P,lab):
        nonlocal best
        x,y=P; bx=x.bit_length(); by=min(y,y^x).bit_length()  # y of -P is x+y
        if bx<best[0]: best=(bx,lab)
        if bx<=thr or by<=thr: found.append(f"{lab}: x bits {bx}, y bits {by}")
    lines=[f"== {name}: m={m}, n*G=O ok", f"   G/2 x = {half[0]:x}  ({half[0].bit_length()} bits), y = {half[1]:x} ({half[1].bit_length()} bits)"]
    Q=G
    for k in range(2,K+1):
        Q=C.add(Q,G); rec(k,Q,f"{k}*G")
    ninv=lambda k: pow(k,-1,C.n)
    # G/k via repeated: G/k = ninv(k)*G ; expensive per k, so do a smaller range unless K small
    KD = 2**12
    for k in range(2,KD+1):
        rec(k,C.mul(ninv(k),G),f"G/{k}")
    lines.append(f"   shortest x among k*G (k<=2^16) and G/k (k<=2^12): {best[0]} bits at {best[1]}  (random expectation for 2^16+2^12 samples ~ {m-16} bits)")
    lines.append(f"   coordinates >=32 bits short: {found if found else 'none'}")
    s="\n".join(lines); print(s, flush=True)
    if out: out.write(s+"\n"); out.flush()
if __name__=="__main__":
    import json
    params=json.load(open("bincurves.json"))
    with open("binpts.out","a") as out:
        for name in sys.argv[1:]:
            d=params[name]; C=Curve(d["m"],poly_from(d["m"],d["taps"]),int(d["a"],16),int(d["b"],16),int(d["n"],16),d["h"])
            run(name,C,(int(d["Gx"],16),int(d["Gy"],16)),out=out)
