
import base64

secret_sed = "gDbUcHRrUpI06h8DpC/HlAZ683vccSwkjvFg/jG8iroFQGM3lwLFsJ/rWUfQ58yDyps+lh6vp0+eRNc6d7exD5Dv5uyMwh1bjZ19XDk7XocWXbLBwBTO2dVpZjh28r3dnCVt/CYrmDyIGdK/VGqt4onRSdtB6MkzLkVLCOWlCuPToP1KSHwH/3hluRFVtLUBmn8AbOkqbr5fc/uR7vpkgcYhixujKD9R7Q6s+OEcoYUYEGf1bw1QjxWTQk2rzzXgfmHkYrbeIt8MVqimBIQg9xKiaEMj1sjwGgsneU7NdbiuWDCZKfmz9FdyU9o9lbuphgktxDL2E4JaqhdGy0zYww=="
encrypt_key = bytearray(base64.b64decode(secret_sed))
print("encrypt_key: ", len(encrypt_key), encrypt_key)
decrypt_key = encrypt_key.copy()
for i, v in enumerate(encrypt_key):
    decrypt_key[v] = i
print("decrypt_key: ", len(decrypt_key), decrypt_key)

def encode(data: bytearray):
    for i, v in enumerate(data):
        data[i] = encrypt_key[v]

def decode(data: bytearray):
    for i, v in enumerate(data):
        data[i] = decrypt_key[v]

data =  bytearray(b'localhost.test.com.cn')

print("data: ", data)

encode(data)

print("data encode: ", data)

decode(data)

print("data decode: ", data)