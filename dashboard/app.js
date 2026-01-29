// SaaS Pro State Management
const REPO_OWNER = "sudhir-bahadure";
const REPO_NAME = "tube-automa";
let CURRENT_STEP = parseInt(localStorage.getItem('onboarding_step')) || 1;
const TOTAL_STEPS = 4;

// UI Elements
const authBtn = document.getElementById('auth-btn');
const authModal = document.getElementById('auth-modal');
const ghTokenInput = document.getElementById('gh-token');
const logsContainer = document.getElementById('logs-container');
const progressPill = document.getElementById('setup-progress-pill');

// Tab Switching
document.querySelectorAll('.nav-links button').forEach(btn => {
    btn.onclick = () => {
        const tab = btn.dataset.tab;
        switchTab(tab);
        document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
        btn.parentElement.classList.add('active');
    };
});

function switchTab(tabId) {
    const views = ['view-setup', 'telemetry-grid', 'command-grid', 'strategy-center'];
    views.forEach(v => {
        const el = document.getElementById(v);
        if (el) el.style.display = 'none';
    });

    document.getElementById('page-title').innerText = tabId.charAt(0).toUpperCase() + tabId.slice(1);

    if (tabId === 'setup') {
        document.getElementById('view-setup').style.display = 'block';
    } else {
        // Show components of the dashboard for other tabs
        document.querySelector('.telemetry-grid').style.display = 'grid';
        document.querySelector('.command-grid').style.display = 'grid';
    }
}

// Check for token on load
let GITHUB_TOKEN = localStorage.getItem('gh_token');
if (GITHUB_TOKEN) {
    authBtn.innerText = "Identity Verified ✅";
    addLog("Dashboard synchronized. Monitoring active.");
    if (CURRENT_STEP === 1) updateStep(2);
    refreshData();
}

function updateStep(step) {
    CURRENT_STEP = step;
    localStorage.setItem('onboarding_step', step);
    progressPill.innerText = `Setup: ${step}/4 Complete`;
    updateWizardUI();
}

function updateWizardUI() {
    document.querySelectorAll('.step').forEach(el => {
        const s = parseInt(el.dataset.step);
        el.className = 'step';
        if (s === CURRENT_STEP) el.classList.add('active');
        if (s < CURRENT_STEP) el.classList.add('completed');
    });
}

function addLog(message) {
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = "log-entry";
    entry.innerText = `[${time}] ${message}`;
    logsContainer.prepend(entry);
    // Keep only last 50 logs
    if (logsContainer.children.length > 50) logsContainer.lastChild.remove();
}

// Refresh all telemetry
async function refreshData() {
    if (!GITHUB_TOKEN) return;

    await fetchWorkflowStatuses();
    await fetchUsageMetrics();
}

async function fetchWorkflowStatuses() {
    const workflows = ['daily_meme.yml', 'daily_curiosity.yml', 'daily_long.yml'];
    let totalRuns = 0;
    let successRuns = 0;
    let mostRecentRun = null;

    for (const wfId of workflows) {
        try {
            const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${wfId}/runs?per_page=1`, {
                headers: { 'Authorization': `token ${GITHUB_TOKEN}` }
            });
            const data = await response.json();

            if (data.workflow_runs && data.workflow_runs.length > 0) {
                const run = data.workflow_runs[0];
                updateWorkflowUI(wfId, run);

                totalRuns++;
                if (run.conclusion === 'success') successRuns++;

                const runDate = new Date(run.created_at);
                if (!mostRecentRun || runDate > mostRecentRun) mostRecentRun = runDate;
            }
        } catch (e) {
            console.error(`Status error for ${wfId}:`, e);
        }
    }

    // Update global telemetry
    if (totalRuns > 0) {
        document.getElementById('runs-count').innerText = totalRuns; // This is a simplified display
        document.getElementById('success-rate').innerText = Math.round((successRuns / totalRuns) * 100);
        if (mostRecentRun) {
            document.getElementById('last-run-time').innerText = `Last Activity: ${mostRecentRun.toLocaleString()}`;
        }
    }
}

function updateWorkflowUI(wfId, run) {
    const card = document.getElementById(`workflow-${wfId}`);
    if (!card) return;

    const indicator = card.querySelector('.status-indicator-mini');
    const statusText = card.querySelector('.wf-status');

    // Reset classes
    indicator.className = 'status-indicator-mini';

    if (run.status === 'in_progress' || run.status === 'queued') {
        indicator.classList.add('in_progress');
        indicator.title = "Status: Running...";
        statusText.innerText = `Running now...`;
    } else {
        indicator.classList.add(run.conclusion || 'unknown');
        indicator.title = `Status: ${run.conclusion}`;
        const dateStr = new Date(run.created_at).toLocaleDateString();
        statusText.innerText = `Last: ${dateStr} (${run.conclusion})`;
    }
}

async function fetchUsageMetrics() {
    try {
        // Since personal billing API is restricted, we'll use repo usage as a proxy or 
        // fallback to a calculated estimate based on recent runs.
        const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/runs?status=completed&per_page=100`, {
            headers: { 'Authorization': `token ${GITHUB_TOKEN}` }
        });
        const data = await response.json();

        let totalMs = 0;
        if (data.workflow_runs) {
            data.workflow_runs.forEach(run => {
                const updated = new Date(run.updated_at);
                const created = new Date(run.created_at);
                totalMs += (updated - created);
            });
        }

        const usedMinutes = Math.round(totalMs / 60000);
        const freeLimit = 2000;

        document.getElementById('used-minutes').innerText = usedMinutes;
        document.getElementById('total-minutes').innerText = freeLimit;

        const percent = Math.min((usedMinutes / freeLimit) * 100, 100);
        document.getElementById('usage-bar').style.width = percent + '%';

        const remaining = freeLimit - usedMinutes;
        const tag = document.getElementById('remaining-minutes-tag');
        tag.innerText = `${remaining} mins free left`;

        if (percent > 80) tag.className = 'pill error';
        else if (percent > 50) tag.className = 'pill warning';
        else tag.className = 'pill success';

        updateRecommendations(usedMinutes);

    } catch (e) {
        console.error("Usage fetch error:", e);
    }
}

