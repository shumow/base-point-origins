"""Run a wordlist (one base string per line) through the k163 variant machinery and both matchers:
the secp*k1 148-bit core (SHA-1 family) and the K-163 value (MD5 family). usage: wordlist_search.py words.txt"""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "k163"))
from hashes import md4, sha0, ripemd128
from strings import variants
import secg_core_search as core
import search as k163

H160 = core.HASHES
H128 = {"md5": lambda b: hashlib.md5(b).digest(), "md4": md4, "ripemd128": ripemd128}
def main(path):
    n = 0; hits = []
    seen = set()
    for line in open(path, encoding="utf-8", errors="ignore"):
        s = line.rstrip("\n")
        if not s: continue
        for v in variants(s):
            if v in seen: continue
            seen.add(v)
            for enc in ("ascii", "utf-16-le", "utf-16-be"):
                try: b = v.encode(enc)
                except Exception: continue
                for suffix in (b"",) + tuple(cb for c in range(4) for cb in (bytes([c]), str(c).encode(), c.to_bytes(4, "big"))):
                    m = b + suffix
                    for hn, hf in H160.items():
                        r = core.check(hf(m)); n += 1
                        if r: hits.append((v, enc, suffix, hn, r)); print("HIT core", repr(v), enc, suffix, hn, r, flush=True)
                    for hn, hf in H128.items():
                        r = k163.match(hf(m)); n += 1
                        if r: hits.append((v, enc, suffix, hn, r)); print("HIT k163", repr(v), enc, suffix, hn, r, flush=True)
    print(f"done: {n} evaluations, {len(hits)} hits")
if __name__ == "__main__": main(sys.argv[1])
