"""Candidate string generator for the K-163 G/2 x-coordinate search. Yields (label, bytes)."""
import itertools, datetime

CORE = [
 # the lore
 "Give Bob and Jerry a raise", "Bob and Jerry rule", "Jerry Solinas should make a million dollars a year",
 "Give Bob and Jerry a raise.", "Bob and Jerry rule.", "Give Jerry a raise", "Give Bob a raise", "Jerry rules", "Bob rules",
 "Bob and Jerry", "Jerry and Bob", "Jerry Solinas", "Jerome Solinas", "Jerome A. Solinas", "J. Solinas", "Solinas", "jsolinas", "jasolin",
 "Bob Reiter", "Robert Reiter", "Reiter", "rreiter", "rwreite",
 # people / places
 "NSA", "National Security Agency", "Fort Meade", "Ft. Meade", "NIST", "ANSI", "X9.62", "X9F1", "ANSI X9.62", "IEEE P1363", "P1363", "SECG", "Certicom", "WAP", "WTLS", "WAP WTLS",
 "Neal Koblitz", "Koblitz", "Victor Miller", "Alfred Menezes", "Scott Vanstone", "Rich Schroeppel", "Don Johnson", "Dan Brown",
 # curve names
 "K-163", "K163", "k163", "K 163", "sect163k1", "ansit163k1", "nistk163", "NIST K-163", "Koblitz 163", "Koblitz-163", "koblitz163", "K-163 base point", "K-163 generator",
 "B-163", "B163", "sect163r2", "ansit163r2", "163", "2^163", "GF(2^163)", "F_2^163", "F2^163", "F2m 163",
 "anomalous binary curve", "ABC", "ABC-163", "anomalous", "Frobenius", "tau", "tau-adic", "TNAF",
 # generic
 "base point", "basepoint", "generator", "point", "G", "g", "P", "x", "seed", "SEED", "random", "secret", "password", "test", "hello", "hello world", "abc", "", " ",
 "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "100", "1000", "12345", "123456789", "42", "163", "1024", "2048",
 # the B-163 seed and other published constants
 "85E25BFE5C86226CDB12016F7553F9D0E693A268", "85e25bfe5c86226cdb12016f7553f9d0e693a268",
 "02FE13C0537BBC11ACAA07D793DE4E6D5E5C94EEE8", "02fe13c0537bbc11acaa07d793de4e6d5e5c94eee8",
 "C49D360886E704936A6678E1139D26B7819F7E90",
]
# dates 1997-01-01 .. 1998-12-31 in several formats
def dates():
    d = datetime.date(1997, 1, 1)
    while d <= datetime.date(1998, 12, 31):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d %B %Y", "%B %d, %Y", "%Y%m%d", "%d%m%Y", "%m%d%Y", "%y%m%d", "%b %d %Y", "%d-%b-%Y", "%A, %B %d, %Y", "%a %b %d %Y"):
            yield d.strftime(fmt)
        d += datetime.timedelta(days=1)
# unix timestamps of the four binary runs and the prime runs, as decimal and ctime strings
TIMES = [892823058, 892823264, 892823418, 892823528, 891607927, 871696354, 871002724, 872952608, 863966734, 863711343, 1984, 1997, 1998]
def time_strings():
    import time
    for t in TIMES:
        yield str(t); yield str(t // 2); yield str(t * 2); yield hex(t); yield hex(t)[2:]
        try: yield time.strftime("%a %b %d %H:%M:%S %Y", time.gmtime(t)); yield time.strftime("%a %b %d %H:%M:%S %Y\n", time.gmtime(t))
        except Exception: pass
def variants(s):
    yield s
    if s and s != s.lower(): yield s.lower()
    if s and s != s.upper(): yield s.upper()
    if s and s[:1].islower(): yield s[:1].upper() + s[1:]
    yield s + "\n"; yield s + "\r\n"; yield s + "\0"; yield s + " "; yield " " + s
    if s and not s.endswith("."): yield s + "."
    if s and not s.endswith("!"): yield s + "!"
def all_strings():
    seen = set()
    for src in (CORE, dates(), time_strings()):
        for s in src:
            for v in variants(s):
                if v in seen: continue
                seen.add(v)
                for enc in ("ascii", "utf-16-le", "utf-16-be"):
                    try: yield (f"{enc}:{v!r}", v.encode(enc))
                    except Exception: pass
