# pdcp_security_project/src/pdcp_packet.py

class PDCP_PDU:
    def __init__(self, sdu_id, sn, count, hfn, payload, mac_i=None, is_control_pdu=False):
        self.sdu_id = sdu_id          # Original SDU identifier for tracking
        self.sn = sn                  # PDCP Sequence Number (e.g., 12 or 18 bits)
        self.count = count            # Full 32-bit COUNT value (HFN + SN)
        self.hfn = hfn                # Hyper Frame Number part of COUNT
        
        # In this model:
        # For Tx: `payload` is initially plaintext SDU. After compression (if any), integrity, ciphering,
        #         `payload` becomes the final PDCP PDU content to be sent (ciphered data + MAC).
        # For Rx: `payload` is the received PDCP PDU content (ciphered data + MAC).
        self.payload = payload # This will store the (potentially ciphered) SDU + MAC

        # mac_i:
        # On Tx side: This can store the calculated plaintext MAC-I before it's appended and ciphered.
        # On Rx side: This will store the received (and deciphered) MAC-I extracted from the payload.
        self.mac_i = mac_i

        self.is_control_pdu = is_control_pdu # e.g., PDCP status report

        # Fields for Rx side processing and logging
        self.is_corrupted_by_channel = False # Flag set by channel if random corruption occurs
        self.is_tampered_by_channel = False # Flag set by channel if malicious tampering occurs
        self.deciphered_payload_data = None # Stores SDU part after deciphering and MAC stripping
        self.integrity_verified = None  # True, False, or None (if not checked)
        self.reception_time = None      # Simulation time of reception
        self.status = "Sent"            # "Sent", "Received", "IntegrityFailed", "Delivered", "DiscardedDuplicate", "DiscardedOld"

    def __repr__(self):
        return (f"PDCP_PDU(ID:{self.sdu_id}, SN:{self.sn}, COUNT:{self.count}, MAC:{self.mac_i.hex() if self.mac_i else 'N/A'}, "
                f"Status:{self.status}, Verified:{self.integrity_verified}, Corrupted:{self.is_corrupted_by_channel}, Tampered:{self.is_tampered_by_channel})")

    def get_data_to_integrity_protect(self) -> bytes:
        """
        Returns the data over which MAC-I should be calculated.
        This is typically the PDCP header (conceptually, SN etc.) + the SDU payload.
        For simplicity, if we don't explicitly construct a PDCP header byte string,
        we can use the SDU payload directly.
        In a full implementation, this would be the serialized PDCP header (excluding MAC-I field)
        concatenated with the (compressed) SDU.
        Here, `self.payload` when this is called on TX is the SDU.
        """
        # Simplified: Assuming self.payload is the SDU data before MAC-I is appended.
        # If you model PDCP header fields like D/C, R, etc., serialize them here.
        # For now, we'll use the SDU payload passed to the transmitter.
        return self.payload # This needs to be the SDU itself.
 