# References

## `crypto2019-rump/` — the 2019–20 investigation (added 22 Oct 2026)

Mailbox surveys, a reconstructed Sage script and a synthesis README for the Heninger–Scholl–Shumow Crypto 2019 rump-session work and its 2020 follow-up. Start with [`crypto2019-rump/README.md`](crypto2019-rump/README.md). The slide deck is missing on purpose (the mailbox copy is IRM-encrypted); the clean copy is in Dan's Gmail.

## Hash-cryptanalysis papers

PDFs to add here. Two automated sessions (20 Oct) could not download them: the sandbox network reaches GitHub and package registries only, and the fetch tool returns extracted text, not the file. Drop them in by hand or attach them in a chat; exact URLs:

- Thesis: https://marc-stevens.nl/research/papers/PhD%20Thesis%20Marc%20Stevens%20-%20Attacks%20on%20Hash%20Functions%20and%20Applications.pdf
- CRYPTO 2013: https://marc-stevens.nl/research/papers/C13-S.pdf (ePrint 2013/358)
- USENIX 2017: https://www.usenix.org/system/files/conference/usenixsecurity17/sec17-stevens.pdf (ePrint 2017/173)

Suggested filenames: `stevens-2012-thesis.pdf`, `stevens-2013-counter-cryptanalysis.pdf`, `stevens-shumow-2017-unavoidable-conditions.pdf`.

1. **Marc Stevens**, *Attacks on Hash Functions and Applications*, PhD thesis, Leiden University, 2012. https://marc-stevens.nl/research/ (thesis PDF linked from the research page). Chapters on MD5/SHA-1 differential cryptanalysis; the step-function inversion and working-state reconstruction used throughout.
2. **Marc Stevens**, *Counter-cryptanalysis*, CRYPTO 2013. IACR ePrint 2013/358, https://eprint.iacr.org/2013/358. Detects collision attacks from a single message by recomputing alternate-message working states forwards and backwards from a known execution — the forward/backward last-block technique.
3. **Marc Stevens, Daniel Shumow**, *Speeding up detection of SHA-1 collision attacks using unavoidable attack conditions*, USENIX Security 2017. IACR ePrint 2017/173, https://eprint.iacr.org/2017/173. Reduces the 2013 check to a handful of "unavoidable conditions" per disturbance vector; same forward/backward machinery.

## Ingestion note — DONE 20 Oct from the online texts; result in `notes/hash-angle.md` §2a. Re-read thesis Ch. 7–8 from the PDF when available.

Read all three with one question in mind: exactly what the forward/backward computation on the last block takes as known and produces as output. The answer, as far as this session can state it without the PDFs in hand, is in `notes/hash-angle.md` §2: the SHA-1 *step* is a permutation given the message word, so from any five consecutive working states plus the message block the whole execution is reconstructible in both directions and the input IHV is recovered from the *final working state*; the Davies–Meyer feed-forward means the output chaining value alone does not yield that final working state unless the input IHV is known — which, for a single-block message, it is (the standard IV). Check that statement against the papers' Algorithm/Section where the alternate IHV_in is recomputed, correct `hash-angle.md` if they say more, and record what the papers say about the cost of the backward recomputation (it should be a handful of steps, not a full compression).
