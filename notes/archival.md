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
| **GEC 2: Test Vectors for SEC 1** (Certicom) | reported **v0.3, Sept 1999** | Pre-SEC-2 Certicom doc; uses secp160r1 with ECDSA. **Top target** — if it tabulates secp\*k1 G, it dates them to 1999, a year before SEC 2. A test-vector doc may also show a worked base-point example. |
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
   aliases: secp160r1 = `wap-wsg-idm-ecid-wtls7` (WTLS/WAP) = `ansip160r1`
   (ANSI X9.63). Search WTLS/WAP and X9.63 drafts under the WTLS ids, not "secp".
4. **SECG was formed by Certicom in 1999**; SEC 1 and SEC 2 are its first two
   standards (2000). GEC 2 (1999) predates both and is the earliest Certicom
   parameter/test-vector document surfaced so far.

## Prioritized target catalog (URLs + reachability)

Priority is by how decisively the source could date the constant or state its
derivation. "Reachable here" = fetchable from this sandbox (GitHub / package
registries only); everything else is for a networked session or hand-drop.

1. **GEC 2: Test Vectors for SEC 1, Certicom, v0.3 Sept 1999** — `http://rfc.nop.hu/secg/gec2.pdf` (mirror). Check for any secp\*k1 G table or worked base-point example. *Not reachable here.*
2. **ANSI X9.62:1998** base-point generation clause (and its IEEE P1363 draft form). The method SEC 1 defers to; decides whether the k-curves even followed a stated procedure. Paywalled; seek the P1363 working draft. *Not reachable here.*
3. **Earliest Wayback captures of secg.org** (pre- and circa 2000-09-20): look for a SEC 2 draft < v1.0 or a different G. Recipe: `https://web.archive.org/web/0/http://www.secg.org/` for the earliest capture; CDX `https://web.archive.org/cdx/search/cdx?url=secg.org*&collapse=urlkey&output=text&filter=original:.*[Ss][Ee][Cc]2.*`; append `id_` to a timestamp for the raw PDF. *Wayback is blocked here.*
4. **SEC 1 v2.0 §"Verifiably Random Curves and Base Point Generators"** — `https://www.secg.org/sec1-v2.pdf` (also mobilefish mirror). Read for any k-curve base-point wording. *Not reachable here.*
5. **SEC 2 v1.5 working draft (2005-09-27)** — `http://rfc.nop.hu/secg/sec2.pdf` (mirror). Diff notes vs v1.0/v2.0. *Not reachable here.*
6. **IEEE P1363 working-group archives** (`grouper.ieee.org/groups/1363/`) — a result surfaced `https://grouper.ieee.org/groups/1904/4/email/pdf7kia4jRaeI.pdf` citing "Recommended Elliptic Curve Domain Parameters"; identity/date unconfirmed. *Not reachable here.*
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
narrows where an early draft of *their* base points could live.

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

1. Pull **GEC 2 (Sept 1999)** and grep its parameter tables for the secp\*k1 Gx
   values above and for `secp*k1`; record whether the base points are present and
   identical. This is the single most informative fetch.
2. Pull the **earliest Wayback secg.org** capture and any SEC 2 draft < v1.0; diff
   every secp\*k1 G against the baseline.
3. Read **SEC 1 v2.0 §"Verifiably Random Curves and Base Point Generators"** and
   **ANSI X9.62:1998**'s base-point clause; quote any sentence bearing on how a
   base point (not the curve) is produced.
4. Drop retrieved PDFs under `references/archival/` with a one-line provenance each
   (source URL, capture date), and log the diff result back into this file.
