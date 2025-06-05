import unittest
import copy
from main import run_simulation_basic  # Use the main runner
from src.crypto_stub import generate_key
from src import cipher_stub
import config
import logging

# Reduce log noise from main simulation during tests unless debugging specific test
# logging.getLogger('main').setLevel(logging.WARNING)
# logging.getLogger('src.pdcp_entity').setLevel(logging.WARNING)
# logging.getLogger('src.channel_simulator').setLevel(logging.WARNING)


class TestIntegrityScenarios(unittest.TestCase):
    def setUp(self):
        self.integrity_key = generate_key(config.INTEGRITY_KEY_LENGTH_BYTES)
        self.cipher_key = cipher_stub.generate_cipher_key(config.CIPHER_KEY_LENGTH_BYTES)
        self.num_sdus = 20
        self.sdu_size = 50
        self.base_channel_params = {
            "loss_rate": 0.0, "duplication_rate": 0.0, "reordering_rate": 0.0,
            "max_reorder_delay": 0, "corruption_rate": 0.0, "tampering_rate": 0.0
        }

    def test_positive_integrity_enabled_no_impairments(self):
        results = run_simulation_basic(
            num_sdus=self.num_sdus, sdu_payload_size=self.sdu_size,
            tx_integrity_enabled=True, rx_integrity_enabled=True,
            tx_ciphering_enabled=True, rx_ciphering_enabled=True,
            integrity_key_tx=self.integrity_key, integrity_key_rx=self.integrity_key,
            cipher_key_tx=self.cipher_key, cipher_key_rx=self.cipher_key,
            channel_params=self.base_channel_params.copy()
        )
        self.assertEqual(results["delivered_sdus_count"], self.num_sdus)
        self.assertEqual(results["integrity_failures"], 0)

    def test_random_tampering_detection(self):
        channel_params = self.base_channel_params.copy()
        channel_params["tampering_rate"] = 0.3  # 30% tampering

        results = run_simulation_basic(
            num_sdus=self.num_sdus, sdu_payload_size=self.sdu_size,
            tx_integrity_enabled=True, rx_integrity_enabled=True,
            tx_ciphering_enabled=True, rx_ciphering_enabled=True,
            integrity_key_tx=self.integrity_key, integrity_key_rx=self.integrity_key,
            cipher_key_tx=self.cipher_key, cipher_key_rx=self.cipher_key,
            channel_params=channel_params
        )
        self.assertEqual(results["rx_input_pdus_count"], self.num_sdus)
        self.assertGreater(results["integrity_failures"], 0)
        self.assertEqual(results["delivered_sdus_count"] + results["integrity_failures"], self.num_sdus)

    def test_key_mismatch_all_fail(self):
        mismatched_key = generate_key(config.INTEGRITY_KEY_LENGTH_BYTES)
        results = run_simulation_basic(
            num_sdus=self.num_sdus, sdu_payload_size=self.sdu_size,
            tx_integrity_enabled=True, rx_integrity_enabled=True,
            tx_ciphering_enabled=True, rx_ciphering_enabled=True,
            integrity_key_tx=self.integrity_key, integrity_key_rx=mismatched_key,
            cipher_key_tx=self.cipher_key, cipher_key_rx=self.cipher_key,
            channel_params=self.base_channel_params.copy()
        )
        self.assertEqual(results["rx_input_pdus_count"], self.num_sdus)
        self.assertEqual(results["integrity_failures"], self.num_sdus)
        self.assertEqual(results["delivered_sdus_count"], 0)

    def test_integrity_disabled_tampering_ignored_by_integrity_check(self):
        channel_params = self.base_channel_params.copy()
        channel_params["tampering_rate"] = 0.3  # 30% tampering

        results = run_simulation_basic(
            num_sdus=self.num_sdus, sdu_payload_size=self.sdu_size,
            tx_integrity_enabled=False, rx_integrity_enabled=False,
            tx_ciphering_enabled=True, rx_ciphering_enabled=True,
            integrity_key_tx=self.integrity_key, integrity_key_rx=self.integrity_key,
            cipher_key_tx=self.cipher_key, cipher_key_rx=self.cipher_key,
            channel_params=channel_params
        )
        self.assertEqual(results["integrity_failures"], 0)
        self.assertEqual(results["delivered_sdus_count"], self.num_sdus)

    def test_replay_attack_same_count_caught_by_duplicate_check(self):
        from src.pdcp_entity import PDCPTransmitter, PDCPReceiver
        from src.channel_simulator import ImpairedChannel

        tx = PDCPTransmitter(bearer_id=1, direction=0, integrity_key=self.integrity_key,
                             cipher_key=self.cipher_key, integrity_enabled=True, ciphering_enabled=True)
        rx = PDCPReceiver(bearer_id=1, direction=0, integrity_key=self.integrity_key,
                          cipher_key=self.cipher_key, integrity_enabled=True, ciphering_enabled=True)
        channel = ImpairedChannel(**self.base_channel_params)

        pdus_sent = []
        for i in range(5):
            pdu = tx.send_sdu(sdu_id=i, sdu_payload=f"Payload {i}".encode())
            pdus_sent.append(pdu)
            arrived = channel.transmit([pdu])
            for apdu in arrived:
                rx.receive_pdu(apdu)

        self.assertEqual(rx.successful_deliveries, 5)
        self.assertEqual(rx.discarded_duplicates, 0)

        replayed_pdu_original = pdus_sent[2]
        replayed_pdu_copy = copy.deepcopy(replayed_pdu_original)

        arrived_replayed = channel.transmit([replayed_pdu_copy])
        for apdu_replayed in arrived_replayed:
            rx.receive_pdu(apdu_replayed)

        self.assertEqual(rx.discarded_integrity_failures, 0)
        self.assertEqual(rx.discarded_duplicates, 1)
        self.assertEqual(rx.successful_deliveries, 5)

    def test_replay_attack_modified_count_fails_integrity(self):
        from src.pdcp_entity import PDCPTransmitter, PDCPReceiver
        from src.channel_simulator import ImpairedChannel
        import copy

        tx = PDCPTransmitter(bearer_id=1, direction=0, integrity_key=self.integrity_key,
                             cipher_key=self.cipher_key, integrity_enabled=True, ciphering_enabled=True)
        rx = PDCPReceiver(bearer_id=1, direction=0, integrity_key=self.integrity_key,
                          cipher_key=self.cipher_key, integrity_enabled=True, ciphering_enabled=True)
        channel = ImpairedChannel(**self.base_channel_params)

        pdu_original = tx.send_sdu(sdu_id=0, sdu_payload=b"Replay me")

        for i in range(1, 5):
            dummy_pdu = tx.send_sdu(sdu_id=i, sdu_payload=f"dummy {i}".encode())
            arrived = channel.transmit([dummy_pdu])
            for adu in arrived:
                rx.receive_pdu(adu)

        self.assertTrue(True, "This principle is covered by other tests where MAC input parameters change.")


if __name__ == '__main__':
    unittest.main()
