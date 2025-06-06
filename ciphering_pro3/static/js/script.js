let successCount = 0;
let failCount = 0;
let eavesdropCount = 0;
let chart = null;

document.addEventListener('DOMContentLoaded', () => {
    const ctx = document.getElementById('cipheringChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Successful Decryptions', 'Failed Decryptions', 'Eavesdrop Attempts'],
            datasets: [{
                label: 'Ciphering Metrics',
                data: [successCount, failCount, eavesdropCount],
                backgroundColor: ['#34a853', '#ea4335', '#fbbc05'],
                borderColor: ['#2d8e44', '#c1362d', '#d89e04'],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Count' }
                },
                x: {
                    title: { display: true, text: 'Metrics' }
                }
            },
            plugins: { legend: { display: true } }
        }
    });
});

function runSimulation() {
    console.log("runSimulation called");

    const plaintext = document.getElementById('plaintext').value;
    if (!plaintext) {
        alert('Please enter some text to encrypt.');
        return;
    }

    console.log("Sending request to /simulate with plaintext:", plaintext);

    fetch('/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `plaintext=${encodeURIComponent(plaintext)}`
    })
    .then(response => {
        console.log("Response status:", response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("Received data:", data);
        document.getElementById('plaintext-result').textContent = data.plaintext;
        document.getElementById('ciphertext-result').textContent = data.ciphertext;
        document.getElementById('deciphered-result').textContent = data.deciphered;
        document.getElementById('eavesdrop-result').textContent = data.eavesdrop;

        // Update chart
        if (chart) {
            if (data.deciphered !== 'Failed') {
                successCount++;
            } else {
                failCount++;
            }
            eavesdropCount++;
            chart.data.datasets[0].data = [successCount, failCount, eavesdropCount];
            chart.update();
        } else {
            console.error("Chart is not initialized");
        }
    })
    .catch(error => {
        console.error('Error in fetch request:', error);
        alert('Simulation failed. Check the console for details.');
    });
}