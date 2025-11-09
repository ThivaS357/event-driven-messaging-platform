// -----------------------------
// Helper: Safe JSON Fetch
// -----------------------------
async function fetchJSON(url, opts = {}) {
    const res = await fetch(url, opts);
    return res.json();
  }
  
  // -----------------------------
  // Upload Users
  // -----------------------------
  async function uploadUsers() {
    const file = document.getElementById("userFile").files[0];
    if (!file) return alert("Select a file first!");
    const formData = new FormData();
    formData.append("file", file);
  
    const res = await fetch(`/ingestions/users`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    document.getElementById("uploadResult").textContent = JSON.stringify(data, null, 2);
  }
  
  // -----------------------------
  // Upload JSONL Events
  // -----------------------------
  async function uploadEvents() {
    const file = document.getElementById("jsonlFile").files[0];
    if (!file) return alert("Select a JSONL file!");
    const formData = new FormData();
    formData.append("file", file);
  
    const res = await fetch(`/ingestions/events`, { method: "POST", body: formData });
    const data = await res.json();
    document.getElementById("eventResult").textContent = JSON.stringify(data, null, 2);
  }
  
  // -----------------------------
  // Template CRUD
  // -----------------------------
  async function createTemplate() {
    const body = {
      name: document.getElementById("templateName").value,
      content: document.getElementById("templateContent").value
    };
    const res = await fetch("/api/v1/templates/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    document.getElementById("templateResult").textContent = JSON.stringify(data, null, 2);
    loadTemplates();
  }
  
  async function loadTemplates() {
    const res = await fetch("/api/v1/templates/");
    const data = await res.json();
    const sel = document.getElementById("templateSelect");
    sel.innerHTML = "";
    data.forEach(t => {
      const opt = document.createElement("option");
      opt.value = t._id;
      opt.textContent = t.name;
      sel.appendChild(opt);
    });
  }
  
  // -----------------------------
  // Segment CRUD
  // -----------------------------
  async function createSegment() {
    const body = {
      name: document.getElementById("segmentName").value,
      topic: document.getElementById("segmentTopic").value,
      rule: JSON.parse(document.getElementById("segmentRule").value || "{}")
    };
    const res = await fetch("/api/v1/segments/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    document.getElementById("segmentResult").textContent = JSON.stringify(data, null, 2);
    loadSegments();
  }
  
  async function loadSegments() {
    const res = await fetch("/api/v1/segments/");
    const data = await res.json();
    const sel = document.getElementById("segmentSelect");
    sel.innerHTML = "";
    data.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s._id;
      opt.textContent = s.name;
      sel.appendChild(opt);
    });
  }
  
  // -----------------------------
  // Campaign CRUD + Run
  // -----------------------------
  async function createCampaign() {
    const body = {
      name: document.getElementById("campaignName").value,
      topic: document.getElementById("topic").value,
      template_id: document.getElementById("templateSelect").value,
      segment_id: document.getElementById("segmentSelect").value,
      status: "scheduled"
    };
  
    const res = await fetch("/api/v1/campaigns/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    document.getElementById("campaignResult").textContent = JSON.stringify(data, null, 2);
  }
  
  async function runCampaign() {
    const id = document.getElementById("campaignId").value.trim();
    if (!id) return alert("Enter campaign ID!");
    const res = await fetch(`/api/v1/campaigns/run/${id}`, { method: "POST" });
    const data = await res.json();
    document.getElementById("runResult").textContent = JSON.stringify(data, null, 2);
  }
  
  // -----------------------------
  // Inbound Messages
  // -----------------------------
  async function loadInbound() {
    const res = await fetch("/api/v1/events/inbound");
    const data = await res.json();
    const list = document.getElementById("inboundList");
    list.innerHTML = "";
    data.forEach(ev => {
      const li = document.createElement("li");
      li.textContent = `${ev.from}: ${ev.body || ""} (${ev.command || ""})`;
      list.appendChild(li);
    });
  }
  
  // -----------------------------
  // Stats Dashboard
  // -----------------------------
  let chart;
  async function loadStats() {
    const stats = await fetchJSON("/api/v1/ingestions/stats");
  
    document.getElementById("statUsers").textContent = stats.total_users;
    document.getElementById("statOptouts").textContent = stats.opt_outs;
    document.getElementById("statSent").textContent = stats.sent;
    document.getElementById("statFailed").textContent = stats.failed;
    document.getElementById("statDelivery").textContent = stats.delivery_pct;
    document.getElementById("statFailRate").textContent = stats.failed_pct;
  
    const ctx = document.getElementById("statsChart");
    const data = {
      labels: ["Delivered %", "Failed %", "Opt-outs"],
      datasets: [{
        data: [
          stats.delivery_pct,
          stats.failed_pct,
          (stats.opt_outs / stats.total_users * 100) || 0
        ],
        backgroundColor: ["#22c55e", "#ef4444", "#f59e0b"]
      }]
    };
    if (chart) chart.destroy();
    chart = new Chart(ctx, { type: "pie", data });
  }
  
  // -----------------------------
  // Page Load Initialization
  // -----------------------------
  window.addEventListener("load", () => {
    if (document.getElementById("templateSelect")) loadTemplates();
    if (document.getElementById("segmentSelect")) loadSegments();
  });
  