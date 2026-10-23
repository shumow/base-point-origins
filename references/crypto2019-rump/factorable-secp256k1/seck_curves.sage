def check_secpk_curve(phex, pexplicit, ahex, bhex, Ghex, nhex, hhex):
    p = Integer(phex)
    a = Integer(ahex)
    b = Integer(bhex)
    Gx = Integer(Ghex[0])
    Gy = Integer(Ghex[1])
    n = Integer(nhex)
    h = Integer(hhex)
    
    if (p != pexplicit):
        print("Explicit prime " + str(pexplicit) + " does not match hex prime " + str(p) + ".")
        return None
    
    Fp = GF(p)
    E = EllipticCurve(Fp, [a,b])
    G = E((Gx,Gy))
    
    P = n*G
    
    if (not P.is_zero()):
        print("Generator does not have supplied order.")
        return None
    
    # TODO? Add cofactor checking
    
    return (E, G, n, h)

def parse_secpk_params(params):
    phex = params[0]
    pexplicit_str = params[1]
    pexplicit = sage_eval(pexplicit_str)
    ahex = params[2]
    bhex = params[3]
    Ghex = params[4]
    nhex = params[5]
    hhex = params[6]

    print("Checking Curve Defined by:")
    print("    p = " + phex)
    print("      = " + pexplicit_str)
    print("      = " + str(pexplicit))
    print("    a = " + ahex)
    print("    b = " + bhex)
    print("    G = (" + Ghex[0] + "," + Ghex[1] + ")")
    print("    n = " + nhex)
    print("    h = " + hhex)

    ret = check_secpk_curve(phex, pexplicit, ahex, bhex, Ghex, nhex, hhex)
    
    if (None != ret):
        print("    checks out.")
    else:
        print("    does not check out.")

    return ret

secp160k1_params = ("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC73",
                    "2^160 - 2^32 - 2^14 - 2^12 - 2^9 - 2^8 - 2^7 - 2^3 - 2^2 - 1",
                    "0x0000000000000000000000000000000000000000",
                    "0x0000000000000000000000000000000000000007",
                    ("0x3B4C382CE37AA192A4019E763036F4F5DD4D7EBB",
                     "0x938CF935318FDCED6BC28286531733C3F03C4FEE"),
                    "0x0100000000000000000001B8FA16DFAB9ACA16B6B3",
                    "0x01")

secp192k1_params = ("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFEE37",
                    "2^192 - 2^32 - 2^12 - 2^8 - 2^7 - 2^6 - 2^3 - 1",
                    "0x000000000000000000000000000000000000000000000000",
                    "0x000000000000000000000000000000000000000000000003",
                    ("0xDB4FF10EC057E9AE26B07D0280B7F4341DA5D1B1EAE06C7D",
                     "0x9B2F2F6D9C5628A7844163D015BE86344082AA88D95E2F9D"),
                    "0xFFFFFFFFFFFFFFFFFFFFFFFE26F2FC170F69466A74DEFD8D",
                    "0x01")

secp224k1_params = ("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFE56D",
                    "2^224 - 2^32 - 2^12 - 2^11 - 2^9 - 2^7 - 2^4 - 2 - 1",
                    "0x00000000000000000000000000000000000000000000000000000000",
                    "0x00000000000000000000000000000000000000000000000000000005",
                    ("0xA1455B334DF099DF30FC28A169A467E9E47075A90F7E650EB6B7A45C",
                     "0x7E089FED7FBA344282CAFBD6F7E319F7C0B0BD59E2CA4BDB556D61A5"),
                    "0x010000000000000000000000000001DCE8D2EC6184CAF0A971769FB1F7",
                    "0x01")

secp256k1_params = ("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F",
                    "2^256 - 2^32 - 2^9 - 2^8 - 2^7 - 2^6 - 2^4 - 1",
                    "0x0000000000000000000000000000000000000000000000000000000000000000",
                    "0x0000000000000000000000000000000000000000000000000000000000000007",
                    ("0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798",
                     "0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8"),
                    "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141",
                    "0x01")


secp160k1 = parse_secpk_params(secp160k1_params)
secp192k1 = parse_secpk_params(secp192k1_params)
secp224k1 = parse_secpk_params(secp224k1_params)
secp256k1 = parse_secpk_params(secp256k1_params)

def x_half_generator(secp_curve):
  G = secp_curve[1]
  q = secp_curve[2]
  Fq = GF(q)
  onehalf = Fq(1/2).lift()
  P = onehalf*G
  return P[0].lift().hex()

print("")
print("Showing short (1/2)*G for each curve:")
print("")
print("secp160k1 (1/2)*G = " + '{:>50}'.format(x_half_generator(secp160k1)))
print("secp192k1 (1/2)*G = " + '{:>50}'.format(x_half_generator(secp192k1)))
print("secp224k1 (1/2)*G = " + '{:>50}'.format(x_half_generator(secp224k1)))
print("secp256k1 (1/2)*G = " + '{:>50}'.format(x_half_generator(secp256k1)))

