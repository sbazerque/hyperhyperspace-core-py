from secrets import token_hex

class RNG:
    
    def randomHexString(bits):
        return token_hex(bits)