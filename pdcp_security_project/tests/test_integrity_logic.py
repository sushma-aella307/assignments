import unittest
from src.crypto_stub import generate_key, calculate_mac_i
from src.pdcp_entity import PDCPTransmitter, PDCPReceiver
from src.pdcp_packet import PDCP_PDU
from src import cipher_stub
import config

class TestIntegrityLogic(unittest.TestCase):
    def setUp(self):
        self.integrity_key = generate_key(config.INTEGRITY_KEY_LENGTH_BYTES)
        self.cipher_key = cipher_stub.generate_cipher_key(config.CIPHER_KEY_LENGTH_BYTES)
        self.count = 123
        self.bearer = 1
        self.direction = 0
        self.data = b"Test data for integrity"

    def test_mac_calculation_basic(self):
        mac1 = calculate_mac_i(self.integrity_key, self.count, self.bearer, self.direction, self.data)
        self.assertIsNotNone(mac1)
        self.assertEqual(len(mac1), 4)  # 32-bit MAC-I

    def test_mac_changes_with_data(self):
        mac1 = calculate_mac_i(self.integrity_key, self.count, self.bearer, self.direction, self.data)
        mac2 = calculate_mac_i(self.integrity_key, self.count, self.bearer, self.direction, b"Different data")
        self.assertNotEqual(mac1, mac2)

    def test_mac_changes_with_count(self):
        mac1 = calculate_mac_i(self.integrity_key, self.count, self.bearer, self.direction, self.data)
        mac2 = calculate_mac_i(self.integrity_key, self.count + 1, self.bearer, self.direction, self.data)
        self.assertNotEqual(mac1, mac2)

    def test_mac_changes_with_key(self):
        mac1 = calculate_mac_i(self.integrity_key, self.count, self.bearer, self.direction, self.data)
        different_key = generate_key(config.INTEGRITY_KEY_LENGTH_BYTES)
        mac2 = calculate_mac_i(different_key, self.count, self.bearer, self.direction, self.data)
        self.assertNotEqual(mac1, mac2)

    def test_pdcp_tx_rx_integrity_pass(self):
        tx = PDCPTransmitter(
            bearer_id=1, direction=0,
            integrity_key=self.integrity_key, cipher_key=self.cipher_key,
            integrity_enabled=True, ciphering_enabled=True
        )
        rx = PDCPReceiver(
            bearer_id=1, direction=0,
            integrity_key=self.integrity_key, cipher_key=self.cipher_key,
            integrity_enabled=True, ciphering_enabled=True
        )

        sdu_id = 0
        sdu_payload = b"Secure payload"
        pdu = tx.send_sdu(sdu_id, sdu_payload)

        # Simulate direct transmission (no channel impairments)
        self.assertTrue(rx.receive_pdu(pdu))
        self.assertEqual(rx.discarded_integrity_failures, 0)
        self.assertEqual(rx.successful_deliveries, 1)
        delivered_sdu = rx.get_delivered_sdus()[0]
        self.assertEqual(delivered_sdu['payload'], sdu_payload)
        self.assertTrue(pdu.integrity_verified is None or pdu.integrity_verified)

    def test_pdcp_tx_rx_integrity_fail_tampered_payload(self):
        tx = PDCPTransmitter(
            bearer_id=1, direction=0,
            integrity_key=self.integrity_key, cipher_key=self.cipher_key,
            integrity_enabled=True, ciphering_enabled=True
        )
        rx = PDCPReceiver(
            bearer_id=1, direction=0,
            integrity_key=self.integrity_key, cipher_key=self.cipher_key,
            integrity_enabled=True, ciphering_enabled=True
        )

        sdu_id = 0
        sdu_payload = b"Secure payload"
        pdu = tx.send_sdu(sdu_id, sdu_payload)

        # Tamper the PDU payload (which is ciphered SDU+MAC)
        if pdu.payload:
            tampered_payload_bytes = bytearray(pdu.payload)
            tampered_payload_bytes[0] ^= 0xFF  # Flip all bits of first byte
            pdu.payload = bytes(tampered_payload_bytes)
            pdu.is_tampered_by_channel = True  # Manually flag for test clarity

        self.assertFalse(rx.receive_pdu(pdu))  # Should fail integrity
        self.assertEqual(rx.discarded_integrity_failures, 1)
        self.assertEqual(rx.successful_deliveries, 0)

    def test_pdcp_tx_rx_integrity_fail_key_mismatch(self):
        tx = PDCPTransmitter(
            bearer_id=1, direction=0,
            integrity_key=self.integrity_key, cipher_key=self.cipher_key,
            integrity_enabled=True, ciphering_enabled=True
        )
        mismatched_key = generate_key(config.INTEGRITY_KEY_LENGTH_BYTES)
        rx = PDCPReceiver(
            bearer_id=1, direction=0,
            integrity_key=mismatched_key, cipher_key=self.cipher_key,
            integrity_enabled=True, ciphering_enabled=True
        )

        sdu_id = 0
        sdu_payload = b"Secure payload"
        pdu = tx.send_sdu(sdu_id, sdu_payload)

        self.assertFalse(rx.receive_pdu(pdu))  # Should fail integrity
        self.assertEqual(rx.discarded_integrity_failures, 1)
        self.assertEqual(rx.successful_deliveries, 0)

if __name__ == '__main__':
    unittest.main()
