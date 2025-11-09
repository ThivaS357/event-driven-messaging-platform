document.addEventListener('DOMContentLoaded', function() {
    // Load initial data when the page is ready
    loadTemplates();
    loadSegments();
    loadInbound();
    loadStats();
});

const API_BASE_URL = '/api/v1';

/**
 * Helper function to display results in a <pre> tag.
 * @param {string} elementId - The ID of the <pre> element.
 * @param {object} data - The JSON data to display.
 * @param {boolean} isError - Whether the data represents an error.
 */
function showResult(elementId, data, isError = false) {
    const el = document.getElementById(elementId);
    el.textContent = JSON.stringify(data, null, 2);
    el.className = isError 
        ? 'text-xs mt-2 bg-red-50 p-2 rounded text-red-700' 
        : 'text-xs mt-2 bg-gray-50 p-2 rounded';
}

async function uploadUsers() {
    const fileInput = document.getElementById('userFile');
    if (fileInput.files.length === 0) {
        showResult('uploadResult', { error: 'Please select a file.' }, true);
        return;
    }
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch(`${API_BASE_URL}/ingestions/users`, {
            method: 'POST',
            body: formData,
        });
        const result = await response.json();
        showResult('uploadResult', result, !response.ok);
    } catch (error) {
        showResult('uploadResult', { error: error.message }, true);
    }
}

async function uploadEvents() {
    const fileInput = document.getElementById('jsonlFile');
    if (fileInput.files.length === 0) {
        showResult('eventResult', { error: 'Please select a file.' }, true);
        return;
    }
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch(`${API_BASE_URL}/ingestions/events`, {
            method: 'POST',
            body: formData,
        });
        const result = await response.json();
        showResult('eventResult', result, !response.ok);
    } catch (error) {
        showResult('eventResult', { error: error.message }, true);
    }
}

async function createTemplate() {
    const name = document.getElementById('templateName').value;
    const content = document.getElementById('templateContent').value;

    if (!name || !content) {
        showResult('templateResult', { error: 'Template name and content are required.' }, true);
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/templates/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ _id: name, content: content }),
        });
        const result = await response.json();
        showResult('templateResult', result, !response.ok);
        if (response.ok) loadTemplates(); // Refresh dropdown
    } catch (error) {
        showResult('templateResult', { error: error.message }, true);
    }
}

async function createSegment() {
    const name = document.getElementById('segmentName').value;
    const topic = document.getElementById('segmentTopic').value;
    const ruleStr = document.getElementById('segmentRule').value;

    if (!name || !topic || !ruleStr) {
        showResult('segmentResult', { error: 'Segment name, topic, and rule are required.' }, true);
        return;
    }

    try {
        const rule = JSON.parse(ruleStr);
        const response = await fetch(`${API_BASE_URL}/segments/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ _id: name, topic: topic, rule: rule }),
        });
        const result = await response.json();
        showResult('segmentResult', result, !response.ok);
        if (response.ok) loadSegments(); // Refresh dropdown
    } catch (error) {
        showResult('segmentResult', { error: 'Invalid JSON in rule or network error: ' + error.message }, true);
    }
}

async function createCampaign() {
    const campaignName = document.getElementById('campaignName').value;
    const templateId = document.getElementById('templateSelect').value;
    const segmentId = document.getElementById('segmentSelect').value;
    const topic = document.getElementById('topic').value;

    if (!campaignName || !templateId || !segmentId || !topic) {
        showResult('campaignResult', { error: 'All fields are required to create a campaign.' }, true);
        return;
    }

    const payload = {
        _id: campaignName,
        template_id: templateId,
        segment_id: segmentId,
        topic: topic,
    };

    try {
        const response = await fetch(`${API_BASE_URL}/campaigns/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const result = await response.json();
        showResult('campaignResult', result, !response.ok);
    } catch (error) {
        showResult('campaignResult', { error: error.message }, true);
    }
}

async function runCampaign() {
    const campaignId = document.getElementById('campaignId').value;
    if (!campaignId) {
        showResult('runResult', { error: 'Campaign ID is required.' }, true);
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/orchestration/run/${campaignId}`, {
            method: 'POST',
        });
        const result = await response.json();
        showResult('runResult', result, !response.ok);
    } catch (error) {
        showResult('runResult', { error: error.message }, true);
    }
}

async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE_URL}/templates/`);
        const templates = await response.json();
        const select = document.getElementById('templateSelect');
        select.innerHTML = '<option value="">-- Select a Template --</option>';
        templates.forEach(t => {
            select.innerHTML += `<option value="${t._id}">${t.content}</option>`;
        });
    } catch (error) {
        console.error('Failed to load templates:', error);
    }
}

async function loadSegments() {
    try {
        const response = await fetch(`${API_BASE_URL}/segments/`);
        const segments = await response.json();
        const select = document.getElementById('segmentSelect');
        select.innerHTML = '<option value="">-- Select a Segment --</option>';
        segments.forEach(s => {
            select.innerHTML += `<option value="${s._id}">${s.name}</option>`;
        });
    } catch (error) {
        console.error('Failed to load segments:', error);
    }
}

async function loadInbound() {
    // This is a placeholder. You would need an API endpoint to fetch inbound messages.
    const list = document.getElementById('inboundList');
    list.innerHTML = '<li>Inbound message loading requires a dedicated API endpoint.</li>';
}

async function loadStats() {
    // This is a placeholder. You would need an API endpoint to fetch stats.
    const statsBox = document.getElementById('statsBox');
    statsBox.innerHTML = '<p>Stats loading requires a dedicated API endpoint.</p>';
}