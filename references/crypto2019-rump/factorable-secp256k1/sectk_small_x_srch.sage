attach("seck_curves.sage")

def sect_small_x_srch(sect_curve):
    E = sect_curve[0]
    F2m = E.base_ring()
    m = F2m.degree()

    G = sect_curve[1]

    q = sect_curve[2]
    Fq = GF(q)

    cfg = find_cofactor_group(sect_curve)

    min_x = None
    min_xbits = m+1

    min_j = None
    min_k = None

    for j in range(0,m):        # iterate over multiples.
        a = Fq(1/2^j).lift()
        P = a*G
        for k in range(0,m):    # iterate over frobenius.
            fre = 2^k
            Q = E(P[0]^fre,P[1]^fre)
            for Q2 in cfg:
                x = (Q+Q2)[0]
                xi = Integer(x.integer_representation())
                xbits = len(xi.bits())
                if (xbits < 0.75*m):
                    print("Found a unexpected short x coordinate, with " + str(xbits) + " bits: 0x" + xi.hex())
                if (xbits < min_xbits):
                    min_xbits = xbits
                    min_x = xi
                    min_j = j
                    min_k = k

    print("Minimum bit length x coordinate has " + str(min_xbits) + " bits: 0x" + min_x.hex())
    print("Minimum occured at k = " + str(min_k) + " j = " + str(min_j))