attach("seck_curves.sage")

def apply_endomorphism(P, el):
    E = P.curve()
    acP = E(0)
    F = E.base_ring()
    p = F.characteristic()
    (x,y) = P.xy()
    for (m, n) in el:
        fre = p^n
        acP = acP + m*E(x^fre,y^fre)
    return acP

# test my endomorphism hypothesis
E = sect233k1[0]
q = sect233k1[2]
Fq = GF(q)

h = sect233k1[3]

end1 = [(1,0),(1,1)]
end2 = [((-1)^j,j) for j in range(233)]

counter_example = false

for j in range(10):
    P = h*E.random_point()
    while (P.is_zero()):
        P = h*E.random_point()
    P2 = apply_endomorphism(P,end1)
    P3 = apply_endomorphism(P2,end2)
    P4 = Fq(1/2).lift()*P3
    if (P != P4):
        counter_example = true
        print("Found counter example!")

if (not counter_example):
    print("Did not find a counter example!")

print("\n\nTesting if hypothesis G=P+f(P) for P w/ short x-coordinate is true for sect233k1:\n")

G = sect233k1[1]

P = Fq(1/2).lift()*apply_endomorphism(G,end2)

cfg = find_cofactor_group(sect233k1)

print("x-coordinates:")
for Q in cfg:
    T = P+Q
    x = T.xy()[0].integer_representation()
    print(Integer(x).hex())
print("-----------------------------------------------------------")
print("01234567890123456789012345678901234567890123456789012345678")