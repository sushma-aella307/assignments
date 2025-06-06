from flask import Flask, render_template, request, jsonify
from pdcp_entity import PDCPTransmitter, PDCPReceiver
from channel_simulator import ChannelSimulator
from crypto_stub import generate_cipher_key, encrypt, decrypt
from config import CIPHERING_ENABLED
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import os

app = Flask(__name__, static_folder="../static", template_folder="../templates")
cipher_key = generate_cipher_key()
transmitter = PDCPTransmitter(bearer_id=5, direction=0, cipher_key=cipher_key, ciphering_enabled=CIPHERING_ENABLED)
receiver = PDCPReceiver(bearer_id=5, direction=0, cipher_key=cipher_key, ciphering_enabled=CIPHERING_ENABLED)
channel = ChannelSimulator()
wrong_key = generate_cipher_key()

# Initialize counters for plotting
success_count = 0
fail_count = 0
eavesdrop_count = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    global success_count, fail_count, eavesdrop_count
    try:
        plaintext = request.form['plaintext'].encode()
        print(f"Received plaintext: {plaintext}")

        pdu = transmitter.send_sdu(plaintext)
        print(f"PDU created: SN={pdu.sn}, HFN={pdu.hfn}, Payload={pdu.payload.hex()}")

        transmitted_pdu = channel.transmit(pdu)
        print(f"Transmitted PDU: Corrupted={transmitted_pdu.is_corrupted}")

        deciphered = receiver.receive_pdu(transmitted_pdu)
        print(f"Deciphered: {deciphered}")

        ciphertext = pdu.payload.hex()
        eavesdrop = decrypt(wrong_key, pdu.count, 5, 0, pdu.payload).hex()

        deciphered_text = deciphered.decode('utf-8', errors='replace') if deciphered else 'Failed'
        plaintext_text = plaintext.decode('utf-8', errors='replace')

        # Update counters
        if deciphered_text != 'Failed':
            success_count += 1
        else:
            fail_count += 1
        eavesdrop_count += 1

        # Generate and save plot
        labels = ['Successful Decryptions', 'Failed Decryptions', 'Eavesdrop Attempts']
        counts = [success_count, fail_count, eavesdrop_count]
        colors = ['#34a853', '#ea4335', '#fbbc05']

        plt.figure(figsize=(8, 6))
        plt.bar(labels, counts, color=colors)
        plt.xlabel('Metrics')
        plt.ylabel('Count')
        plt.title('Ciphering Metrics')

        # Ensure plots folder exists
        plots_dir = '../plots'
        if not os.path.exists(plots_dir):
            os.makedirs(plots_dir)

        # Save plot with a timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plot_path = os.path.join(plots_dir, f'ciphering_metrics_{timestamp}.png')
        plt.savefig(plot_path)
        plt.close()

        print(f"Successfully saved plot to: {plot_path}")

        response = {
            'plaintext': plaintext_text,
            'ciphertext': ciphertext,
            'deciphered': deciphered_text,
            'eavesdrop': eavesdrop
        }
        print(f"Sending response: {response}")
        return jsonify(response)
    except Exception as e:
        print(f"Error in /simulate: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)