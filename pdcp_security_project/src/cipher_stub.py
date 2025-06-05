# pdcp_security_project/src/cipher_stub.py
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes # For keystream, not directly for AES-CTR key
import struct

# Note: This is a highly simplified AES-CTR stub.
# Real 3GPP AES-CTR (NEA0, NEA1, NEA2, NEA3) has specific counter block formatting.
# For NEA0 (null cipher), it would just return the plaintext.

def generate_cipher_key(length_bytes=16):
    return get_random_bytes(length_bytes)

def _generate_keystream_byte(cipher_key: bytes, count: int, bearer: int, direction: int, length: int) -> bytes:
    """
    Generates a keystream using AES-CTR mode.
    The counter block is formed from COUNT, BEARER, DIRECTION.
    This is a simplified version.
    """
    if not cipher_key:
        raise ValueError("Cipher key cannot be None for keystream generation.")

    # Construct the initial counter block (16 bytes for AES)
    # COUNT (4 bytes), BEARER (1 byte, 5 LSBs), DIRECTION (1 byte, 1 LSB),
    # then pad with zeros or other fixed values.
    # For simplicity, we'll make it more direct.
    # Ensure values fit their intended bit widths for more accurate simulation
    bearer_val = bearer & 0x1F   # 5 bits
    direction_val = direction & 0x01 # 1 bit

    # Simplified counter block construction for simulation:
    # We need a 16-byte IV/nonce for AES-CTR.
    # Let's use COUNT, BEARER, DIRECTION and pad.
    # High 4 bytes: COUNT
    # Next 1 byte: BEARER
    # Next 1 byte: DIRECTION
    # Remaining 10 bytes: zeros (for simplicity)
    # This is NOT 3GPP compliant but serves to make the keystream unique per packet.
    iv_part1 = count.to_bytes(4, 'big')
    iv_part2 = bearer_val.to_bytes(1, 'big')
    iv_part3 = direction_val.to_bytes(1, 'big')
    iv_padding = b'\x00' * (16 - len(iv_part1) - len(iv_part2) - len(iv_part3))
    nonce = iv_part1 + iv_part2 + iv_part3 + iv_padding # This is the initial counter value

    cipher = AES.new(cipher_key, AES.MODE_CTR, nonce=nonce[:12], initial_value=int.from_bytes(nonce[12:], 'big')) # Example split
    # A more common way for AES-CTR is to provide a nonce and let the library handle the counter.
    # PyCryptodome's AES.MODE_CTR uses a nonce (typically 8-15 bytes) and an initial_value (integer) for the counter part.
    # Or, you can provide a 'counter' callable.
    # For simplicity, let's form a unique "nonce" for each packet and use a fixed initial counter value.
    # This is NOT how 3GPP does it, but creates unique keystreams.
    # A better simplified nonce for CTR:
    nonce_for_ctr = count.to_bytes(4, 'big') + \
                    bearer_val.to_bytes(1, 'big') + \
                    direction_val.to_bytes(1, 'big') + \
                    b'\x00' * 6 # Making a 12-byte nonce, CTR counter starts at 1

    # For AES-CTR, the nonce should typically be 12 bytes, and the counter part is 4 bytes.
    # Let's use first 8 bytes of our constructed 'nonce' as the actual nonce for CTR mode.
    # And use the remaining part to form the initial counter value.

    # A simpler nonce for PyCryptodome's CTR mode (often 8 bytes for nonce, counter separate)
    # Let's make a 12-byte nonce and start counter from 1.
    # COUNT (4), BEARER (1), DIRECTION (1), padding to 12 bytes.
    ctr_nonce_material = count.to_bytes(4, 'big') + \
                         bearer_val.to_bytes(1, 'big') + \
                         direction_val.to_bytes(1, 'big')
    # Pad to 12 bytes for a common CTR nonce length. This is arbitrary for our stub.
    ctr_nonce = (ctr_nonce_material + b'\x00' * 12)[:12]


    # Re-initialize cipher with a unique nonce for each call to ensure keystream is unique.
    # The `initial_value` is the starting value for the counter part of the counter block.
    cipher = AES.new(cipher_key, AES.MODE_CTR, nonce=ctr_nonce, initial_value=1)
    keystream = cipher.encrypt(b'\x00' * length) # Encrypt null bytes to get keystream
    return keystream

def encrypt(cipher_key: bytes, count: int, bearer: int, direction: int, plaintext: bytes) -> bytes:
    """Simulates PDCP ciphering (simplified AES-CTR like)."""
    if plaintext is None: plaintext = b''
    if not cipher_key: # Null ciphering if no key
        return plaintext
    keystream = _generate_keystream_byte(cipher_key, count, bearer, direction, len(plaintext))
    ciphertext = bytes([p ^ k for p, k in zip(plaintext, keystream)])
    return ciphertext

def decrypt(cipher_key: bytes, count: int, bearer: int, direction: int, ciphertext: bytes) -> bytes:
    """Simulates PDCP deciphering (simplified AES-CTR like)."""
    if ciphertext is None: ciphertext = b''
    if not cipher_key: # Null ciphering if no key
        return ciphertext
    # CTR mode decryption is the same as encryption
    return encrypt(cipher_key, count, bearer, direction, ciphertext)

if __name__ == "__main__":
    key = generate_cipher_key()
    test_plaintext = b"This is secret data for 5G!"
    test_count = 555
    test_bearer = 5
    test_direction = 1 # Downlink

    print(f"Plaintext: {test_plaintext}")

    ciphered = encrypt(key, test_count, test_bearer, test_direction, test_plaintext)
    print(f"Ciphered:  {ciphered.hex()}")

    deciphered = decrypt(key, test_count, test_bearer, test_direction, ciphered)
    print(f"Deciphered: {deciphered.decode('utf-8', errors='ignore')}")
    assert deciphered == test_plaintext

    # Test with different count (should produce different ciphertext and fail decryption if wrong count used)
    ciphered_wrong_count_tx = encrypt(key, test_count + 1, test_bearer, test_direction, test_plaintext)
    deciphered_wrong_count_rx = decrypt(key, test_count, test_bearer, test_direction, ciphered_wrong_count_tx)
    print(f"Ciphered (COUNT+1): {ciphered_wrong_count_tx.hex()}")
    print(f"Deciphered with original COUNT: {deciphered_wrong_count_rx.decode('utf-8', errors='ignore')}")
    assert deciphered_wrong_count_rx != test_plaintext

    print("Cipher stub self-test successful.")