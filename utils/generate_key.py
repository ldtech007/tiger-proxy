import random
import base64

SECRET_KEY_LEN = 256
secret_key = bytearray(SECRET_KEY_LEN)
encode_secret_key = bytearray(2 * SECRET_KEY_LEN + 1)
decode_secret_key = bytearray(SECRET_KEY_LEN)


def check_key_valid(secretkey, length):
    for i in range(length):
        if secretkey[i] == i:
            return -1
    return 0

def generate_secret_key():
    secret_key = bytearray(range(SECRET_KEY_LEN))
    random.shuffle(secret_key)
    #print("secret_key is:", secret_key)

    ret = check_key_valid(secret_key, SECRET_KEY_LEN)

    if ret < 0:
        print("generate secret failed!")
        return
    print("generate secret success!")

    encode_secret_key = base64.b64encode(secret_key)
    #print("secret_key after base64encode encode_len is:", len(encode_secret_key))
    print("secret_sed:\n", encode_secret_key.decode())

    #decode_secret_key = base64.b64decode(encode_secret_key)
    #print("encode_secret_key after base64decode decode_len is:", len(decode_secret_key))
    #print(decode_secret_key)

generate_secret_key()