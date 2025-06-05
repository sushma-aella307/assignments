# pdcp_security_project/app.py
from flask import Flask, render_template, request, jsonify, session, url_for
import threading
import time
import logging
import io
import copy 
import os 
import matplotlib # For checking backend

from src.pdcp_entity import PDCPTransmitter, PDCPReceiver
from src.channel_simulator import ImpairedChannel
from src.crypto_stub import generate_key
from src import cipher_stub
from src.plotting_utils import generate_summary_plot
import config as app_config 

app = Flask(__name__)
# IMPORTANT: Change this key for any production or shared environment!
app.secret_key = "pdcp_sim_very_secret_key_!@#$%" 

class SimulationLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_records = []

    def emit(self, record):
        log_entry = self.format(record)
        self.log_records.append(log_entry)
    
    def get_logs(self):
        return list(self.log_records) 
    
    def clear_logs(self):
        self.log_records = []

sim_log_handler = SimulationLogHandler()
sim_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'))

# Setup loggers that will use sim_log_handler during simulation
pdcp_entity_logger = logging.getLogger('src.pdcp_entity')
channel_sim_logger = logging.getLogger('src.channel_simulator')
app_specific_logger = logging.getLogger(__name__) # Renamed to avoid confusion with flask 'app.logger'
plotting_logger = logging.getLogger('src.plotting_utils')

simulation_threads = {} # Stores active simulation threads by sim_id

def setup_simulation_loggers_for_thread():
    # Configure loggers for the current simulation thread
    for logger_instance in [pdcp_entity_logger, channel_sim_logger, app_specific_logger, plotting_logger]:
        # Remove first to prevent duplicates if called multiple times for the same logger
        try:
            logger_instance.removeHandler(sim_log_handler)
        except ValueError:
            pass # Handler was not there
        logger_instance.addHandler(sim_log_handler)
        logger_instance.setLevel(logging.DEBUG) # Capture all logs for display
    sim_log_handler.clear_logs()

def remove_simulation_loggers_from_thread():
    for logger_instance in [pdcp_entity_logger, channel_sim_logger, app_specific_logger, plotting_logger]:
        try:
            logger_instance.removeHandler(sim_log_handler)
        except ValueError:
            pass

