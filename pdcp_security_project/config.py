# pdcp_security_project/config.py

# PDCP SN and Windowing
SN_LENGTH_BITS = 12  # Can be 12 or 18
HFN_LENGTH_BITS = 32 - SN_LENGTH_BITS  # <--- CRUCIAL LINE
WINDOW_SIZE = 2**(SN_LENGTH_BITS - 1)

# Channel Simulation Parameters
LOSS_RATE = 0.01          # Packet loss rate (0.0 to 1.0)
DUPLICATION_RATE = 0.00   # Packet duplication rate
REORDERING_RATE = 0.00    # Probability of a packet being reordered
MAX_REORDER_DELAY = 0     # Max "slots" a packet can be delayed if reordered
CORRUPTION_RATE = 0.01    # Rate of random bit corruption (simpler than tampering for now)

# Integrity Protection Parameters
INTEGRITY_ENABLED_FOR_SRB = True # Signaling Radio Bearers always have integrity
INTEGRITY_ENABLED_FOR_DRB = True # Data Radio Bearers (user plane)
TAMPERING_RATE = 0.02            # Percentage of packets to maliciously alter (0.0 to 1.0)
INTEGRITY_KEY_LENGTH_BYTES = 16  # 128-bit key

# Ciphering Parameters
CIPHERING_ENABLED_FOR_SRB = True
CIPHERING_ENABLED_FOR_DRB = True
CIPHER_KEY_LENGTH_BYTES = 16     # 128-bit key

# Simulation Settings
NUM_SDUS = 100
SDU_PAYLOAD_SIZE_BYTES = 100 # Example payload size
BEARER_ID_SRB1 = 1
BEARER_ID_DRB1 = 5
DIRECTION_UPLINK = 0
DIRECTION_DOWNLINK = 1

# Logging
LOG_LEVEL = "INFO" # DEBUG, INFO, WARNING, ERROR