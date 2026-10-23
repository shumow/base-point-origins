# Archival pass — SEC 2 drafts and the provenance of the secp*k1 base points

*Started 2026-10-23 (HANDOFF §4.5). This is the catalog-and-plan phase. The goal
is documentary, not computational: find a source that either (a) shows an
**earlier or different** generator G for a secp\*k1 curve — which dates when the
constant was fixed — or (b) **states the derivation** of the base points — which
ends the search. Everything below separates established fact from lead-to-verify,
and carries the source URL. Nothing here has been fetched in full from this
session (see "Network constraint"); the version dates and quotations are from web
search snippets and must be confirmed against the primary PDFs.*

## Decision rule (what each outcome means)

- A draft or prior document whose secp\*k1 **G differs** from the published value
  ⇒ the constant was chosen at/after that draft; brackets the date and may expose
  an intermediate form.
- A document that **states how G (or x(G/2)) was derived** for the Koblitz curves
  ⇒ the search is over.
- A draft that already carries **today's G with no derivation** ⇒ pushes the
  origin earlier and narrows where the recipe was recorded (private Certicom
  material, X9.62 working notes).

## Baseline already established in-repo (do not re-fetch)

- SEC 2 **v1.0 (2000-09-20)** and **v2.0 (2010-01-27)** parameters were fetched by
  an earlier session (HANDOFF §6) and every secp\*k1 (p,a,b,G,n,h) verified by
  n·G = O in `scripts/secg_scan.py`. So the published G values are unchanged from
  v1.0 onward; the open question is strictly **before 2000-09-20**.
- Published generators (baseline for any diff), x(G/2) structure in `notes/record.md`:
  ```
  secp160k1 Gx=3b4c382ce37aa192a4019e763036f4f5dd4d7ebb
  secp192k1 Gx=db4ff10ec057e9ae26b07d0280b7f4341da5d1b1eae06c7d
  secp224k1 Gx=a1455b334df099df30fc28a169a467e9e47075a90f7e650eb6b7a45c
  secp256k1 Gx=79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
  ```

## Timeline of the standards (dates to confirm against the PDFs)