def run_simulation_thread_function(sim_id, params):
    if sim_id not in session.get('simulation_state', {}):
        app_specific_logger.error(f"[{sim_id}] Simulation ID not found in session state at thread start.")
        return

    # Initialize session state for this run
    session['simulation_state'][sim_id]['status'] = 'running'
    session['simulation_state'][sim_id].setdefault('logs', [])
    session['simulation_state'][sim_id].setdefault('stats', {})
    session['simulation_state'][sim_id].setdefault('plot_url', None)
    session['simulation_state'][sim_id].setdefault('packet_pipeline', {
        "tx_pdus": [], "channel_pdus": [], "rx_input_pdus": [], "delivered_pdus": [], "discarded_pdus": []
    })
    session.modified = True 

    setup_simulation_loggers_for_thread()
    app_specific_logger.info(f"[{sim_id}] Plotting backend check: {matplotlib.get_backend()}")

    try:
        app_specific_logger.info(f"[{sim_id}] Thread started for simulation with params: {params}")

        integrity_key_shared = generate_key(app_config.INTEGRITY_KEY_LENGTH_BYTES)
        cipher_key_shared = cipher_stub.generate_cipher_key(app_config.CIPHER_KEY_LENGTH_BYTES)

        integrity_key_tx = integrity_key_shared
        integrity_key_rx = integrity_key_shared
        if params.get('key_mismatch', False):
            integrity_key_rx = generate_key(app_config.INTEGRITY_KEY_LENGTH_BYTES)
            app_specific_logger.info(f"[{sim_id}] Simulating integrity key mismatch.")

        pdcp_tx = PDCPTransmitter(
            bearer_id=app_config.BEARER_ID_DRB1, direction=app_config.DIRECTION_UPLINK,
            integrity_key=integrity_key_tx, cipher_key=cipher_key_shared,
            integrity_enabled=params['integrity_enabled'], ciphering_enabled=params['ciphering_enabled']
        )
        pdcp_rx = PDCPReceiver(
            bearer_id=app_config.BEARER_ID_DRB1, direction=app_config.DIRECTION_UPLINK,
            integrity_key=integrity_key_rx, cipher_key=cipher_key_shared,
            integrity_enabled=params['integrity_enabled'], ciphering_enabled=params['ciphering_enabled']
        )
        channel = ImpairedChannel(
            loss_rate=params['loss_rate'],
            tampering_rate=params['tampering_rate'],
            corruption_rate=params['corruption_rate'],
            duplication_rate=params.get('duplication_rate', 0.0), 
            reordering_rate=params.get('reordering_rate', 0.0),   
            max_reorder_delay=params.get('max_reorder_delay', 0) 
        )

        num_sdus = params['num_sdus']
        sdu_payload_size = params['sdu_payload_size']
        
        # Access session data within the loop carefully
        current_sim_state = session['simulation_state'][sim_id]
        current_pipeline = current_sim_state['packet_pipeline']


        for sdu_id in range(num_sdus):
            # Check for external stop signal if implemented, or just run to completion
            if session.get('simulation_state', {}).get(sim_id, {}).get('status') != 'running':
                app_specific_logger.info(f"[{sim_id}] Simulation halt detected by thread state.")
                break 
            
            base_string = f"SDU_{sdu_id}_Web_"
            remaining_length_for_random_part = sdu_payload_size - len(base_string.encode('utf-8'))
            random_hex_data = ""
            if remaining_length_for_random_part > 0:
                num_bytes_from_os_urandom = remaining_length_for_random_part // 2
                if num_bytes_from_os_urandom > 0:
                    random_hex_data = os.urandom(num_bytes_from_os_urandom).hex()
            payload_content_str = base_string + random_hex_data
            sdu_payload_bytes = payload_content_str.encode('utf-8')
            if len(sdu_payload_bytes) > sdu_payload_size:
                sdu_payload_bytes = sdu_payload_bytes[:sdu_payload_size]
            elif len(sdu_payload_bytes) < sdu_payload_size:
                sdu_payload_bytes += b'\x00' * (sdu_payload_size - len(sdu_payload_bytes))

            pdu_tx = pdcp_tx.send_sdu(sdu_id, sdu_payload_bytes)
            current_pipeline['tx_pdus'].append(pdu_to_dict(pdu_tx))

            pdus_for_channel = [pdu_tx] # Channel expects a list
            arrived_at_rx_input = channel.transmit(pdus_for_channel) # channel.transmit might modify pdu_tx in place

            # Update status of pdu_tx in the pipeline if modified by channel
            for i_tx_pdu, p_dict_tx in enumerate(current_pipeline['tx_pdus']):
                if p_dict_tx['sdu_id'] == pdu_tx.sdu_id: # pdu_tx is the object from this iteration
                    current_pipeline['tx_pdus'][i_tx_pdu] = pdu_to_dict(pdu_tx)
                    break
            
            for pdu_rx_in in arrived_at_rx_input:
                # Add to rx_input_pdus BEFORE processing by pdcp_rx
                current_pipeline['rx_input_pdus'].append(pdu_to_dict(pdu_rx_in)) 
                
                pdcp_rx.receive_pdu(pdu_rx_in) # RX processes it, pdu_rx_in object is updated
                
                updated_pdu_rx_in_dict = pdu_to_dict(pdu_rx_in) # Get dict AFTER RX processing
                # Find and update the PDU in rx_input_pdus list with its post-RX status
                for i_rx_pdu, p_dict_rx in enumerate(current_pipeline['rx_input_pdus']): 
                    if p_dict_rx['sdu_id'] == pdu_rx_in.sdu_id and p_dict_rx['status'] != updated_pdu_rx_in_dict['status']: # Update if status changed
                        current_pipeline['rx_input_pdus'][i_rx_pdu] = updated_pdu_rx_in_dict
                        break 
                # If not found or status didn't change (e.g. it was already there from a previous step), this is fine.
                # The goal is that rx_input_pdus reflects the final state after pdcp_rx.receive_pdu.

                if pdu_rx_in.status == "Delivered":
                    current_pipeline['delivered_pdus'].append(updated_pdu_rx_in_dict)
                elif pdu_rx_in.status.startswith("Discarded"):
                    current_pipeline['discarded_pdus'].append(updated_pdu_rx_in_dict)

            # Update session incrementally
            current_sim_state['logs'] = sim_log_handler.get_logs()
            current_sim_state['stats'] = pdcp_rx.get_stats()
            # current_pipeline is already being modified in place
            session.modified = True # Mark session as modified
            time.sleep(0.001) # Reduced sleep, adjust as needed (0 for max speed)

        # After loop, flush channel buffer
        remaining_channel_pdus = channel.flush_reorder_buffer()
        for pdu_rx_in in remaining_channel_pdus:
            current_pipeline['rx_input_pdus'].append(pdu_to_dict(pdu_rx_in))
            pdcp_rx.receive_pdu(pdu_rx_in)
            updated_pdu_rx_in_dict = pdu_to_dict(pdu_rx_in)
            for i_flush_pdu, p_dict_flush in enumerate(current_pipeline['rx_input_pdus']):
                if p_dict_flush['sdu_id'] == pdu_rx_in.sdu_id and p_dict_flush['status'] != updated_pdu_rx_in_dict['status']:
                    current_pipeline['rx_input_pdus'][i_flush_pdu] = updated_pdu_rx_in_dict
                    break
            if pdu_rx_in.status == "Delivered":
                current_pipeline['delivered_pdus'].append(updated_pdu_rx_in_dict)
            elif pdu_rx_in.status.startswith("Discarded"):
                current_pipeline['discarded_pdus'].append(updated_pdu_rx_in_dict)

        # Final update of session state before completing
        final_stats = pdcp_rx.get_stats()
        current_sim_state['stats'] = final_stats
        current_sim_state['logs'] = sim_log_handler.get_logs()
        
        plot_relative_url = generate_summary_plot(final_stats, output_dir="static/plots")
        app_specific_logger.debug(f"[{sim_id}] plot_relative_url from generate_summary_plot: {plot_relative_url}")
        if plot_relative_url:
            static_folder_abs = os.path.join(app.root_path, app.static_folder.strip('/\\'))
            plot_abs_path = os.path.join(static_folder_abs, plot_relative_url)
            app_specific_logger.debug(f"[{sim_id}] Absolute path for generated plot: {plot_abs_path}")
            if not os.path.exists(plot_abs_path):
                 app_specific_logger.error(f"[{sim_id}] Plot file NOT FOUND at {plot_abs_path} after generation call!")
            current_sim_state['plot_url'] = url_for('static', filename=plot_relative_url)
            app_specific_logger.info(f"[{sim_id}] Generated plot URL for client: {current_sim_state['plot_url']}")
        else:
            current_sim_state['plot_url'] = None
            app_specific_logger.warning(f"[{sim_id}] Failed to generate plot or no stats to plot.")
        
        current_sim_state['status'] = 'completed'
        app_specific_logger.info(f"[{sim_id}] Simulation completed.")
        session.modified = True

    except Exception as e:
        app_specific_logger.error(f"[{sim_id}] Error in simulation thread: {e}", exc_info=True)
        # Ensure session and sim_id are still valid before trying to update
        if 'simulation_state' in session and sim_id in session['simulation_state']:
            session['simulation_state'][sim_id]['status'] = 'error'
            session['simulation_state'][sim_id]['error_message'] = str(e)
            error_log_entry = f"SIMULATION THREAD ERROR: {e}"
            session['simulation_state'][sim_id].setdefault('logs', []).append(error_log_entry)
            session.modified = True
    finally:
        remove_simulation_loggers_from_thread()
        if sim_id in simulation_threads:
            del simulation_threads[sim_id]