function applyTweak(text) {
    const input = document.getElementById('prompt-tweak');
    input.value = text;
    input.scrollIntoView({ behavior: 'smooth' });
    input.classList.add('pulse-highlight');
    setTimeout(() => input.classList.remove('pulse-highlight'), 1000);
    addLog(`Protocol updated: "${text}" applied to buffer.`);
}

function updateRecommendations(usedMinutes, wfData) {
    const list = document.getElementById('recommendations-list');
    list.innerHTML = '';

    const recs = [];

    // Usage-based
    if (usedMinutes > 1500) {
        recs.push({ title: "Minutes Critical", text: "Usage at 75%. Switch to every 3 days to stay free." });
    } else {
        recs.push({ title: "Resource Status", text: "Healthy quota. Safe to run daily documentary." });
    }

    // Performance-based with Action Buttons
    recs.push({
        title: "Virality Boost",
        text: "Curiosity is trending. Apply 'Space Explorations' upgrade.",
        tweak: "Focus on mysterious space discoveries and deep-sea mysteries"
    });

    recs.push({
        title: "Humor Engine",
        text: "Memes need fresh energy. Apply 'Gen-Z Satire' tweak.",
        tweak: "Use heavy Gen-Z slang and fast-paced surrealist humor"
    });

    recs.forEach(rec => {
        const div = document.createElement('div');
        div.className = 'rec-card';
        let actionBtn = rec.tweak ? `<button onclick="applyTweak('${rec.tweak}')" class="btn-mini">Apply Tweak</button>` : '';
        div.innerHTML = `
            <div>
                <small>${rec.title}</small>
                <p>${rec.text}</p>
            </div>
            ${actionBtn}
        `;
        list.appendChild(div);
    });
}

// Auth Logic
authBtn.onclick = () => {
    authModal.classList.remove('hidden');
};

function closeModal() {
    authModal.classList.add('hidden');
}

function saveToken() {
    const token = ghTokenInput.value.trim();
    if (token) {
        localStorage.setItem('gh_token', token);
        GITHUB_TOKEN = token;
        authBtn.innerText = "GitHub Linked ✅";
        addLog("Identity Guard: Token saved successfully.");
        refreshData();
        closeModal();
    }
}

// Workflow Triggering
async function triggerWorkflow(workflowId) {
    if (!GITHUB_TOKEN) {
        addLog("ERROR: Please link your GitHub token first.");
        authModal.classList.remove('hidden');
        return;
    }

    const tweak = document.getElementById('prompt-tweak').value.trim();
    addLog(`Command: Triggering ${workflowId}...`);

    try {
        const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${workflowId}/dispatches`, {
            method: 'POST',
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github.v3+json',
            },
            body: JSON.stringify({
                ref: 'main',
                inputs: { prompt_tweak: tweak }
            })
        });

        if (response.status === 204) {
            addLog(`SUCCESS: Protocol initiated. Initializing...`);
            document.getElementById('prompt-tweak').value = '';
            // Refresh quickly after trigger
            setTimeout(refreshData, 3000);
        } else {
            const error = await response.json();
            addLog(`FAILURE: ${error.message}`);
        }
    } catch (e) {
        addLog(`ERROR: ${e.message}`);
    }
}

// Wizard Navigation Loop
const nextStepBtn = document.getElementById('next-step-btn');
if (nextStepBtn) {
    nextStepBtn.onclick = () => {
        if (CURRENT_STEP < TOTAL_STEPS) {
            const next = CURRENT_STEP + 1;
            showPanel(next);
            updateStep(next);
        } else {
            switchTab('dashboard');
        }
    };
}

function showPanel(stepIdx) {
    document.querySelectorAll('.step-panel').forEach(p => p.classList.add('hidden'));
    const target = document.getElementById(`step-${stepIdx}-panel`);
    if (target) {
        target.classList.remove('hidden');
        target.classList.add('fadeIn');
    }

    // Step-Specific Logic
    if (stepIdx === 2) {
        nextStepBtn.disabled = false;
        nextStepBtn.innerText = "Next: Channel Setup";
    } else if (stepIdx === 3) {
        nextStepBtn.innerText = "Next: API Access";
    } else if (stepIdx === 4) {
        nextStepBtn.innerText = "Launch Automation 🚀";
    }
}

function selectNiche(name) {
    document.querySelectorAll('.niche-card').forEach(c => c.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    addLog(`Strategy Selected: ${name} Niche identified for monetization.`);
    localStorage.setItem('user_niche', name);
}

// Initial Wizard State
if (CURRENT_STEP > 1) {
    showPanel(CURRENT_STEP);
}

// Polling Loop (Refresh every 60s)
setInterval(refreshData, 60000);

// Visual flair
setInterval(() => {
    const bars = document.querySelectorAll('.bar');
    bars.forEach(bar => {
        const height = Math.floor(Math.random() * 80) + 20;
        bar.style.height = height + '%';
    });
}, 3000);
