// TubeAutoma Pro: Auth & License Engine
let IS_AUTHENTICATED = localStorage.getItem('is_authenticated') === 'true';
let IS_ACTIVATED = localStorage.getItem('is_activated') === 'true';

// Mock DB for License Keys
const VALID_KEYS = ["PRO-X782-K921", "TUBE-SaaS-2026", "GIFT-7788-PRO"];

document.addEventListener('DOMContentLoaded', () => {
    checkInitialState();
});

function checkInitialState() {
    if (IS_AUTHENTICATED) {
        document.getElementById('auth-gate').classList.add('hidden');
        document.getElementById('app-main').classList.remove('hidden');
        document.body.classList.remove('auth-required');

        if (!IS_ACTIVATED) {
            updateStep(0); // Force to License phase
        } else {
            // If already activated, jump to dashboard if onboarding is done
            const savedStep = parseInt(localStorage.getItem('onboarding_step'));
            if (savedStep >= 4) {
                switchTab('dashboard');
            } else {
                updateStep(savedStep || 1);
            }
        }
    }
}

function mockLogin() {
    // Simple mock login for SaaS MVP
    const email = document.querySelector('#login-form input[type="email"]').value;
    const pass = document.querySelector('#login-form input[type="password"]').value;

    if (email && pass) {
        localStorage.setItem('is_authenticated', 'true');
        IS_AUTHENTICATED = true;

        addLog(`Identity Confirmed: Welcome ${email}`);

        // Visual transition
        document.getElementById('auth-gate').style.opacity = '0';
        setTimeout(() => {
            document.getElementById('auth-gate').classList.add('hidden');
            document.getElementById('app-main').classList.remove('hidden');
            document.body.classList.remove('auth-required');
            checkInitialState();
        }, 500);
    }
}

function activateLicense() {
    const key = document.getElementById('license-key').value.trim().toUpperCase();

    if (VALID_KEYS.includes(key)) {
        localStorage.setItem('is_activated', 'true');
        IS_ACTIVATED = true;

        addLog("PROTOCOL UNLOCKED: Premium License Verified.");

        // Move to Step 1 (Deployment)
        updateStep(1);
        showPanel(1);
    } else {
        alert("Invalid License Key. Please purchase a key from your SaaS provider.");
    }
}

function toggleAuth() {
    // Simply swap text for the SaaS demo
    const title = document.querySelector('.auth-card h2');
    const footer = document.querySelector('.auth-footer');

    if (title.innerText.includes("Awaits")) {
        title.innerText = "Become a Media Mughal";
        footer.innerHTML = 'Already a member? <a href="#" onclick="toggleAuth()">Sign In</a>';
    } else {
        title.innerText = "Quantum Automation Awaits";
        footer.innerHTML = 'New Creator? <a href="#" onclick="toggleAuth()">Start Free Trial</a>';
    }
}
