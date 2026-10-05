// QueueLess - Admin Live Queue Refresh Script

document.addEventListener('DOMContentLoaded', () => {
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    const refreshTimerSpan = document.getElementById('admin-refresh-timer');
    let timerSeconds = 10;
    let timerInterval = null;

    if (autoRefreshToggle) {
        // Retrieve stored preference or default to active
        const savedPref = localStorage.getItem('queueless_admin_autorefresh');
        if (savedPref !== null) {
            autoRefreshToggle.checked = (savedPref === 'true');
        }

        function runTimer() {
            if (!autoRefreshToggle.checked) {
                if (refreshTimerSpan) refreshTimerSpan.innerText = 'Auto-refresh paused';
                if (timerInterval) clearInterval(timerInterval);
                return;
            }

            timerSeconds = 10;
            if (timerInterval) clearInterval(timerInterval);

            timerInterval = setInterval(() => {
                if (!autoRefreshToggle.checked) {
                    clearInterval(timerInterval);
                    return;
                }
                timerSeconds--;
                if (refreshTimerSpan) {
                    refreshTimerSpan.innerText = `Refreshing in ${timerSeconds}s`;
                }

                if (timerSeconds <= 0) {
                    clearInterval(timerInterval);
                    window.location.reload();
                }
            }, 1000);
        }

        autoRefreshToggle.addEventListener('change', () => {
            localStorage.setItem('queueless_admin_autorefresh', autoRefreshToggle.checked);
            runTimer();
        });

        runTimer();
    }
});
