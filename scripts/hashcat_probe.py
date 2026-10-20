"""Decide whether hashcat's SHA-1 matcher confirms the leading 32-bit digest word (register a).

Why: make_targets.py enumerates all 256 unknown top-byte values of the secp core into the *leading* word of each
target digest. hashcat (v7, both optimized and pure kernels) reports far fewer "unique digests" than the file contains
because it reduces its hash table on words 1..4 and treats the leading word specially. If it does NOT re-confirm the
leading word on a bucket hit, the 256-way enumeration is unnecessary (and the search is blind to the top byte anyway,
which is what we want: a hit matches whatever the real top byte is). If it DOES confirm it losslessly, the full list is
required and correct. This probe distinguishes the two, and guards against the dangerous third case (lossy dedup that
keeps one leading word and still confirms it -> silent false negative).

It writes a one-line target: SHA-1("Certicom") with its leading word overwritten by deadbeef, i.e. a digest that is
WRONG in the leading word and correct in words 1..4. Then run hashcat against the existing wordlist, which contains the
real "Certicom":

    python3 scripts/hashcat_probe.py targets
    hashcat -m 100 -a 0 --potfile-path targets/probe.pot targets/probe_leadingword.txt wordlists/certicom.txt

Interpretation:
  * CRACKED ("deadbeef...:Certicom")  -> hashcat ignores the leading word. We can shrink the target list 256x
    (drop the top-byte loop in make_targets) and a real hit is caught regardless of its top byte.
  * EXHAUSTED (no crack)              -> hashcat confirms the full digest. Keep the 256-way enumeration; it is correct.
Either way the planted control in make_targets must still crack; this probe only tells us whether the top-byte loop is
load-bearing.
"""
import hashlib, sys
from pathlib import Path

def main(outdir="targets"):
    out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    real = hashlib.sha1(b"Certicom").digest()
    corrupted = bytes.fromhex("deadbeef") + real[4:]          # leading word wrong, words 1..4 correct
    assert corrupted != real and corrupted[4:] == real[4:]
    (out / "probe_leadingword.txt").write_text(corrupted.hex() + "\n")
    print(f"wrote {out}/probe_leadingword.txt")
    print(f"  real      SHA1('Certicom') = {real.hex()}")
    print(f"  corrupted (lead word only) = {corrupted.hex()}")
    print("run: hashcat -m 100 -a 0 --potfile-path %s/probe.pot %s/probe_leadingword.txt wordlists/certicom.txt" % (outdir, outdir))
    print("  CRACKED  -> hashcat ignores the leading word (shrink the target list 256x)")
    print("  EXHAUSTED-> hashcat confirms the full digest (keep the 256-way top-byte enumeration)")

if __name__ == "__main__":
    main(*sys.argv[1:2])
