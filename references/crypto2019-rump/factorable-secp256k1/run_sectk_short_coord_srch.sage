attach("sectk_small_x_srch.sage")

print("\n\n")
print("Searching for short x-coordiantes by checking:")
print("Multiples of 2^(-j) mod q and iterations of squaring 2^k (frobenius maps.)")
print("")

print("sect163k1 searching for short x-coordinates:")
sect_small_x_srch(sect163k1)
print("")

print("sect233k1 searching for short x-coordinates:")
sect_small_x_srch(sect233k1)
print("")

print("sect239k1 searching for short x-coordinates:")
sect_small_x_srch(sect239k1)
print("")

print("sect283k1 searching for short x-coordinates:")
sect_small_x_srch(sect283k1)
print("")

print("sect409k1 searching for short x-coordinates:")
sect_small_x_srch(sect409k1)
print("")

print("sect571k1 searching for short x-coordinates:")
sect_small_x_srch(sect571k1)
print("")