def hex2binaryfield(K, ehex):
    ei = Integer(ehex)
    bits = ei.bits()
    a = K.gen()
    ek = K(0)
    for j in range(len(bits)):
        ek = ek + bits[j]*(a^j)
    return ek

def binaryfield2hex(ek):
    ei = Integer(ek.integer_representation())
    return ei.hex()

def check_sectk_curve(fstr, ahex, bhex, Ghex, nhex, hhex):
    B = GF(2)
    R = PolynomialRing(B, 'x')
    f = R(fstr)
    K = B.extension(f, 'a')
    a = hex2binaryfield(K, ahex)
    b = hex2binaryfield(K, bhex)
    Gx = hex2binaryfield(K, Ghex[0])
    Gy = hex2binaryfield(K, Ghex[1])
    n = Integer(nhex)
    h = Integer(hhex)
    E = EllipticCurve(K, [B(1), a, 0, 0, b])
    G = E((Gx,Gy))
    
    P = n*G

    if (not P.is_zero()):
        print("Generator does not have supplied order.")
        return None
    
    # TODO? Add cofactor checking
    
    return (E, G, n, h)

def parse_sectk_params(params):
    fstr = params[0]
    ahex = params[1]
    bhex = params[2]
    Ghex = params[3]
    nhex = params[4]
    hhex = params[5]

    print("Checking Curve Defined by:")
    print("    f = " + fstr)
    print("    a = " + ahex)
    print("    b = " + bhex)
    print("    G = (" + Ghex[0] + "," + Ghex[1] + ")")
    print("    n = " + nhex)
    print("    h = " + hhex)

    ret = check_sectk_curve(fstr, ahex, bhex, Ghex, nhex, hhex)
    
    if (None != ret):
        print("    checks out.")
    else:
        print("    does not check out.")

    return ret


sect163k1_params = ("x^163 + x^7 + x^6 + x^3 + 1",
                    "0x000000000000000000000000000000000000000001",
                    "0x000000000000000000000000000000000000000001",
                    ("0x02FE13C0537BBC11ACAA07D793DE4E6D5E5C94EEE8",
                     "0x0289070FB05D38FF58321F2E800536D538CCDAA3D9"),
                    "0x04000000000000000000020108A2E0CC0D99F8A5EF",
                    "0x02")

sect233k1_params = ("x^233 + x^74 + 1",
                    "0x000000000000000000000000000000000000000000000000000000000000",
                    "0x000000000000000000000000000000000000000000000000000000000001",                    ("0x017232BA853A7E731AF129F22FF4149563A419C26BF50A4C9D6EEFAD6126",
                     "0x01DB537DECE819B7F70F555A67C427A8CD9BF18AEB9B56E0C11056FAE6A3"),                    "0x8000000000000000000000000000069D5BB915BCD46EFB1AD5F173ABDF",
                    "0x04")

sect239k1_params = ("x^239 + x^158 + 1",
                    "0x000000000000000000000000000000000000000000000000000000000000",
                    "0x000000000000000000000000000000000000000000000000000000000001",
                    ("0x29A0B6A887A983E9730988A68727A8B2D126C44CC2CC7B2A6555193035DC",
                     "0x76310804F12E549BDB011C103089E73510ACB275FC312A5DC6B7 6553F0CA"),
                    "0x2000000000000000000000000000005A79FEC67CB6E91F1C1DA800E478A5",
                    "0x04")

sect283k1_params = ("x^283 + x^12 + x^7 + x^5 + 1",
                    "0x000000000000000000000000000000000000000000000000000000000000000000000000",
                    "0x000000000000000000000000000000000000000000000000000000000000000000000001",
                    ("0x0503213F78CA44883F1A3B8162F188E553CD265F23C1567A16876913B0C2AC2458492836",
                     "0x01CCDA380F1C9E318D90F95D07E5426FE87E45C0E8184698E45962364E34116177DD2259"),
                    "0x01FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE9AE2ED07577265DFF7F94451E061E163C61",
                    "0x04")

sect409k1_params = ("x^409 + x^87 + 1",
                    "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                    "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",
                    ("0x0060F05F658F49C1AD3AB1890F7184210EFD0987E307C84C27ACCFB8F9F67CC2C460189EB5AAAA62EE222EB1B35540CFE9023746",
                     "0x01E369050B7C4E42ACBA1DACBF04299C3460782F918EA427E6325165E9EA10E3DA5F6C42E9C55215AA9CA27A5863EC48D8E0286B"),
                    "0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE5F83B2D4EA20400EC4557D5ED3E3E7CA5B4B5C83B8E01E5FCF",
                    "0x04")

sect571k1_params = ("x^571 + x^10 + x^5 + x^2 + 1",
                    "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                    "0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",
                    ("0x026EB7A859923FBC82189631F8103FE4AC9CA2970012D5D46024804801841CA44370958493B205E647DA304DB4CEB08CBBD1BA39494776FB988B47174DCA88C7E2945283A01C8972",
                     "0x0349DC807F4FBF374F4AEADE3BCA95314DD58CEC9F307A54FFC61EFC006D8A2C9D4979C0AC44AEA74FBEBBB9F772AEDCB620B01A7BA7AF1B320430C8591984F601CD4C143EF1C7A3"),
                    "0x020000000000000000000000000000000000000000000000000000000000000000000000131850E1F19A63E4B391A8DB917F4138B630D84BE5D639381E91DEB45CFE778F637C1001",
                    "0x04")
                     
