// QueueLess - Live User Queue Status Polling Script

(function() {
    let tokenId = null;
    let pollInterval = null;
    let countdownInterval = null;
    let countdownSeconds = 5;
    let previousStatus = null;

    function playBeep() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
            osc.frequency.setValueAtTime(880, ctx.currentTime + 0.15); // A5
            gain.gain.setValueAtTime(0.2, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.5);
        } catch (e) {
            console.log('Audio notification unavailable:', e);
        }
    }

    async function fetchStatus() {
        if (!tokenId) return;

        const syncText = document.getElementById('sync-countdown');
        if (syncText) syncText.innerText = 'Syncing with database...';

        try {
            const response = await fetch(`/api/token/${tokenId}/status`);
            if (!response.ok) return;

            const data = await response.json();
            if (!data.success) return;

            updateTicketUI(data);

            // Check if status newly transitioned to Serving
            if (previousStatus === 'Waiting' && data.status === 'Serving') {
                playBeep();
                alert(`🔔 Counter Notification: Your Token ${data.token_number} is NOW BEING SERVED at ${data.service_name}! Please proceed to the counter.`);
            }
            previousStatus = data.status;

            // If terminal status reached, stop automatic polling
            if (data.status === 'Completed' || data.status === 'Cancelled') {
                clearInterval(pollInterval);
                clearInterval(countdownInterval);
                const syncBox = document.getElementById('ticket-sync-box');
                if (syncBox) {
                    syncBox.innerHTML = `<span style="color: #64748b; font-size: 0.82rem;">Token status is finalized (${data.status}).</span>`;
                }
            }
        } catch (err) {
            console.error('Error fetching live queue status:', err);
        } finally {
            countdownSeconds = 5;
        }
    }

    function updateTicketUI(data) {
        // 1. Status badge
        const badge = document.getElementById('ticket-status-badge');
        if (badge) {
            badge.innerText = data.status;
            badge.className = `badge badge-${data.status.toLowerCase()}`;
        }

        // 2. Metrics
        const posEl = document.getElementById('val-position');
        if (posEl) {
            if (data.status === 'Serving') {
                posEl.innerText = 'Serving Now';
                posEl.style.color = '#166534';
            } else if (data.status === 'Waiting') {
                posEl.innerText = data.position ? `#${data.position}` : '-';
                posEl.style.color = '#1e293b';
            } else {
                posEl.innerText = data.status;
            }
        }

        const aheadEl = document.getElementById('val-ahead');
        if (aheadEl) {
            aheadEl.innerText = data.people_ahead !== undefined ? `${data.people_ahead} person(s)` : '-';
        }

        const waitEl = document.getElementById('val-wait');
        if (waitEl) {
            waitEl.innerText = data.estimated_wait_text || '-';
        }

        const servingEl = document.getElementById('val-serving');
        if (servingEl) {
            servingEl.innerText = data.current_serving || 'None';
        }

        // 3. Update cancel button visibility
        const cancelForm = document.getElementById('cancel-token-form');
        if (cancelForm) {
            if (data.status === 'Completed' || data.status === 'Cancelled') {
                cancelForm.style.display = 'none';
            }
        }

        // 4. Update status alert banner if serving
        const servingAlert = document.getElementById('now-serving-alert');
        if (servingAlert) {
            if (data.status === 'Serving') {
                servingAlert.style.display = 'block';
            } else {
                servingAlert.style.display = 'none';
            }
        }
    }

    function startTimer() {
        countdownSeconds = 5;
        const countdownEl = document.getElementById('sync-countdown');

        if (countdownInterval) clearInterval(countdownInterval);
        countdownInterval = setInterval(() => {
            countdownSeconds--;
            if (countdownEl && countdownSeconds >= 0) {
                countdownEl.innerText = `Auto-refresh in ${countdownSeconds}s`;
            }
        }, 1000);

        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(fetchStatus, 5000);
    }

    // Initialize when page loads
    document.addEventListener('DOMContentLoaded', () => {
        const ticketEl = document.getElementById('ticket-container');
        if (!ticketEl) return;

        tokenId = ticketEl.getAttribute('data-token-id');
        const initialStatus = ticketEl.getAttribute('data-initial-status');
        previousStatus = initialStatus;

        if (tokenId && initialStatus !== 'Completed' && initialStatus !== 'Cancelled') {
            startTimer();

            const manualBtn = document.getElementById('btn-manual-sync');
            if (manualBtn) {
                manualBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    fetchStatus();
                });
            }
        }
    });
})();
