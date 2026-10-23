# `std-curves/` — independent parameter source for cross-checking

`secg-curves.json` is the SECG section of **J08nY/std-curves**, a machine-readable
catalog of standardized elliptic curves maintained by Jan Jančar and Vladimír
Sedláček (the CRoCS group's curve database, used by DiSSECT/ECTester).

- Upstream: https://github.com/J08nY/std-curves (`secg/curves.json`)
- Vendored at commit `77fe6e3585ca2c2225b59d7df24b7c775437276f` (shallow clone, 2026-10-23)
- Licence: MIT (see `LICENSE`), © 2018–2020 Jan Jancar, Vladimir Sedlacek

Why it's here: it gives p, a, b, the base point G, the order n and the cofactor
for all 33 SECG curves, assembled independently of this repo's own parameter
tables (`scripts/secg_scan.py` CURVES, `data/bincurves.json`,
`scripts/sectk_2020_checks.py` SECTK). `scripts/crosscheck_stdcurves.py` compares
the two field-by-field so the generators this project analyses rest on a second
source, not just transcription. It also carries the curves' aliases (ANSI X9.62/
X9.63, WTLS/WAP, NIST), useful for the archival pass (`notes/archival.md`).
One alias is contested: std-curves gives `wap-wsg-idm-ecid-wtls7` to secp160r1
(and its `wtls/curves.json` carries secp160r1's p and G under that name), while
OpenSSL's `crypto/ec/ec_curve.c` maps the same NID to secp160r2's parameters.
The 1999 WTLS specification decides; until then treat the wtls7 alias as unsettled.
The parameter cross-check compares SECG entries by SECG name, so it is unaffected.

Not redistributed as authoritative: on any disagreement the primary SEC 2 text
(verified in-repo by n·G = O) governs; the cross-check exists to catch
transcription error in either source.
