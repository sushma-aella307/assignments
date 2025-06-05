# pdcp_security_project/src/pdcp_entity.py
import collections
import logging
from .pdcp_packet import PDCP_PDU
from . import crypto_stub
from . import cipher_stub # Assuming you have this
from config import SN_LENGTH_BITS, HFN_LENGTH_BITS, WINDOW_SIZE

# Setup basic logging
logger = logging.getLogger(__name__)

class PDCPTransmitter:
    def __init__(self, bearer_id: int, direction: int, integrity_key: bytes = None, cipher_key: bytes = None,
                 integrity_enabled: bool = False, ciphering_enabled: bool = False, sn_length_bits: int = SN_LENGTH_BITS):
        self.bearer_id = bearer_id
        self.direction = direction  # 0 for UL, 1 for DL

        self.integrity_key = integrity_key
        self.cipher_key = cipher_key
        self.integrity_enabled = integrity_enabled
        self.ciphering_enabled = ciphering_enabled

        if self.integrity_enabled and not self.integrity_key:
            raise ValueError("Integrity enabled but no integrity key provided.")
        if self.ciphering_enabled and not self.cipher_key:
            raise ValueError("Ciphering enabled but no cipher key provided.")

        self.sn_length_bits = sn_length_bits
        self.max_sn = (1 << self.sn_length_bits) - 1
        self.hfn_latch = 0 # Current HFN
        self.next_tx_sn = 0 # Next PDCP SN to be used
        self.tx_count = 0 # Full 32-bit COUNT for transmission

        logger.info(f"PDCP Tx initialized for Bearer {bearer_id}, Direction {direction}, "
                    f"Integrity: {'Enabled' if integrity_enabled else 'Disabled'}, "
                    f"Ciphering: {'Enabled' if ciphering_enabled else 'Disabled'}")

    def _get_current_count_and_increment(self):
        current_count = (self.hfn_latch << self.sn_length_bits) | self.next_tx_sn
        self.tx_count = current_count # For internal tracking if needed

        sn_to_use = self.next_tx_sn
        hfn_to_use = self.hfn_latch

        self.next_tx_sn += 1
        if self.next_tx_sn > self.max_sn:
            self.next_tx_sn = 0
            self.hfn_latch = (self.hfn_latch + 1) % (1 << (32 - self.sn_length_bits))
        return current_count, sn_to_use, hfn_to_use

    def send_sdu(self, sdu_id: int, sdu_payload: bytes) -> PDCP_PDU:
        sdu_count, sn, hfn = self._get_current_count_and_increment()
        logger.debug(f"[TX B:{self.bearer_id} D:{self.direction}] Preparing SDU ID {sdu_id}, COUNT={sdu_count}, SN={sn}, HFN={hfn}")

        # 1. (Optional) Header Compression - STUBBED
        # For simplicity, compressed_payload is the same as sdu_payload
        compressed_payload = sdu_payload # Replace with actual RoHC if implemented

        # Data to be integrity protected (PDCP Header info + SDU)
        # For simplicity in this simulation, the "PDCP Header info" part is implicitly covered by
        # COUNT, BEARER, DIRECTION inputs to MAC-I. The `data_for_integrity` is the SDU.
        # In a real PDU, you'd construct header bytes. Here, `compressed_payload` is what MAC-I is calculated over.
        data_for_integrity = compressed_payload
        
        calculated_mac_i = None
        if self.integrity_enabled:
            calculated_mac_i = crypto_stub.calculate_mac_i(
                self.integrity_key, sdu_count, self.bearer_id, self.direction, data_for_integrity
            )
            logger.debug(f"[TX B:{self.bearer_id}] SDU ID {sdu_id} COUNT {sdu_count}: Calculated MAC-I: {calculated_mac_i.hex()}")
            payload_to_cipher = data_for_integrity + calculated_mac_i
        else:
            payload_to_cipher = data_for_integrity
            logger.debug(f"[TX B:{self.bearer_id}] SDU ID {sdu_id} COUNT {sdu_count}: Integrity disabled, no MAC-I.")

        # 2. Ciphering (after integrity protection, MAC is also ciphered)
        final_payload_for_pdu = payload_to_cipher # Default if ciphering is off
        if self.ciphering_enabled:
            final_payload_for_pdu = cipher_stub.encrypt(
                self.cipher_key, sdu_count, self.bearer_id, self.direction, payload_to_cipher
            )
            logger.debug(f"[TX B:{self.bearer_id}] SDU ID {sdu_id} COUNT {sdu_count}: Ciphered payload length: {len(final_payload_for_pdu)}")
        else:
            logger.debug(f"[TX B:{self.bearer_id}] SDU ID {sdu_id} COUNT {sdu_count}: Ciphering disabled.")

        # Create PDCP PDU
        # The `payload` field of PDCP_PDU now holds the (possibly compressed), (possibly integrity protected), (possibly ciphered) data.
        # The `mac_i` field in the PDU stores the *plaintext* MAC-I for the transmitter's own record or logging.
        # It's not strictly needed in the PDU object if the MAC is embedded in `final_payload_for_pdu` and extracted by Rx.
        # However, storing it can be useful for debugging/verification.
        pdu = PDCP_PDU(sdu_id, sn, sdu_count, hfn, final_payload_for_pdu, mac_i=calculated_mac_i)
        pdu.status = "TX_Prepared"
        logger.info(f"[TX B:{self.bearer_id} D:{self.direction}] SENT SDU ID {sdu_id} as PDU (SN:{sn}, COUNT:{sdu_count}, MAC:{calculated_mac_i.hex() if calculated_mac_i else 'N/A'})")
        return pdu