sect163k1 = parse_sectk_params(sect163k1_params)
sect233k1 = parse_sectk_params(sect233k1_params)
sect239k1 = parse_sectk_params(sect239k1_params)
sect283k1 = parse_sectk_params(sect283k1_params)
sect409k1 = parse_sectk_params(sect409k1_params)
sect571k1 = parse_sectk_params(sect571k1_params)

def x_half_generator_binary(sect_curve):
  G = sect_curve[1]
  q = sect_curve[2]
  Fq = GF(q)
  onehalf = Fq(1/2).lift()
  P = onehalf*G
  return binaryfield2hex(P[0]) + " " + str(len(Integer(P[0].integer_representation()).bits()))

print("sect163k1 (1/2)*G = " + '{:>45}'.format(x_half_generator_binary(sect163k1)))
print("sect233k1 (1/2)*G = " + '{:>45}'.format(x_half_generator_binary(sect233k1)))
print("sect239k1 (1/2)*G = " + '{:>45}'.format(x_half_generator_binary(sect239k1)))
print("sect283k1 (1/2)*G = " + '{:>45}'.format(x_half_generator_binary(sect283k1)))
print("sect409k1 (1/2)*G = " + '{:>45}'.format(x_half_generator_binary(sect409k1)))
print("sect571k1 (1/2)*G = " + '{:>45}'.format(x_half_generator_binary(sect571k1)))

def x_reciprocal_times_generator_binary(sect_curve, m):
    G = sect_curve[1]
    q = sect_curve[2]
    Fq = GF(q)
    P = Fq(1/m).lift()*G
    return binaryfield2hex(P[0]) + " " + str(len(Integer(P[0].integer_representation()).bits()))

print("sect233k1 (1/4)*G = " + '{:>45}'.format(x_reciprocal_times_generator_binary(sect233k1, 4)))
print("sect239k1 (1/4)*G = " + '{:>45}'.format(x_reciprocal_times_generator_binary(sect239k1, 4)))
print("sect283k1 (1/4)*G = " + '{:>45}'.format(x_reciprocal_times_generator_binary(sect283k1, 4)))
print("sect409k1 (1/4)*G = " + '{:>45}'.format(x_reciprocal_times_generator_binary(sect409k1, 4)))
print("sect571k1 (1/4)*G = " + '{:>45}'.format(x_reciprocal_times_generator_binary(sect571k1, 4)))

def find_cofactor_group(sect_curve):
    E = sect_curve[0]
    G = sect_curve[1]
    q = sect_curve[2]
    h = sect_curve[3]

    cofactor_points = [E(0)]

    while (len(cofactor_points) != h):
        P = E.random_point()
        P = q*P
        pts = [P]
        Q = P
        while (not Q.is_zero()):
            Q = Q+P
            if (Q not in pts):
                pts.append(Q)
        for Q in pts:
           for P in cofactor_points:
               R = P + Q
               if (R not in cofactor_points):
                   cofactor_points.append(R)

    return cofactor_points

def print_generator_preimage_points(sect_curve, m):
    cfg = find_cofactor_group(sect_curve)
    G = sect_curve[1]
    q = sect_curve[2]

    Fq = GF(q)

    P = Fq(1/m).lift()*G

    for Ph in cfg:
        P3 = P+Ph
        x = P3[0]
        print("\t" + binaryfield2hex(x))

    return

print("\n\n")

print("sect163k1 (1/2)*G preimage = ")
print_generator_preimage_points(sect163k1, 2)
print("")

print("sect233k1 (1/2)*G preimage = ")
print_generator_preimage_points(sect233k1, 2)
print("")

print("sect239k1 (1/2)*G preimage = ")
print_generator_preimage_points(sect239k1, 2)
print("")

print("sect283k1 (1/2)*G preimage = ")
print_generator_preimage_points(sect283k1, 2)
print("")

print("sect409k1 (1/2)*G preimage = ")
print_generator_preimage_points(sect409k1, 2)
print("")

print("sect571k1 (1/2)*G preimage = ")
print_generator_preimage_points(sect571k1, 2)
print("")

print("\n\n")

print("sect233k1 (1/4)*G preimage = ")
print_generator_preimage_points(sect233k1, 4)
print("")

print("sect239k1 (1/4)*G preimage = ")
print_generator_preimage_points(sect239k1, 4)
print("")

print("sect283k1 (1/4)*G preimage = ")
print_generator_preimage_points(sect283k1, 4)
print("")

print("sect409k1 (1/4)*G preimage = ")
print_generator_preimage_points(sect409k1, 4)
print("")

print("sect571k1 (1/4)*G preimage = ")
print_generator_preimage_points(sect571k1, 4)
print("")
