const REPO_OWNER = "sudhir-bahadure";
const REPO_NAME = "tube-automa";

// UI Elements
const authBtn = document.getElementById('auth-btn');
const authModal = document.getElementById('auth-modal');
const ghTokenInput = document.getElementById('gh-token');
const logsContainer = document.getElementById('logs-container');

// Check for token on load
let GITHUB_TOKEN = localStorage.getItem('gh_token');
if (GITHUB_TOKEN) {
    authBtn.innerText = "GitHub Linked ✅";
    addLog("System ready. Token detected.");
}

function addLog(message) {
    const time = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = "log-entry";
    entry.innerText = `[${time}] ${message}`;
    logsContainer.prepend(entry);
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
        closeModal();
    }
}

// Workflow Logic
async function triggerWorkflow(workflowId) {
    if (!GITHUB_TOKEN) {
        addLog("ERROR: Please link your GitHub token first.");
        authModal.classList.remove('hidden');
        return;
    }

    const tweak = document.getElementById('prompt-tweak').value.trim();
    addLog(`Initiating trigger: ${workflowId}${tweak ? ' with tweak: "' + tweak + '"' : ''}...`);

    try {
        const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${workflowId}/dispatches`, {
            method: 'POST',
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`,
                'Accept': 'application/vnd.github.v3+json',
            },
            body: JSON.stringify({
                ref: 'main',
                inputs: {
                    prompt_tweak: tweak
                }
            })
        });

        if (response.status === 204) {
            addLog(`SUCCESS: ${workflowId} dispatched! Check your Actions tab.`);
            // Clear tweak after successful trigger
            document.getElementById('prompt-tweak').value = '';
        } else {
            const error = await response.json();
            addLog(`FAILURE: ${error.message}`);
        }
    } catch (e) {
        addLog(`NETWORK ERROR: ${e.message}`);
    }
}

// Sample dynamic telemetry (just for visual flair)
setInterval(() => {
    const bars = document.querySelectorAll('.bar');
    bars.forEach(bar => {
        const height = Math.floor(Math.random() * 80) + 20;
        bar.style.height = height + '%';
    });
}, 3000);