class PDCPReceiver:
    def __init__(self, bearer_id: int, direction: int, integrity_key: bytes = None, cipher_key: bytes = None,
                 integrity_enabled: bool = False, ciphering_enabled: bool = False, sn_length_bits: int = SN_LENGTH_BITS):
        self.bearer_id = bearer_id
        self.direction = direction # Should be opposite of Tx (e.g. 1 for DL if Tx is UL)

        self.integrity_key = integrity_key
        self.cipher_key = cipher_key
        self.integrity_enabled = integrity_enabled
        self.ciphering_enabled = ciphering_enabled
        
        if self.integrity_enabled and not self.integrity_key:
            raise ValueError("Integrity enabled but no integrity key provided.")
        # Ciphering can be enabled even if integrity is not, but key is needed if enabled.
        if self.ciphering_enabled and not self.cipher_key:
            raise ValueError("Ciphering enabled but no cipher key provided.")

        self.sn_length_bits = sn_length_bits
        self.max_sn = (1 << self.sn_length_bits) - 1
        self.window_size = WINDOW_SIZE # From config, e.g., 2**(SN_LENGTH_BITS - 1)

        self.last_delivered_sn = -1 # SN of the last in-sequence PDU delivered
        self.next_expected_sn = 0   # SN expected for in-order delivery
        self.hfn_rcv = 0            # Current HFN at receiver side
        
        self.reordering_buffer = {} # SN -> PDCP_PDU
        self.delivered_sdus = []    # List of (sdu_id, payload)
        self.received_counts = set() # To detect duplicates based on full COUNT

        self.discarded_integrity_failures = 0
        self.discarded_duplicates = 0
        self.discarded_old_packets = 0
        self.successful_deliveries = 0
        
        logger.info(f"PDCP Rx initialized for Bearer {bearer_id}, Direction {direction}, "
                    f"Integrity: {'Enabled' if integrity_enabled else 'Disabled'}, "
                    f"Ciphering: {'Enabled' if ciphering_enabled else 'Disabled'}")

    def _estimate_hfn(self, rcvd_sn: int) -> int:
        # Simplified HFN estimation. More robust logic may be needed for wrap-around.
        # This estimation is crucial for COUNT reconstruction.
        # Assumes rcvd_sn is reasonably close to next_expected_sn or last_delivered_sn
        ref_sn = self.last_delivered_sn if self.last_delivered_sn != -1 else self.next_expected_sn

        if abs(rcvd_sn - ref_sn) < self.window_size:
            # SN is within window, HFN is likely the same
            return self.hfn_rcv
        elif rcvd_sn < ref_sn and (ref_sn - rcvd_sn) > (self.max_sn - self.window_size +1) : # Late arrival from previous HFN cycle
            # Received SN is small, reference SN is large -> HFN likely wrapped
             return (self.hfn_rcv + 1) % (1 << (32 - self.sn_length_bits))
        elif rcvd_sn > ref_sn and (rcvd_sn - ref_sn) > (self.max_sn - self.window_size +1): # Early arrival for next HFN cycle
            # Received SN is large, reference SN is small -> HFN likely from previous cycle (packet very old or reordered)
            if self.hfn_rcv > 0:
                return (self.hfn_rcv - 1) % (1 << (32 - self.sn_length_bits))
            else: # Cannot go below HFN 0
                 return 0 # Or handle as out-of-window error more explicitly
        return self.hfn_rcv # Default if unsure or within typical window

    def _reconstruct_count(self, rcvd_sn: int) -> int:
        estimated_hfn = self._estimate_hfn(rcvd_sn)
        return (estimated_hfn << self.sn_length_bits) | rcvd_sn

    def receive_pdu(self, pdu: PDCP_PDU):
        logger.debug(f"[RX B:{self.bearer_id} D:{self.direction}] Received PDU: SDU_ID {pdu.sdu_id}, SN {pdu.sn}, In-Payload len {len(pdu.payload)}")
        pdu.status = "RX_Received"

        if pdu.is_corrupted_by_channel: # This is physical layer CRC failure, not integrity
            logger.warning(f"[RX B:{self.bearer_id}] Discarding PDU SDU_ID {pdu.sdu_id} (SN {pdu.sn}) due to channel corruption.")
            pdu.status = "Discarded_ChannelCorruption"
            return False # Cannot process further

        # 1. Reconstruct COUNT
        # NOTE: COUNT reconstruction MUST happen before deciphering and integrity if they depend on COUNT.
        rcvd_count = self._reconstruct_count(pdu.sn)
        pdu.count = rcvd_count # Update PDU with reconstructed COUNT for logging/consistency
        logger.debug(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (SN {pdu.sn}): Reconstructed COUNT = {rcvd_count} (Est. HFN {rcvd_count >> self.sn_length_bits})")

        # 2. Deciphering
        # The PDU payload contains (SDU + MAC-I) ciphered together if ciphering was enabled.
        payload_after_deciphering = pdu.payload # Default if ciphering is off
        if self.ciphering_enabled:
            if not self.cipher_key:
                logger.error(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Ciphering enabled but no key. CANNOT DECIPHER.")
                pdu.status = "Discarded_DecipherError_NoKey"
                return False # Critical error

            payload_after_deciphering = cipher_stub.decrypt(
                self.cipher_key, rcvd_count, self.bearer_id, self.direction, pdu.payload
            )
            logger.debug(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Deciphered payload length: {len(payload_after_deciphering)}")
            if pdu.is_tampered_by_channel:
                 logger.warning(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Payload was tampered in channel. Deciphered content may be garbage.")
        else:
            logger.debug(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Ciphering disabled.")


        # 3. Integrity Verification (if enabled)
        # MAC-I is 4 bytes. It was appended to the SDU before ciphering.
        # So, after deciphering, the last 4 bytes are the received MAC-I.
        deciphered_sdu_data = payload_after_deciphering
        received_mac_i = None

        if self.integrity_enabled:
            if len(payload_after_deciphering) < 4:
                logger.error(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Deciphered payload too short ({len(payload_after_deciphering)} bytes) to contain MAC-I. Integrity check failed.")
                pdu.integrity_verified = False
                pdu.status = "Discarded_IntegrityFailure_Short"
                self.discarded_integrity_failures += 1
                return False

            deciphered_sdu_data = payload_after_deciphering[:-4]
            received_mac_i = payload_after_deciphering[-4:]
            pdu.mac_i = received_mac_i # Store the extracted MAC-I in the PDU object
            logger.debug(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Received MAC-I (extracted): {received_mac_i.hex()}")

            if not self.integrity_key:
                logger.error(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Integrity enabled but no key. CANNOT VERIFY.")
                pdu.integrity_verified = False # Cannot verify
                pdu.status = "Discarded_IntegrityFailure_NoKey"
                self.discarded_integrity_failures += 1 # Treat as failure
                return False

            calculated_x_mac = crypto_stub.calculate_mac_i(
                self.integrity_key, rcvd_count, self.bearer_id, self.direction, deciphered_sdu_data
            )
            logger.debug(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Calculated X-MAC: {calculated_x_mac.hex()}")

            if calculated_x_mac != received_mac_i:
                logger.warning(f"!!! INTEGRITY FAILURE !!! [RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): MAC mismatch. Expected {calculated_x_mac.hex()}, Got {received_mac_i.hex()}. Discarding PDU.")
                pdu.integrity_verified = False
                pdu.status = "Discarded_IntegrityFailure"
                self.discarded_integrity_failures += 1
                # If PDU was marked as tampered by channel, this is expected.
                if pdu.is_tampered_by_channel:
                    logger.info(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id}: Integrity failure was due to simulated tampering.")
                return False # Discard packet
            else:
                logger.info(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Integrity VERIFIED.")
                pdu.integrity_verified = True
        else:
            # Integrity not enabled, so implicitly verified (or rather, not checked)
            pdu.integrity_verified = None # Mark as not applicable or True by default
            logger.debug(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}): Integrity check disabled/skipped.")
        
        pdu.deciphered_payload_data = deciphered_sdu_data # Store the actual user data part

        # 4. Duplicate Check (using full COUNT)
        if rcvd_count in self.received_counts:
            logger.warning(f"[RX B:{self.bearer_id}] Discarding PDU SDU_ID {pdu.sdu_id} (COUNT {rcvd_count}) as duplicate.")
            pdu.status = "Discarded_Duplicate"
            self.discarded_duplicates += 1
            return False
        self.received_counts.add(rcvd_count)

        # 5. Old Packet Check (based on sliding window, simplified)
        # Define lower edge of receive window based on next_expected_sn and hfn_rcv
        # This logic needs to be robust for SN wrap-around.
        # A simple check: if SN is too far behind next_expected_sn, considering wrap-around.
        # Example: next_expected_sn=5, window_size=1024, max_sn=4095. Window is roughly [ (5-1024+4096)%4096 ... 5 ]
        # A packet is "old" if its SN falls outside the reception window.
        # Window: [RX_DELIV - Reordering_Window_Size + 1, RX_DELIV + Reordering_Window_Size]
        # More simply: if rcvd_count < ( (self.hfn_rcv << self.sn_length_bits | self.next_expected_sn) - self.window_size * SOME_FACTOR ):
        # For now, a basic check: if rcvd_sn is significantly less than next_expected_sn and not a wrap-around case.
        # This is complex; often tied to timer-based discard or explicit window boundaries.
        # A simpler out-of-window check:
        lower_window_edge_sn = (self.next_expected_sn - self.window_size + self.max_sn + 1) % (self.max_sn + 1)
        
        # This check is tricky. If a packet's COUNT is too old, it might be discarded.
        # We rely on the HFN estimation and the `received_counts` for robust replay protection.
        # A true "old packet" check might use a discard timer or if COUNT is outside a very large window.
        # For this simulation, the duplicate check using full COUNT is the primary defense against most replays
        # after integrity is verified.

        # 6. Add to Reordering Buffer
        self.reordering_buffer[pdu.sn] = pdu
        logger.debug(f"[RX B:{self.bearer_id}] SDU_ID {pdu.sdu_id} (SN {pdu.sn}) added to reordering buffer.")
        pdu.status = "RX_Buffered"

        # 7. In-order Delivery from Reordering Buffer
        delivered_now = []
        while self.next_expected_sn in self.reordering_buffer:
            pdu_to_deliver = self.reordering_buffer.pop(self.next_expected_sn)
            
            # Update HFN if SN wraps around
            if self.next_expected_sn == 0 and self.last_delivered_sn == self.max_sn :
                self.hfn_rcv = (self.hfn_rcv + 1) % (1 << (32 - self.sn_length_bits))
                logger.info(f"[RX B:{self.bearer_id}] HFN incremented to {self.hfn_rcv} due to SN wrap-around.")

            self.last_delivered_sn = self.next_expected_sn
            self.next_expected_sn = (self.next_expected_sn + 1) % (self.max_sn + 1)
            
            self.delivered_sdus.append({'sdu_id': pdu_to_deliver.sdu_id, 
                                        'payload': pdu_to_deliver.deciphered_payload_data, 
                                        'count': pdu_to_deliver.count})
            pdu_to_deliver.status = "Delivered"
            self.successful_deliveries += 1
            logger.info(f"[RX B:{self.bearer_id}] Delivered SDU ID {pdu_to_deliver.sdu_id} (SN {pdu_to_deliver.sn}, COUNT {pdu_to_deliver.count}) in-order.")
            delivered_now.append(pdu_to_deliver)
        
        return True # Successfully processed or buffered

    def get_delivered_sdus(self):
        return self.delivered_sdus

    def get_stats(self):
        return {
            "successful_deliveries": self.successful_deliveries,
            "discarded_integrity_failures": self.discarded_integrity_failures,
            "discarded_duplicates": self.discarded_duplicates,
            "discarded_old_packets": self.discarded_old_packets, # Placeholder, not fully implemented
            "buffered_packets": len(self.reordering_buffer)
        }