def pdu_to_dict(pdu):
    if pdu is None: return None
    return {
        "sdu_id": pdu.sdu_id, "sn": pdu.sn, "count": pdu.count,
        "mac_i_hex": pdu.mac_i.hex() if pdu.mac_i else None,
        "is_tampered_by_channel": pdu.is_tampered_by_channel,
        "is_corrupted_by_channel": pdu.is_corrupted_by_channel,
        "integrity_verified": pdu.integrity_verified, "status": pdu.status
    }

@app.route('/')
def index():
    # Initialize or refresh current_sim_id
    if 'current_sim_id' not in session or \
       session.get('simulation_state', {}).get(session['current_sim_id'], {}).get('status') in ['completed', 'error', None]: # Consider None as needing refresh
        session['current_sim_id'] = "sim_" + str(int(time.time() * 100000)) # Make it more unique
    
    sim_id = session['current_sim_id']
    
    if 'simulation_state' not in session:
        session['simulation_state'] = {}
    
    # Ensure the current sim_id has a default structure in session['simulation_state']
    if sim_id not in session['simulation_state']:
         session['simulation_state'][sim_id] = {
             'status': 'idle', 'logs': [], 'stats': {}, 'plot_url': None, 
             'packet_pipeline': {"tx_pdus": [], "channel_pdus": [], "rx_input_pdus": [], "delivered_pdus": [], "discarded_pdus": []}
         }
    session.modified = True
    return render_template('index.html', sim_id=sim_id)

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    # Use the sim_id that index() should have prepared and stored in session
    sim_id = session.get('current_sim_id')
    if not sim_id: # Fallback, should not happen if index() is called first
        sim_id = "sim_" + str(int(time.time() * 100000))
        session['current_sim_id'] = sim_id

    if 'simulation_state' not in session: # Should be initialized by index()
        session['simulation_state'] = {}
    
    # Ensure this sim_id has a structure in simulation_state
    if sim_id not in session['simulation_state']:
        session['simulation_state'][sim_id] = {} # Initialize if somehow missing

    # Check if simulation for this sim_id is already running
    if session['simulation_state'][sim_id].get('status') == 'running' and \
       sim_id in simulation_threads and simulation_threads[sim_id].is_alive():
        return jsonify({"error": "A simulation for this session is already running. Please wait or reload."}), 400
    
    params = request.json
    # Reset/Initialize state for this specific sim_id for a new run
    session['simulation_state'][sim_id] = {
        'status': 'starting', 'params': params, 'logs': [], 'stats': {}, 'plot_url': None,
        'packet_pipeline': {"tx_pdus": [], "channel_pdus": [], "rx_input_pdus": [], "delivered_pdus": [], "discarded_pdus": []}
    }
    session.modified = True

    thread = threading.Thread(target=run_simulation_thread_function, args=(sim_id, params))
    thread.daemon = True 
    simulation_threads[sim_id] = thread # Store thread reference
    thread.start()
    
    return jsonify({"message": "Simulation started", "sim_id": sim_id})

