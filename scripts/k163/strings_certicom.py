"""Certicom-era candidate strings (HANDOFF §4.1). Same interface as strings.py: all_strings() yields (label, bytes).
Covers Certicom / SECG people, places, orgs, curve names, SEC draft dates and the ECC Challenge, r-curve SEEDs and their
ASCII, obvious test strings, and the published parameters (p, n, a, b, Gx, Gy) of the secp*k1 and secp160r curves as
decimal / hex strings. Set CERTICOM_ONLY=0 in the environment to also include the original strings.py set."""
import datetime, itertools, os
from strings import variants, dates as nist_dates, CORE as NIST_CORE, time_strings

CORE = [
 # orgs / places
 "Certicom", "Certicom Corp", "Certicom Corp.", "Certicom Corporation", "Certicom Research", "Certicom Inc", "Certicom Inc.",
 "SECG", "SEC", "SEC 1", "SEC1", "SEC 2", "SEC2", "SEC 2: Recommended Elliptic Curve Domain Parameters",
 "Standards for Efficient Cryptography", "Standards for Efficient Cryptography Group", "Recommended Elliptic Curve Domain Parameters",
 "Elliptic Curve Cryptography", "ECC", "ECDSA", "ECDH", "ECIES", "ECMQV", "MQV",
 "Mississauga", "Mississauga, Ontario", "Waterloo", "Waterloo, Ontario", "University of Waterloo", "Hayward", "Hayward, California", "Hayward CA",
 "Ontario", "Canada", "Toronto", "Mobile e-Business", "Certicom Security Builder", "Security Builder",
 # people
 "Scott Vanstone", "Scott A. Vanstone", "S. Vanstone", "Vanstone", "savanstone", "svanstone",
 "Alfred Menezes", "Alfred J. Menezes", "A. Menezes", "Menezes", "ajmeneze", "amenezes",
 "Minghua Qu", "M. Qu", "Qu", "mqu", "Ming Hua Qu",
 "Dan Brown", "Daniel Brown", "Daniel R. L. Brown", "Daniel R.L. Brown", "D. Brown", "Brown", "dbrown",
 "Rob Gallant", "Robert Gallant", "Robert P. Gallant", "R. Gallant", "Gallant", "rgallant",
 "Rob Lambert", "Robert Lambert", "Robert J. Lambert", "R. Lambert", "Lambert", "rlambert",
 "Simon Blake-Wilson", "Blake-Wilson", "S. Blake-Wilson", "sblakewilson", "sblake-wilson",
 "Don Johnson", "Donald Johnson", "Donald B. Johnson", "D. Johnson", "Johnson", "djohnson",
 "Ron Mullin", "Ronald Mullin", "Ronald C. Mullin", "R. Mullin", "Mullin", "rmullin",
 "Ian Blake", "Ian F. Blake", "I. Blake", "Blake",
 "Neal Koblitz", "N. Koblitz", "Koblitz", "Jerry Solinas", "Solinas",
 "Richard Schroeppel", "Rich Schroeppel", "Schroeppel",
 "Tom Rosati", "Ash Vadekar", "Ashok Vadekar", "Michael Qu", "Leon Pintsov", "Paul Van Oorschot", "Paul van Oorschot", "van Oorschot",
 "Gordon Agnew", "Gord Agnew", "Agnew", "Philip Deck", "Phil Deck", "Deck", "Rick Dalmazzi", "Brian Minard", "Minard",
 "Scott Vanstone and Alfred Menezes", "Menezes, Qu, Vanstone", "Menezes Qu Vanstone", "MQV", "Vanstone Menezes Qu",
 # curve names
 "secp160k1", "secp192k1", "secp224k1", "secp256k1", "secp160r1", "secp160r2",
 "sec160k1", "sec192k1", "sec224k1", "sec256k1", "sec160r1", "sec160r2",
 "ansip160k1", "ansip192k1", "ansip224k1", "ansip256k1", "ansip160r1", "ansip160r2",
 "SECP160K1", "SECP192K1", "SECP224K1", "SECP256K1",
 "secp-160k1", "secp-192k1", "secp-224k1", "secp-256k1", "p160k1", "p192k1", "p224k1", "p256k1",
 "Koblitz 160", "Koblitz 192", "Koblitz 224", "Koblitz 256", "Koblitz-160", "Koblitz-192", "Koblitz-224", "Koblitz-256",
 "k160", "k192", "k224", "k256", "K160", "K192", "K224", "K256", "K-160", "K-192", "K-224", "K-256",
 "koblitz", "Koblitz", "Koblitz curve", "Koblitz curves", "anomalous", "anomalous curve", "CM curve", "CM", "j=0", "j = 0", "j-invariant 0",
 "a=0", "a = 0", "b=7", "b = 7", "b=3", "b=5", "y^2 = x^3 + 7", "y^2=x^3+7", "y^2 = x^3 + 3", "y^2 = x^3 + 5", "x^3 + 7", "x^3+7",
 "160", "192", "224", "256", "2^160", "2^192", "2^224", "2^256", "GF(p)", "F_p", "Fp", "prime field", "prime", "generator", "base point",
 "Generalized Mersenne", "generalized Mersenne prime", "Solinas prime", "pseudo-Mersenne", "pseudo-Mersenne prime",
 # Certicom ECC Challenge (1997)
 "Certicom ECC Challenge", "ECC Challenge", "The Certicom ECC Challenge", "ECCp-79", "ECCp-89", "ECCp-97", "ECCp-109", "ECCp-131", "ECCp-163", "ECCp-191", "ECCp-239", "ECCp-359",
 "ECC2-79", "ECC2-89", "ECC2-97", "ECC2-109", "ECC2-131", "ECC2-163", "ECC2-191", "ECC2-238", "ECC2-353",
 "ECC2K-95", "ECC2K-108", "ECC2K-130", "ECC2K-163", "ECC2K-238", "ECC2K-358",
 "ECCp79", "ECCp131", "ECC2K163", "ECC2K130", "challenge", "Challenge", "Certicom challenge",
 # test strings
 "test", "Test", "TEST", "test vector", "Certicom test vector", "test1", "test2", "testing", "abc", "abcd", "abcde", "abcdef", "hello", "Hello", "hello world", "Hello, world", "Hello World",
 "The quick brown fox jumps over the lazy dog", "The quick brown fox jumps over the lazy dog.", "quick brown fox", "foo", "bar", "foobar", "foo bar", "dummy", "sample", "example", "example seed",
 "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",   # SHA-1 test vector
 "message digest", "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
 "12345678901234567890123456789012345678901234567890123456789012345678901234567890", "a", "",
 "The Magic Words are Squeamish Ossifrage", "Squeamish Ossifrage",
 # r-curve SEEDs (SEC 2 v1.0) and their ASCII content
 "00F50B028E4D696E676875615175290472783FB1", "002757A1114D696E67687561517531D7FE6ED48A", "000E0D4D696E6768756151750CC03A4473D03679",
 "004D696E67687561517512D8F03431FCE63B88F4", "1053CDE42C14D696E67687561517533BF3F83345", "B99B99B099B323E02709A4D696E6768756151751",
 "00f50b028e4d696e676875615175290472783fb1", "002757a1114d696e67687561517531d7fe6ed48a", "000e0d4d696e6768756151750cc03a4473d03679",
 "004d696e67687561517512d8f03431fce63b88f4", "1053cde42c14d696e67687561517533bf3f83345", "b99b99b099b323e02709a4d696e6768756151751",
 "Minghua Qu", "Minghua Qu3", "Minghua Qu1", "Minghua Qu2", "MinghuaQu", "minghua qu", "Minghua", "Qu Minghua",
 "Minghua Qu, Certicom", "Minghua Qu Certicom", "Certicom Minghua Qu",
 # misc 90s Certicom product/standard names
 "WAP", "WTLS", "WAP Forum", "WAP WTLS", "wtls", "IEEE P1363", "P1363", "X9.62", "X9.63", "ANSI X9.63", "X9F1", "IETF", "TLS", "SSL", "IPSEC", "IPsec", "IKE",
 "Oakley", "Oakley group", "OAKLEY", "Elliptic Curve Oakley", "ECC Oakley group", "RFC 2409", "RFC2409",
 "secret", "SECRET", "password", "Password", "random", "RANDOM", "seed", "SEED", "Seed", "nothing up my sleeve", "nothing-up-my-sleeve", "Nothing up my sleeve",
]

