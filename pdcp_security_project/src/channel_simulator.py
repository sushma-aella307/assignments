# pdcp_security_project/src/channel_simulator.py
import random
import copy
import logging

logger = logging.getLogger(__name__)

class ImpairedChannel:
    def __init__(self, loss_rate=0.0, duplication_rate=0.0, reordering_rate=0.0,
                 max_reorder_delay=0, corruption_rate=0.0, tampering_rate=0.0):
        self.loss_rate = loss_rate
        self.duplication_rate = duplication_rate
        self.reordering_rate = reordering_rate
        self.max_reorder_delay = max_reorder_delay # Number of "slots" or PDUs
        self.corruption_rate = corruption_rate # Random bit flips on payload
        self.tampering_rate = tampering_rate # "Malicious" bit flips on payload

        self.reorder_buffer = [] # Store tuples of (pdu, delay_slots_remaining)

    def _maliciously_tamper(self, pdu_to_tamper):
        """
        Simulates an attacker modifying the (encrypted) PDU payload.
        This should cause integrity check to fail at the receiver after decryption.
        """
        if pdu_to_tamper.payload and len(pdu_to_tamper.payload) > 0:
            payload_list = bytearray(pdu_to_tamper.payload) # Mutable copy
            
            # Tamper 1 to 3 bytes for more noticeable effect
            num_bytes_to_tamper = random.randint(1, min(3, len(payload_list)))
            
            for _ in range(num_bytes_to_tamper):
                tamper_idx = random.randint(0, len(payload_list) - 1)
                original_byte = payload_list[tamper_idx]
                # Flip one or more bits in the byte. XOR with a random non-zero byte.
                tampered_byte = original_byte ^ random.randint(1, 255)
                payload_list[tamper_idx] = tampered_byte
            
            pdu_to_tamper.payload = bytes(payload_list)
            pdu_to_tamper.is_tampered_by_channel = True # Mark it
            pdu_to_tamper.status = "Channel_Tampered"
            logger.warning(f"  [Channel] MALICIOUSLY TAMPERED PDU SDU_ID {pdu_to_tamper.sdu_id} (COUNT {pdu_to_tamper.count})")
        return pdu_to_tamper

    def _randomly_corrupt(self, pdu_to_corrupt):
        """
        Simulates random bit errors in the payload, like those from a noisy channel.
        Could also cause integrity check to fail if not caught by lower layer CRC.
        """
        if pdu_to_corrupt.payload and len(pdu_to_corrupt.payload) > 0:
            payload_list = bytearray(pdu_to_corrupt.payload)
            corrupt_idx = random.randint(0, len(payload_list) - 1)
            original_byte = payload_list[corrupt_idx]
            # Flip a single random bit in the chosen byte
            bit_to_flip = 1 << random.randint(0, 7)
            corrupted_byte = original_byte ^ bit_to_flip
            payload_list[corrupt_idx] = corrupted_byte
            
            pdu_to_corrupt.payload = bytes(payload_list)
            pdu_to_corrupt.is_corrupted_by_channel = True # Mark it
            pdu_to_corrupt.status = "Channel_Corrupted"
            logger.info(f"  [Channel] RANDOMLY CORRUPTED PDU SDU_ID {pdu_to_corrupt.sdu_id} (COUNT {pdu_to_corrupt.count}) at byte index {corrupt_idx}")
        return pdu_to_corrupt

    def transmit(self, pdus_to_transmit):
        """
        Simulates transmission over an impaired channel.
        Input: a list of PDCP_PDU objects from the transmitter.
        Output: a list of PDCP_PDU objects as they would arrive at the receiver.
        """
        output_pdus = []
        
        # Add new PDUs to reorder buffer along with existing ones
        for pdu in pdus_to_transmit:
            # Create a deep copy to avoid modifying the original PDU list if it's reused
            pdu_copy = copy.deepcopy(pdu)
            pdu_copy.status = "Channel_Transit"
            
            # 1. Loss
            if random.random() < self.loss_rate:
                logger.info(f"  [Channel] LOST PDU SDU_ID {pdu_copy.sdu_id} (COUNT {pdu_copy.count})")
                pdu_copy.status = "Channel_Lost"
                # Don't add to any further processing if lost
                continue # Effectively lost

            # 2. Malicious Tampering (operates on the PDU that wasn't lost)
            # This happens to the encrypted PDU on the wire.
            if random.random() < self.tampering_rate:
                self._maliciously_tamper(pdu_copy)
                # Note: Tampered PDU continues through other impairments

            # 3. Random Corruption (independent of tampering)
            if random.random() < self.corruption_rate and not pdu_copy.is_tampered_by_channel : # Avoid double "damage" for clarity
                self._randomly_corrupt(pdu_copy)
                # Note: Corrupted PDU continues

            # 4. Duplication
            if random.random() < self.duplication_rate:
                logger.info(f"  [Channel] DUPLICATED PDU SDU_ID {pdu_copy.sdu_id} (COUNT {pdu_copy.count})")
                # Add the original and its duplicate to be potentially reordered
                self.reorder_buffer.append({'pdu': copy.deepcopy(pdu_copy), 'delay': 0}) # The duplicate
                pdu_copy.status += "+Duplicated"

            # 5. Reordering: Add to buffer with a potential delay
            delay = 0
            if random.random() < self.reordering_rate and self.max_reorder_delay > 0:
                delay = random.randint(1, self.max_reorder_delay)
                logger.info(f"  [Channel] PDU SDU_ID {pdu_copy.sdu_id} (COUNT {pdu_copy.count}) will be reordered with delay {delay}")
                pdu_copy.status += f"+ReorderDelay({delay})"
            self.reorder_buffer.append({'pdu': pdu_copy, 'delay': delay})

        # Process reorder buffer: decrement delays, release PDUs with delay 0
        ready_to_send = []
        remaining_in_buffer = []
        
        for item in self.reorder_buffer:
            if item['delay'] <= 0:
                ready_to_send.append(item['pdu'])
            else:
                item['delay'] -= 1
                remaining_in_buffer.append(item)
        
        self.reorder_buffer = remaining_in_buffer
        
        # Shuffle the PDUs that are ready to be sent to simulate reordering effect
        random.shuffle(ready_to_send)
        output_pdus.extend(ready_to_send)
        
        for pdu in output_pdus:
            if not pdu.status.startswith("Channel_Lost"): # Update status if not lost
                 pdu.status = "Channel_Output"
        logger.debug(f"  [Channel] Outputting {len(output_pdus)} PDUs this cycle. {len(self.reorder_buffer)} still buffered.")
        return output_pdus

    def flush_reorder_buffer(self):
        """Call at the end of simulation to get any remaining PDUs."""
        flushed_pdus = [item['pdu'] for item in self.reorder_buffer]
        self.reorder_buffer = []
        random.shuffle(flushed_pdus) # Final shuffle
        for pdu in flushed_pdus:
             pdu.status = "Channel_Flushed"
        logger.info(f"  [Channel] Flushing {len(flushed_pdus)} PDUs from reorder buffer.")
        return flushed_pdus