@app.route('/get_status')
def get_status():
    sim_id = session.get('current_sim_id')
    default_empty_pipeline = {"tx_pdus": [], "channel_pdus": [], "rx_input_pdus": [], "delivered_pdus": [], "discarded_pdus": []}

    if not sim_id or 'simulation_state' not in session or sim_id not in session['simulation_state']:
        return jsonify({
            "sim_id": sim_id or "N/A", "status": "idle", 
            "error_message": "No simulation data found for current session." if sim_id else "Session not initialized.",
            "logs": [], "stats": {}, "plot_url": None, "packet_pipeline": default_empty_pipeline
        }), 200

    sim_data = session['simulation_state'][sim_id]
    
    # Check if a 'running' simulation's thread is still alive
    if sim_data.get('status') == 'running' and \
       (sim_id not in simulation_threads or not simulation_threads[sim_id].is_alive()):
        app_specific_logger.warning(f"[{sim_id}] Found 'running' status but thread is not alive or not in dict. Marking as error.")
        sim_data['status'] = 'error'
        sim_data['error_message'] = "Simulation thread terminated unexpectedly or was lost."
        if sim_id in simulation_threads: # Clean up if present
            del simulation_threads[sim_id]
        session.modified = True # Save updated status
        
    return jsonify({
        "sim_id": sim_id, 
        "status": sim_data.get('status', 'unknown'),
        "error_message": sim_data.get('error_message'), 
        "logs": sim_data.get('logs', []),
        "stats": sim_data.get('stats', {}), 
        "plot_url": sim_data.get('plot_url'),
        "packet_pipeline": sim_data.get('packet_pipeline', default_empty_pipeline)
    })

if __name__ == '__main__':
    # Configure general Flask app logging (not simulation-specific logs to sim_log_handler)
    werkzeug_logger = logging.getLogger('werkzeug') # Flask's internal request logger
    werkzeug_logger.setLevel(logging.INFO) 
    
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s [%(threadName)s] - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Configure app_specific_logger (for app.py's own messages)
    if not app_specific_logger.handlers: # Avoid adding multiple console handlers on reload
        app_specific_logger.addHandler(console_handler)
    app_specific_logger.setLevel(logging.DEBUG) # Set to DEBUG to see detailed app logs

    # Configure plotting_logger
    if not plotting_logger.handlers:
        plotting_logger.addHandler(console_handler)
    plotting_logger.setLevel(logging.DEBUG) # Set to DEBUG for plotting issues

    app_specific_logger.info("Starting PDCP Simulation Flask App...")
    app.run(debug=True, threaded=True, use_reloader=False) # use_reloader=False can sometimes help with thread issues in dev