def sec_dates():
    """1997-01-01 .. 2000-12-31 (ECC Challenge 1997, SEC drafts 1999–2000); strings.py covers 1997–98 in 13 formats, so
    only extend 1999–2000 here, same formats."""
    d = datetime.date(1999, 1, 1)
    while d <= datetime.date(2000, 12, 31):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d %B %Y", "%B %d, %Y", "%Y%m%d", "%d%m%Y", "%m%d%Y", "%y%m%d", "%b %d %Y", "%d-%b-%Y", "%A, %B %d, %Y", "%a %b %d %Y"):
            yield d.strftime(fmt)
        d += datetime.timedelta(days=1)
    for y in (1997, 1998, 1999, 2000, 2001):
        yield str(y)
        for m in range(1, 13): yield f"{y}-{m:02d}"; yield f"{m}/{y}"; yield datetime.date(y, m, 1).strftime("%B %Y"); yield datetime.date(y, m, 1).strftime("%b %Y")

PARAMS = {
 "secp160k1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC73, a=0, b=7, n=0x0100000000000000000001B8FA16DFAB9ACA16B6B3,
                   Gx=0x3B4C382CE37AA192A4019E763036F4F5DD4D7EBB, Gy=0x938CF935318FDCED6BC28286531733C3F03C4FEE),
 "secp192k1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFEE37, a=0, b=3, n=0xFFFFFFFFFFFFFFFFFFFFFFFE26F2FC170F69466A74DEFD8D,
                   Gx=0xDB4FF10EC057E9AE26B07D0280B7F4341DA5D1B1EAE06C7D, Gy=0x9B2F2F6D9C5628A7844163D015BE86344082AA88D95E2F9D),
 "secp224k1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFE56D, a=0, b=5, n=0x010000000000000000000000000001DCE8D2EC6184CAF0A971769FB1F7,
                   Gx=0xA1455B334DF099DF30FC28A169A467E9E47075A90F7E650EB6B7A45C, Gy=0x7E089FED7FBA344282CAFBD6F7E319F7C0B0BD59E2CA4BDB556D61A5),
 "secp256k1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F, a=0, b=7, n=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141,
                   Gx=0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798, Gy=0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8),
 "secp160r1": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFF, a=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFC, b=0x1C97BEFC54BD7A8B65ACF89F81D4D4ADC565FA45,
                   n=0x0100000000000000000001F4C8F927AED3CA752257, Gx=0x4A96B5688EF573284664698968C38BB913CBFC82, Gy=0x23A628553168947D59DCC912042351377AC5FB32),
 "secp160r2": dict(p=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC73, a=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC70, b=0xB4E134D3FB59EB8BAB57274904664D5AF50388BA,
                   n=0x0100000000000000000000351EE786A818F3A1A16B, Gx=0x52DCB034293A117E1F4FF11B30F7199D3144CE6D, Gy=0xFEAFFEF2E331F296E071FA0DF9982CFEA7D43F2E),
}

