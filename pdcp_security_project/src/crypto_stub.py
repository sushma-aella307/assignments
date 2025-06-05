# pdcp_security_project/src/crypto_stub.py
from Cryptodome.Cipher import AES
from Cryptodome.Hash import CMAC
from Cryptodome.Random import get_random_bytes

def generate_key(length_bytes=16): # Generic key generation
    """Generates a random key of specified length."""
    return get_random_bytes(length_bytes)

def calculate_mac_i(integrity_key: bytes, count: int, bearer: int, direction: int, input_data: bytes) -> bytes:
    """
    Simulates 3GPP integrity algorithm (e.g., EIA2/NIA2) using AES-CMAC.
    Inputs are combined as per 3GPP specifications.
    Returns 32-bit (4-byte) MAC-I.
    """
    if not integrity_key:
        raise ValueError("Integrity key cannot be None or empty for MAC calculation.")
    if input_data is None:
        input_data = b''

    count_bytes = count.to_bytes(4, 'big')
    bearer_val = bearer & 0x1F 
    bearer_byte = bearer_val.to_bytes(1, 'big')
    direction_val = direction & 0x01
    direction_byte = direction_val.to_bytes(1, 'big')

    mac_input_block = count_bytes + bearer_byte + direction_byte + input_data

    # --- CORRECTION HERE ---
    # CMAC.new expects the key and the cipher module itself (AES)
    # The cipher object (AES.new(integrity_key, AES.MODE_ECB)) is not passed directly to CMAC.new
    # Instead, pass the key and specify ciphermod=AES
    mac_obj = CMAC.new(integrity_key, ciphermod=AES) 
    # --- END CORRECTION ---
    
    mac_obj.update(mac_input_block) 

    full_mac = mac_obj.digest() 
    mac_i = full_mac[:4] 
    return mac_i

if __name__ == "__main__":
    key = generate_key()
    test_data = b"Hello, 5G World! This is a test payload."
    test_count = 12345
    test_bearer = 1
    test_direction = 0

    mac = calculate_mac_i(key, test_count, test_bearer, test_direction, test_data)
    print(f"Original Data: {test_data}")
    print(f"Generated MAC-I: {mac.hex()}") # Should be 8 hex chars (4 bytes)

    tampered_data = b"Hello, 5G W0rld! This is a test payload."
    tampered_mac_val = calculate_mac_i(key, test_count, test_bearer, test_direction, tampered_data)
    print(f"Tampered Data: {tampered_data}")
    print(f"MAC-I for Tampered Data: {tampered_mac_val.hex()}")
    print(f"MAC-I Match (Tampered Data vs Original MAC)? {mac == tampered_mac_val}")

    replayed_count = 12346
    replayed_mac_val = calculate_mac_i(key, replayed_count, test_bearer, test_direction, test_data)
    print(f"Original Data, Count {replayed_count}")
    print(f"MAC-I for Replayed Count:  {replayed_mac_val.hex()}")
    print(f"MAC-I Match (Replayed Count vs Original MAC)? {mac == replayed_mac_val}")

    print("\nCrypto stub self-test successful if MACs differ for different inputs.")