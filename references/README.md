# References

PDFs to add here (the automated session that created this directory could not download them — its network reaches GitHub only):

1. **Marc Stevens**, *Attacks on Hash Functions and Applications*, PhD thesis, Leiden University, 2012. https://marc-stevens.nl/research/ (thesis PDF linked from the research page). Chapters on MD5/SHA-1 differential cryptanalysis; the step-function inversion and working-state reconstruction used throughout.
2. **Marc Stevens**, *Counter-cryptanalysis*, CRYPTO 2013. IACR ePrint 2013/358, https://eprint.iacr.org/2013/358. Detects collision attacks from a single message by recomputing alternate-message working states forwards and backwards from a known execution — the forward/backward last-block technique.
3. **Marc Stevens, Daniel Shumow**, *Speeding up detection of SHA-1 collision attacks using unavoidable attack conditions*, USENIX Security 2017. IACR ePrint 2017/173, https://eprint.iacr.org/2017/173. Reduces the 2013 check to a handful of "unavoidable conditions" per disturbance vector; same forward/backward machinery.

## Ingestion note (for a text session)

Read all three with one question in mind: exactly what the forward/backward computation on the last block takes as known and produces as output. The answer, as far as this session can state it without the PDFs in hand, is in `notes/hash-angle.md` §2: the SHA-1 *step* is a permutation given the message word, so from any five consecutive working states plus the message block the whole execution is reconstructible in both directions and the input IHV is recovered from the *final working state*; the Davies–Meyer feed-forward means the output chaining value alone does not yield that final working state unless the input IHV is known — which, for a single-block message, it is (the standard IV). Check that statement against the papers' Algorithm/Section where the alternate IHV_in is recomputed, correct `hash-angle.md` if they say more, and record what the papers say about the cost of the backward recomputation (it should be a handful of steps, not a full compression).