| Document | Date | Base-point content / relevance |
|---|---|---|
| ANSI X9.62 | 1998 | The curve/base-point **generation method** SEC 1 defers to. Ultimate primary source for the procedure. Paywalled; drafts circulated in IEEE P1363. |
| **"Recommended Elliptic Curve Domain Parameters"**, Certicom working draft (probably **GEC 1**) | **1999** (reported) | The title is SEC 2's own; a 1999 draft of the curve tables is the pre-SEC-2 document that would carry the secp\*k1 generators. **Top target.** Surfaced only as a citation (catalog item 6); identity as GEC 1 and its mirror URL to confirm. |
| **WAP WTLS specification** (WAP-199, `SPEC-WTLS-19991105`) | **1999-11-05** | Its curve appendix gives full parameters, base points included, for curves 1 and 3–12: 3 = sect163k1 (K-163), 10 = sect233k1, 11 = sect233r1, 6 = secp112r1, 12 = secp224r1, 5 = c2pnb163v1, and 7 = a 160-bit SECG r-curve (secp160r2 by OpenSSL's curve table, secp160r1 by std-curves — the PDF decides, see finding 3). Ten months before SEC 2 v1.0, so it dates those generators, including K-163's short half and the secp160r pair of §2.2. |
| **GEC 2: Test Vectors for SEC 1** (Certicom) | reported **v0.3, Sept 1999** | Pre-SEC-2 Certicom doc; ECDSA test vectors on secp160r1. Worth a look for a worked base-point example, but as a test-vector document it is unlikely to table the k-curve generators. |
| SEC 1 v1.0 | 2000-09-20 | "Generated verifiably at random using SHA-1 as described in ANSI X9.62" — defers the method to X9.62; does not give the k-curve base-point derivation. |
| **SEC 2 v1.0** | 2000-09-20 | Earliest public SEC curve tables. States only the **curve** selection for Koblitz curves ("repeatedly selecting parameters admitting an efficiently computable endomorphism until a prime-order curve was found") — **no base-point derivation stated**. |
| SEC 2 v1.5 | working draft 2005-09-27 | Intermediate; worth diffing for any changed note. |
| SEC 1 v2.0 | 2009 | Has a section titled **"Verifiably Random Curves and Base Point Generators"**, base points "partly derived from a secure hash of a seed value" — but this is the r-curve procedure; check whether it says anything about the k-curve generators. |
| SEC 2 v2.0 | 2010-01-27 | Dropped ≤160-bit curves; k-curve G unchanged. |

## Findings from this pass (search-level, to confirm on the PDFs)

1. **The standards never state a base-point derivation for the Koblitz curves.**
   SEC 2 v1.0 gives only the curve-selection method; SEC 1 defers generation to
   X9.62. The one explicit "Base Point Generators" text (SEC 1 v2.0) is about the
   verifiably-random r-curves. This is consistent with the whole premise: the
   k-curve base points are unexplained in the public record.
2. **Popular "G is derived deterministically / rigid" claims are unsourced.**
   Multiple secondary pages assert secp256k1's G is "derived deterministically";
   none cite a derivation. That folk claim is exactly the gap this project is
   filling — worth a line in any write-up.
3. **The curves travelled under several names**, so drafts may table them under
   aliases: ANSI X9.63 `ansip*k1` / `ansip160r1` / `ansit*k1`, NIST `K-*`, and the
   WAP WTLS ids (`wap-wsg-idm-ecid-wtlsN`). Search WTLS/WAP and X9.63 drafts under
   those ids, not "secp"/"sect". **Caution on wtls7** (corrected 23 Oct): this
   note first said secp160r1 = wtls7, following std-curves' alias table. OpenSSL's
   `crypto/ec/ec_curve.c` disagrees: it maps `NID_wap_wsg_idm_ecid_wtls7` to the
   `_EC_SECG_PRIME_160R2` parameters (p = 2¹⁶⁰ − 2³² − 21389), while std-curves'
   `wtls/curves.json` gives wtls7 secp160r1's p = 2¹⁶⁰ − 2³¹ − 1 and G. Two
   catalogs, two answers; the 1999 WTLS PDF settles it, and whoever fetches it
   should compare curve 7's p and G against both. The undisputed WTLS ids are
   wtls3 = sect163k1 (K-163), wtls10 = sect233k1, wtls11 = sect233r1, wtls6 =
   secp112r1, wtls12 = secp224r1, wtls5 = c2pnb163v1; wtls1, 8, 9 are WTLS-only
   curves (wtls8 and wtls9 have G = (1, …)).
4. **SECG was formed by Certicom in 1998 or 1999** (sources disagree); SEC 1 and
   SEC 2 are its first two standards (2000). The 1999 Certicom drafts (GEC 1/GEC 2)
   and the Nov 1999 WTLS specification predate both.

## Prioritized target catalog (URLs + reachability)

Priority is by how decisively the source could date the constant or state its
derivation. "Reachable here" = fetchable from this sandbox (GitHub / package
registries only); everything else is for a networked session or hand-drop.

1. **Certicom's 1999 working draft "Recommended Elliptic Curve Domain Parameters"** — probably GEC 1, in which case the mirror would be `http://rfc.nop.hu/secg/gec1.pdf` next to gec2.pdf; identity to confirm. The pre-SEC-2 curve tables themselves: diff every secp\*k1 and sect\*k1 G against the baseline above. *Not reachable here.*
1b. **WAP WTLS specification, 5 Nov 1999** — `https://cdimage.debian.org/mirror/archive/ftp.sunet.se/pub/security/docs/PCA/TLS/SPEC-WTLS-19991105.pdf` (Debian archive mirror; also the Open Mobile Alliance's WAP archive as WAP-199-WTLS). Read the curve appendix: compare curve 3 (sect163k1), 10 (sect233k1) and 7 (secp160r1 or r2, finding 3) base points with the baseline; any match dates that generator to 1999, any difference is an earlier form. *Not reachable here (tried 23 Oct: DNS denied).*
1c. **GEC 2: Test Vectors for SEC 1, Certicom, v0.3 Sept 1999** — `http://rfc.nop.hu/secg/gec2.pdf` (mirror). secp160r1 test vectors; check for a worked base-point example, not expected to table the k-curves. *Not reachable here.*
2. **ANSI X9.62:1998** base-point generation clause (and its IEEE P1363 draft form). The method SEC 1 defers to; decides whether the k-curves even followed a stated procedure. Paywalled; seek the P1363 working draft. *Not reachable here.*
3. **Earliest Wayback captures of secg.org** (pre- and circa 2000-09-20): look for a SEC 2 draft < v1.0 or a different G. Recipe: `https://web.archive.org/web/0/http://www.secg.org/` for the earliest capture; CDX `https://web.archive.org/cdx/search/cdx?url=secg.org*&collapse=urlkey&output=text&filter=original:.*[Ss][Ee][Cc]2.*`; append `id_` to a timestamp for the raw PDF. *Wayback is blocked here.*
4. **SEC 1 v2.0 §"Verifiably Random Curves and Base Point Generators"** — `https://www.secg.org/sec1-v2.pdf` (also mobilefish mirror). Read for any k-curve base-point wording. *Not reachable here.*
5. **SEC 2 v1.5 working draft (2005-09-27)** — `http://rfc.nop.hu/secg/sec2.pdf` (mirror). Diff notes vs v1.0/v2.0. *Not reachable here.*
6. **IEEE P1363 working-group archives** (`grouper.ieee.org/groups/1363/`) — a result surfaced `https://grouper.ieee.org/groups/1904/4/email/pdf7kia4jRaeI.pdf` citing "Recommended Elliptic Curve Domain Parameters"; identity/date unconfirmed — this is the citation behind item 1 and is most likely GEC 1. *Not reachable here.*
7. **Secondary catalogs for cross-checks** (provenance notes, aliases, not drafts):
   SafeCurves `https://safecurves.cr.yp.to/refs.html`; DiSSECT `https://dissect.crocs.fi.muni.cz/standards/secg`; std-curves `https://std.neuromancer.sk/secg/secp256k1/`. *Not reachable over the web here, but **std-curves is done**: J08nY/std-curves was added (git-readable) and its SECG section vendored at `references/std-curves/secg-curves.json` (commit `77fe6e3`, MIT). `scripts/crosscheck_stdcurves.py` confirms all 26 overlapping curves (10 prime, 6 sect\*k1, 10 NIST binary) agree field-for-field with this repo — 182 fields, 0 mismatches — so the generators under analysis rest on a second independent catalog. See "Cross-check" below.*

## Cross-check against std-curves (done 23 Oct 2026)

`scripts/crosscheck_stdcurves.py` → `results/crosscheck-stdcurves.txt` (controls
`tests/test_crosscheck.py`, 5 tests incl. a planted-mismatch detection). Every
(p/poly, a, b, Gx, Gy, n, h) for the 10 SECG prime curves, the 6 sect\*k1 binary
curves and the 10 NIST binary curves (matched by std-curves alias) matches this
repo's `secg_scan.CURVES`, `sectk_2020_checks.SECTK` and `data/bincurves.json`.
So nothing in the base-point analysis rests on a lone transcription of G.

Aliases recorded for the archival trail (search drafts under these too): the
prime Koblitz curves carry only `x963/ansip*k1` (ANSI X9.63) — no NIST or WTLS
alias — while the binary Koblitz curves carry `nist/K-*`, `x963/ansit*k1`, and
some a WTLS id (sect163k1 = `wtls/wap-wsg-idm-ecid-wtls3`, sect233k1 = `wtls10`).
So secp256k1 and the other prime k-curves are Certicom/ANSI-X9.63 only, which
narrows where an early draft of *their* base points could live. One alias in the
vendored table is contested: std-curves gives wtls7 to secp160r1, OpenSSL gives
it secp160r2's parameters (finding 3 above); the parameter cross-check itself is
unaffected, since it compares SECG entries by SECG name, not by alias.

## DiSSECT checked for base-point provenance (done 23 Oct 2026)

`crocs-muni/DiSSECT` (the CRoCS curve-analysis framework behind
dissect.crocs.fi.muni.cz) was added (git-readable) and searched for any stated
derivation of the base points. **Finding: none.** It carries no prose provenance
notes and no derivation; greps for "Koblitz", "seed", "ANSI", "Certicom" hit only
utility code, and its curve database is the same neuromancer/std-curves catalog
already vendored and cross-checked (no `.gitmodules`; README: "taken from our
sister project neuromancer.sk/std"), so it adds no new parameter data.

What DiSSECT *does* contribute is analytic, and it is directly on point: the
trait `dissect/traits/multiples_x.py` independently formalises this project's
scan — for k = 1..10 it computes the bitlength of x of (1/k mod n)·G and the
"difference" from the group bitlength. At **k = 2 this is x(G/2)**, the
half-generator. `scripts/dissect_multiples_x.py` (controls
`tests/test_dissect_multiples_x.py`) transcribes the trait and confirms its k=2
value equals the recorded x(G/2) on secp160k1/192k1/224k1/256k1 and K-163; on
secp256k1 only k=2 is short (166 bits, ~90 below the group) while k=1,3..10 are
full-size. So the CRoCS group's public trait measures exactly the short
half-generator anomaly this repo studies — independent corroboration that the
coordinate is anomalous — but, like every public source surveyed, it records the
anomaly without a derivation. Related structure traits worth a look in their live
database (not fetchable here): `hamming_x` (low-Hamming-weight x-coordinates) and
`x962_invariant` (a³/b², the X9.62 curve invariant; 0 on the a=0 k-curves).

## Network constraint (why the fetch step is not done here)

WebSearch works, but WebFetch in this environment resolves only GitHub and
package-registry hosts (the egress policy denies all other DNS: secg.org,
web.archive.org, safecurves, rfc.nop.hu, ieee.org all returned ENOTFOUND, and
web.archive.org is additionally blocked at the tool). So the PDFs above cannot be
retrieved from this session. This matches the earlier note in
`references/README.md` ("the sandbox network reaches GitHub and package
registries only"). The pass is set up here; the retrieval is a hand-drop or a
networked session, exactly as the Stevens papers and the rump slides were handled.

## Next actions (for whoever has network)

1. Pull the **1999 "Recommended Elliptic Curve Domain Parameters" draft (GEC 1?)**
   and the **Nov 1999 WTLS specification**, and grep their parameter tables for
   the secp\*k1 / sect\*k1 Gx values above; record whether each base point is
   present and identical. These are the two most informative fetches; GEC 2 is a
   distant third.
2. Pull the **earliest Wayback secg.org** capture and any SEC 2 draft < v1.0; diff
   every secp\*k1 G against the baseline.
3. Read **SEC 1 v2.0 §"Verifiably Random Curves and Base Point Generators"** and
   **ANSI X9.62:1998**'s base-point clause; quote any sentence bearing on how a
   base point (not the curve) is produced.
4. Drop retrieved PDFs under `references/archival/` with a one-line provenance each
   (source URL, capture date), and log the diff result back into this file.
