// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('startButton');
    const logsDiv = document.getElementById('logs');
    const statsDiv = document.getElementById('statsContainer');
    const plotContainer = document.getElementById('plotContainer'); // Get plot container
    
    const txLane = document.getElementById('txLanePackets');
    const channelLane = document.getElementById('channelLanePackets');
    const rxLane = document.getElementById('rxLanePackets');
    const deliveredLane = document.getElementById('deliveredLanePackets');

    let simulationRunning = false;
    let intervalId = null;
    let allPackets = {}; 

    startButton.addEventListener('click', async function() {
        if (simulationRunning) {
            console.log("Simulation stop requested (not fully implemented for ongoing sim). Reload to restart cleanly.");
            if (intervalId) clearInterval(intervalId);
            simulationRunning = false;
            startButton.textContent = "Start Simulation";
            return;
        }

        logsDiv.innerHTML = '';
        statsDiv.innerHTML = '';
        plotContainer.innerHTML = '<p>Plot will appear here after simulation completes.</p>'; // Reset plot
        txLane.innerHTML = '';
        channelLane.innerHTML = '';
        rxLane.innerHTML = '';
        deliveredLane.innerHTML = '';
        allPackets = {};

        const simParams = {
            num_sdus: parseInt(document.getElementById('numSdus').value),
            sdu_payload_size: parseInt(document.getElementById('sduSize').value),
            integrity_enabled: document.getElementById('integrityEnabled').checked,
            ciphering_enabled: document.getElementById('cipheringEnabled').checked,
            loss_rate: parseFloat(document.getElementById('lossRate').value),
            tampering_rate: parseFloat(document.getElementById('tamperingRate').value),
            corruption_rate: parseFloat(document.getElementById('corruptionRate').value),
            key_mismatch: document.getElementById('keyMismatch').checked
        };

        startButton.textContent = "Running...";
        startButton.disabled = true;
        simulationRunning = true;

        try {
            const response = await fetch('/start_simulation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(simParams)
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            fetchStatus();
            if (intervalId) clearInterval(intervalId); 
            intervalId = setInterval(fetchStatus, 1000); 
        } catch (error) {
            logsDiv.innerHTML = `<div class="log-entry log-ERROR">Error starting simulation: ${error.message}</div>`;
            simulationRunning = false;
            startButton.textContent = "Start Simulation";
            startButton.disabled = false;
        }
    });

    async function fetchStatus() {
        if (!simulationRunning) return;

        try {
            const response = await fetch('/get_status');
            const data = await response.json(); // Try to parse JSON even if not ok, for error messages

            if (!response.ok) {
                if (response.status === 404 && data.status === "idle") { 
                    console.log("Session might have expired or no active simulation.");
                     // No need to stop polling if server says idle, means it's ready for new sim
                } else if (data && data.error) {
                     throw new Error(data.error || `HTTP error! status: ${response.status}`);
                } else {
                     throw new Error(`HTTP error! status: ${response.status}`);
                }
                return; // Don't proceed if response not ok (unless it's an idle status from server)
            }
            
            updateLogs(data.logs);
            updateStats(data.stats);
            updatePacketVisualization(data.packet_pipeline);

            // --- UPDATE PLOT ---
            if (data.plot_url) {
                plotContainer.innerHTML = `<img src="${data.plot_url}" alt="Simulation Summary Plot" style="max-width: 100%;">`;
            } else if (data.status === 'completed' && !data.plot_url) {
                 plotContainer.innerHTML = '<p>Plot generation failed or no data to plot.</p>';
            }
            // --- END PLOT UPDATE ---


            if (data.status === "completed" || data.status === "error") {
                simulationCompleted(data.status === "error" ? data.error_message : "");
            }
        } catch (error) {
            console.error('Error fetching status:', error);
            // Don't stop polling immediately, server might recover or it's a transient issue.
            // If error persists, user might need to reload.
        }
    }
    
    function simulationCompleted(errorMessage = "") {
        if (intervalId) clearInterval(intervalId);
        intervalId = null;
        simulationRunning = false;
        startButton.textContent = "Start Simulation";
        startButton.disabled = false;
        if (errorMessage) {
             logsDiv.innerHTML += `<div class="log-entry log-ERROR">Simulation ended with error: ${errorMessage}</div>`;
        } else {
             logsDiv.innerHTML += `<div class="log-entry log-INFO"><strong>Simulation Completed.</strong></div>`;
        }
        logsDiv.scrollTop = logsDiv.scrollHeight; 
    }

    // ... (updateLogs, updateStats, formatStatKey, updatePacketVisualization, createPacketDiv - same as before) ...
    function updateLogs(logMessages) {
        if (!logMessages || !Array.isArray(logMessages)) return;
        const currentLogCount = logsDiv.children.length;
        for (let i = currentLogCount; i < logMessages.length; i++) {
            const logEntry = document.createElement('div');
            const parts = logMessages[i].split(' - ');
            let level = "INFO"; 
            if (parts.length > 1) {
                const levelPart = parts[1].trim();
                if (["DEBUG", "INFO", "WARNING", "ERROR"].includes(levelPart)) {
                    level = levelPart;
                }
            }
            logEntry.className = `log-entry log-${level}`;
            logEntry.textContent = logMessages[i];
            logsDiv.appendChild(logEntry);
        }
        if(logsDiv.children.length > 0){ // Scroll only if there are logs
             logsDiv.scrollTop = logsDiv.scrollHeight;
        }
    }

    function updateStats(statsData) {
        if (!statsData || Object.keys(statsData).length === 0) {
            statsDiv.innerHTML = "<p>No stats available yet.</p>";
            return;
        }
        let html = '<ul>';
        for (const key in statsData) {
            html += `<li><strong>${formatStatKey(key)}:</strong> ${statsData[key]}</li>`;
        }
        html += '</ul>';
        statsDiv.innerHTML = html;
    }

    function formatStatKey(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    function updatePacketVisualization(pipeline) {
        if (!pipeline) return;

        (pipeline.tx_pdus || []).forEach(p => allPackets[p.sdu_id] = {...allPackets[p.sdu_id], ...p, lane: 'tx'});
        (pipeline.channel_pdus || []).forEach(p => allPackets[p.sdu_id] = {...allPackets[p.sdu_id], ...p, lane: 'channel'});
        (pipeline.rx_input_pdus || []).forEach(p => allPackets[p.sdu_id] = {...allPackets[p.sdu_id], ...p, lane: 'rx_input'});
        (pipeline.delivered_pdus || []).forEach(p => allPackets[p.sdu_id] = {...allPackets[p.sdu_id], ...p, lane: 'delivered'});
        (pipeline.discarded_pdus || []).forEach(p => allPackets[p.sdu_id] = {...allPackets[p.sdu_id], ...p, lane: 'discarded'});

        txLane.innerHTML = '';
        channelLane.innerHTML = '';
        rxLane.innerHTML = '';
        deliveredLane.innerHTML = '';
        
        const sduIds = Object.keys(allPackets).map(id => parseInt(id)).sort((a,b) => a - b);

        sduIds.forEach(sdu_id => {
            const p = allPackets[sdu_id];
            if (!p || !p.sdu_id) return; // Basic check for valid packet data

            const packetDiv = createPacketDiv(p);
            
            if (p.status === "Delivered") {
                deliveredLane.appendChild(packetDiv);
            } else if (p.status && p.status.startsWith("Discarded")) {
                 rxLane.appendChild(packetDiv); 
            } else if (p.lane === 'rx_input' || (p.status && p.status.startsWith("RX_"))) {
                rxLane.appendChild(packetDiv);
            } else if (p.lane === 'channel' || (p.status && p.status.startsWith("Channel_"))) {
                channelLane.appendChild(packetDiv);
            } else if (p.lane === 'tx' || (p.status && p.status.startsWith("TX_"))) {
                txLane.appendChild(packetDiv);
            } else {
                // Fallback or unhandled packet state, maybe add to a general lane or log it
                // For now, if no clear lane, it won't be visualized to avoid clutter.
            }
        });
    }

    function createPacketDiv(pdu) {
        const div = document.createElement('div');
        div.className = `packet status-${pdu.status || 'Unknown'}`;
        div.textContent = pdu.sn !== undefined ? pdu.sn : pdu.sdu_id; 

        const tooltip = document.createElement('span');
        tooltip.className = 'packet-tooltip';
        let tooltipText = `ID: ${pdu.sdu_id}, SN: ${pdu.sn !== undefined ? pdu.sn : 'N/A'}, COUNT: ${pdu.count !== undefined ? pdu.count : 'N/A'}\nStatus: ${pdu.status || 'N/A'}\n`;
        if (pdu.mac_i_hex) tooltipText += `MAC: ${pdu.mac_i_hex}\n`;
        if (pdu.integrity_verified !== undefined && pdu.integrity_verified !== null) tooltipText += `Integrity: ${pdu.integrity_verified}\n`;
        if (pdu.is_tampered_by_channel) tooltipText += `Tampered!\n`;
        if (pdu.is_corrupted_by_channel) tooltipText += `Corrupted!\n`;
        tooltip.innerText = tooltipText;
        div.appendChild(tooltip);
        
        return div;
    }
});