def param_strings():
    """Each curve parameter as decimal, hex (upper/lower, with/without 0x), fixed-width hex; also p-3 (the k1 'c' in 2^m - c), and the big-endian bytes themselves."""
    seen = set()
    for cname, d in PARAMS.items():
        m = d["p"].bit_length(); width = (m + 7) // 8 * 2
        for key, v in list(d.items()) + [("c", (1 << m) - d["p"]) if d["a"] == 0 else ("a+3", (d["a"] + 3) % d["p"])]:
            for s in (str(v), hex(v), hex(v)[2:], hex(v)[2:].upper(), "0x" + hex(v)[2:].upper(), f"{v:0{width}x}", f"{v:0{width}X}", f"{key}={v}", f"{key} = {v}", f"{cname} {key}"):
                if s not in seen: seen.add(s); yield s
            nb = max(width // 2, (v.bit_length() + 7) // 8)
            yield ("bytes", v.to_bytes(nb, "big"))
            yield ("bytes-le", v.to_bytes(nb, "little"))

def all_strings():
    seen = set()
    sources = [CORE, sec_dates(), param_strings()]
    if os.environ.get("CERTICOM_ONLY", "1") == "0":
        sources += [NIST_CORE, nist_dates(), time_strings()]
    for src in sources:
        for s in src:
            if isinstance(s, tuple):            # raw bytes
                if s in seen: continue
                seen.add(s); yield (f"raw:{s[0]}:{s[1].hex()}", s[1]); continue
            for v in variants(s):
                if v in seen: continue
                seen.add(v)
                for enc in ("ascii", "utf-16-le", "utf-16-be"):
                    try: yield (f"{enc}:{v!r}", v.encode(enc))
                    except Exception: pass

if __name__ == "__main__":
    print(sum(1 for _ in all_strings()), "candidate byte strings")
