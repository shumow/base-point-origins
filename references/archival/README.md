# `archival/` — retrieved primary documents for the SEC 2 archival pass

Landing spot for PDFs and captures fetched against the target checklist in
[`../../notes/archival.md`](../../notes/archival.md) ("Remaining fetch targets").
This directory is empty until the first document is retrieved: the fetch step is
blocked in the cloud sandbox (WebFetch reaches only GitHub and package
registries), so retrieval is a hand-drop or a networked session.

When you add a file here:

1. Keep the original filename where sensible; prefix with a date if the version is
   ambiguous (e.g. `gec1-1999.pdf`, `wtls-19991105.pdf`, `secg-sec2-draft-<capturedate>.pdf`).
2. Add a line to `PROVENANCE.md` here (create it on the first drop): the local
   filename, the exact source URL, the document's own version/date, and the
   retrieval/capture date. Note if the copy is redistributable (as with the
   rump slides, confirm permission before committing a copyrighted PDF — a
   provenance line plus the extracted parameter table may be preferable to the
   PDF itself).
3. Diff its generator tables against the "Grep targets" block in
   `notes/archival.md`, and record the outcome there under a dated "Findings"
   entry: present/identical (dates that G), present/different (an earlier form —
   give the value), or a stated derivation (the search is over).

Do not commit large or licence-encumbered PDFs reflexively; when in doubt, commit
the provenance line and the extracted table, not the file.
