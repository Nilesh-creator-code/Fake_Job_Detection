const appFrame = document.querySelector(".app-frame");
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebar-toggle");
const navItems = Array.from(document.querySelectorAll(".nav-item"));
const form = document.getElementById("analyze-form");
const analyzeButton = document.getElementById("analyze-button");
const statusEl = document.getElementById("status");
const downloadButton = document.getElementById("download-report");
const scanAnotherButton = document.getElementById("scan-another");
const quickDemoButton = document.getElementById("quick-demo");
const timeline = document.getElementById("timeline");
const alertFeed = document.getElementById("alert-feed");
const dropZone = document.getElementById("drop-zone");
const fileUpload = document.getElementById("file-upload");
const reportModal = document.getElementById("report-modal");
const closeModal = document.getElementById("close-modal");
const cancelDownload = document.getElementById("cancel-download");
const confirmDownload = document.getElementById("confirm-download");

const scanHistory = [];
let latestResult = null;
let uploadedContext = "";

const demoUrls = [
  "https://example.com/jobs/remote-data-entry-intern",
  "https://example.com/careers/frontend-engineer",
  "https://example.com/listing/urgent-remote-assistant",
];

const riskRingCenterText = {
  id: "riskRingCenterText",
  afterDraw(chart) {
    const { ctx, chartArea } = chart;
    if (!chartArea) return;
    ctx.save();
    ctx.font = "700 30px Inter";
    ctx.fillStyle = "#ebf2ff";
    ctx.textAlign = "center";
    ctx.fillText("", chart.width / 2, chart.height / 2);
    ctx.restore();
  },
};

Chart.register(riskRingCenterText);

const riskRingChart = new Chart(document.getElementById("riskRingChart"), {
  type: "doughnut",
  data: {
    datasets: [
      {
        data: [0, 100],
        backgroundColor: ["#53a2ff", "rgba(255,255,255,0.08)"],
        borderWidth: 0,
        hoverOffset: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    cutout: "78%",
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
  },
});

const probabilityTrendChart = new Chart(document.getElementById("probabilityTrendChart"), {
  type: "line",
  data: {
    labels: ["-6", "-5", "-4", "-3", "-2", "-1", "Now"],
    datasets: [
      {
        data: [12, 20, 18, 36, 42, 37, 24],
        borderColor: "#8d5dff",
        backgroundColor: "rgba(141,93,255,0.18)",
        fill: true,
        tension: 0.42,
        pointRadius: 0,
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    scales: {
      x: { display: false },
      y: { display: false, min: 0, max: 100 },
    },
  },
});

const signalChart = new Chart(document.getElementById("signalChart"), {
  type: "bar",
  data: {
    labels: ["Rules", "Red Flags", "Trust", "Domain", "Language", "Recruiter"],
    datasets: [
      {
        label: "Signal Strength",
        data: [0, 0, 0, 0, 0, 0],
        borderRadius: 10,
        backgroundColor: ["#53a2ff", "#ff697d", "#2fe39b", "#8d5dff", "#50e6ff", "#ffb84d"],
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: {
        ticks: { color: "#90a5c7", font: { size: 11 } },
        grid: { display: false },
      },
      y: {
        ticks: { color: "#90a5c7", font: { size: 11 } },
        grid: { color: "rgba(170,198,255,0.08)" },
        suggestedMax: 100,
      },
    },
  },
});

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function animateNumber(id, target, suffix = "") {
  const el = document.getElementById(id);
  const start = Number.parseFloat(el.dataset.value || "0");
  const end = Number.parseFloat(target) || 0;
  const startTime = performance.now();
  const duration = 700;

  function step(now) {
    const progress = Math.min(1, (now - startTime) / duration);
    const value = start + (end - start) * (1 - Math.pow(1 - progress, 3));
    el.textContent = `${Math.round(value)}${suffix}`;
    el.dataset.value = `${value}`;
    if (progress < 1) {
      requestAnimationFrame(step);
    }
  }

  requestAnimationFrame(step);
}

function setList(id, items, emptyLabel = "None") {
  const target = document.getElementById(id);
  target.innerHTML = "";
  (items && items.length ? items : [emptyLabel]).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    target.appendChild(li);
  });
}

function formatPattern(value) {
  return value ? value.replaceAll("_", " ") : "-";
}

function updateRiskChip(level) {
  const el = document.getElementById("risk-meter");
  const key = (level || "").toLowerCase();
  el.className = `risk-chip ${key || "neutral"}`;
  el.textContent = level || "Pending";
}

function updateRing(score) {
  const bounded = Math.max(0, Math.min(100, score));
  riskRingChart.data.datasets[0].data = [bounded, 100 - bounded];
  riskRingChart.data.datasets[0].backgroundColor = [
    bounded >= 75 ? "#ff697d" : bounded >= 50 ? "#ffb84d" : bounded >= 25 ? "#53a2ff" : "#2fe39b",
    "rgba(255,255,255,0.08)",
  ];
  riskRingChart.update();
}

function updateTrendChart(probability) {
  const base = probability;
  const series = [
    Math.max(5, base - 26),
    Math.max(8, base - 18),
    Math.max(10, base - 24),
    Math.max(12, base - 10),
    Math.max(16, base - 4),
    Math.max(14, base - 8),
    base,
  ];
  probabilityTrendChart.data.datasets[0].data = series;
  probabilityTrendChart.update();
}

function updateSignalChart(data) {
  const features = data.features;
  const redFlagCount = data.explanation.red_flags.length;
  const trustCount = data.explanation.trust_signals.length;
  signalChart.data.datasets[0].data = [
    data.rule_score,
    redFlagCount * 12,
    trustCount * 10,
    (features.brand_mismatch + features.suspicious_tld + features.spoofed_email_count) * 18,
    Math.round(features.grammar_error_ratio * 100),
    (features.free_email_count + features.spoofed_email_count) * 16,
  ];
  signalChart.update();
}

function inferJobType(posting) {
  const text = `${posting.title} ${posting.job_description}`.toLowerCase();
  if (text.includes("intern")) return "Internship";
  if (text.includes("remote")) return "Remote";
  if (text.includes("contract")) return "Contract";
  return "Full-time / Listed role";
}

function inferExperience(posting) {
  const text = posting.job_description.toLowerCase();
  if (text.includes("no experience")) return "No experience listed";
  if (text.includes("entry level")) return "Entry level";
  if (text.includes("senior")) return "Senior";
  return "Not clearly stated";
}

function languageQuality(features) {
  if (features.grammar_error_ratio >= 0.5) return "Poor";
  if (features.grammar_error_ratio >= 0.2) return "Mixed";
  return "Good";
}

function updateHeatmap(data) {
  const heatmap = document.getElementById("pattern-heatmap");
  const items = [
    ["Advance Fee Scam", data.features.upfront_payment_count * 20],
    ["Phishing Recruitment", data.features.brand_mismatch * 30 + data.features.spoofed_email_count * 18],
    ["Remote Scam Pattern", data.features.remote_scam_count * 14],
    ["Internship Exploitation", data.features.internship_exploitation_count * 18],
    ["Generic Fraud Signals", Math.round(data.features.genericity_score * 100)],
    ["Urgency Pressure", data.features.urgency_count * 16],
  ];
  heatmap.innerHTML = "";
  items.forEach(([label, value]) => {
    const cell = document.createElement("div");
    cell.className = "heatmap-cell";
    cell.innerHTML = `
      <strong>${label}</strong>
      <div class="heatmap-bar"><span style="width:${Math.min(100, value)}%"></span></div>
      <small>${Math.round(value)}/100 signal strength</small>
    `;
    heatmap.appendChild(cell);
  });
}

function renderTimeline() {
  timeline.innerHTML = "";
  if (!scanHistory.length) {
    timeline.innerHTML = `<div class="timeline-empty">No scans yet.</div>`;
    return;
  }

  scanHistory
    .slice()
    .reverse()
    .forEach((entry) => {
      const item = document.createElement("div");
      item.className = "timeline-item";
      item.innerHTML = `
        <strong>${entry.title}</strong>
        <p>${entry.company} · ${entry.level} · ${entry.score}</p>
        <small>${entry.time}</small>
      `;
      timeline.appendChild(item);
    });
}

function updateAlertFeed(data) {
  const alerts = [
    data.explanation.red_flags[0] || "No immediate red flags.",
    data.explanation.triggered_rules[0] || "No rule match triggered.",
    data.explanation.model_reasoning[0] || "Model reasoning will appear after a scan.",
  ];
  alertFeed.innerHTML = "";
  alerts.forEach((alert, index) => {
    const item = document.createElement("div");
    item.className = "alert-item";
    item.innerHTML = `
      <span class="alert-dot" style="background:${index === 0 ? "#ff697d" : index === 1 ? "#ffb84d" : "#50e6ff"}"></span>
      <div>
        <strong>${index === 0 ? "Primary signal" : index === 1 ? "Rule trigger" : "Model insight"}</strong>
        <p>${alert}</p>
      </div>
    `;
    alertFeed.appendChild(item);
  });
  setText("alerts-count", `${alerts.length}`);
}

function recordHistory(data) {
  scanHistory.push({
    title: data.posting.title || "Unknown role",
    company: data.posting.company_name || "Unknown company",
    score: `${data.overall_risk_score.toFixed(0)}/100`,
    level: data.risk_meter,
    result: data.model_prediction.label,
    time: new Date().toLocaleString(),
  });
  if (scanHistory.length > 8) scanHistory.shift();
  renderTimeline();
}

function setLoading(loading) {
  analyzeButton.classList.toggle("is-loading", loading);
  analyzeButton.disabled = loading;
  form.classList.toggle("skeleton", loading);
}

function populateDashboard(data) {
  latestResult = data;
  const posting = data.posting;
  const features = data.features;
  const fakeProbability = data.fake_percentage;
  const trustCount = data.explanation.trust_signals.length;
  const redFlagCount = data.explanation.red_flags.length;

  animateNumber("risk-score", data.overall_risk_score);
  animateNumber("risk-center", data.overall_risk_score);
  animateNumber("fake-percentage", fakeProbability, "%");
  setText("risk-label", `${data.risk_meter} risk`);
  setText("confidence", `Confidence: ${data.confidence_score.toFixed(0)}%`);
  setText("classification", data.model_prediction.label);
  setText("recommendation", data.explanation.recommendation);
  setText("fraud-category", `Pattern: ${formatPattern(data.model_prediction.category)}`);
  setText("summary-text", data.explanation.summary);
  setText("job-title", posting.title || "-");
  setText("company-name", posting.company_name || "-");
  setText("domain", posting.domain_info.root_domain || "-");
  setText("salary", posting.salary_text || "Not stated");
  setText("job-type", inferJobType(posting));
  setText("experience", inferExperience(posting));
  setText("source-url", posting.source_url || "-");
  setText("recruiter-email", posting.recruiter_details.emails[0] || posting.contact_details.emails[0] || "Not found");
  setText("application-link", posting.application_links[0] || "No link captured");
  setText("description-length", `${posting.job_description.length} chars`);
  setText("language-quality", languageQuality(features));
  setText("requirements-flag", features.missing_requirements ? "Weak / missing" : "Present");
  setText("report-risk-score", `${data.overall_risk_score.toFixed(0)}/100`);
  setText("report-fake", `${fakeProbability.toFixed(0)}%`);
  setText("report-level", data.risk_meter);
  setText("report-recommendation", data.explanation.recommendation);
  setText("report-pattern", formatPattern(data.model_prediction.category));
  setText("report-timestamp", new Date().toLocaleString());
  setText("trust-score", `${trustCount}`);
  setText("flag-score", `${redFlagCount}`);
  setText("red-flag-badge", `${redFlagCount}`);
  setText("trust-badge", `${trustCount}`);
  setText("risk-trend", fakeProbability >= 70 ? "Escalating threat pattern" : fakeProbability >= 40 ? "Needs human verification" : "Low scam signal profile");
  setText("alerts-count", `${Math.max(1, redFlagCount)}`);

  setList("red-flags", data.explanation.red_flags, "No red flags found.");
  setList("trust-signals", data.explanation.trust_signals, "No trust signals found.");
  setList("feature-triggers", data.explanation.triggered_features, "No feature triggers found.");
  setList("rule-matches", data.explanation.triggered_rules, "No rule matches found.");
  setList("model-reasoning", data.explanation.model_reasoning, "No model reasoning available.");

  updateRiskChip(data.risk_meter);
  document.getElementById("fake-bar").style.width = `${Math.max(6, fakeProbability)}%`;
  updateRing(data.overall_risk_score);
  updateTrendChart(fakeProbability);
  updateSignalChart(data);
  updateHeatmap(data);
  updateAlertFeed(data);
  recordHistory(data);
}

async function analyzeUrl(url) {
  if (!url) {
    statusEl.textContent = "A URL is required.";
    return;
  }

  setLoading(true);
  statusEl.textContent = uploadedContext
    ? "Running analysis with uploaded context and live job signals..."
    : "Fetching posting content and running fraud analysis...";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.details || data.error || "Analysis failed.");

    populateDashboard(data);
    statusEl.textContent = uploadedContext
      ? "Analysis complete. Uploaded context noted for analyst review."
      : "Analysis complete.";
  } catch (error) {
    statusEl.textContent = error.message;
  } finally {
    setLoading(false);
  }
}

function triggerDownload() {
  if (!latestResult) {
    statusEl.textContent = "Run a scan before downloading the report.";
    return;
  }

  const report = {
    generated_at: new Date().toISOString(),
    input_url: latestResult.input_url,
    dashboard: latestResult.dashboard,
    explanation: latestResult.explanation,
    features: latestResult.features,
    uploaded_context_excerpt: uploadedContext.slice(0, 1200),
  };

  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "jobguard-report.json";
  link.click();
  URL.revokeObjectURL(link.href);
}

sidebarToggle.addEventListener("click", () => {
  appFrame.classList.toggle("sidebar-collapsed");
  sidebar.classList.toggle("is-collapsed");
});

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    navItems.forEach((entry) => entry.classList.remove("is-active"));
    item.classList.add("is-active");
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await analyzeUrl(document.getElementById("url-input").value.trim());
});

scanAnotherButton.addEventListener("click", () => {
  form.reset();
  uploadedContext = "";
  statusEl.textContent = "Ready for another scan.";
  document.getElementById("url-input").focus();
});

quickDemoButton.addEventListener("click", async () => {
  const url = demoUrls[Math.floor(Math.random() * demoUrls.length)];
  document.getElementById("url-input").value = url;
  await analyzeUrl(url);
});

["dragenter", "dragover"].forEach((type) => {
  dropZone.addEventListener(type, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((type) => {
  dropZone.addEventListener(type, () => {
    dropZone.classList.remove("dragover");
  });
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  const file = event.dataTransfer.files[0];
  if (file) readTextFile(file);
});

fileUpload.addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) readTextFile(file);
});

function readTextFile(file) {
  if (!file.name.toLowerCase().endsWith(".txt")) {
    statusEl.textContent = "Only .txt uploads are supported right now.";
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    uploadedContext = String(reader.result || "").trim();
    statusEl.textContent = uploadedContext
      ? `Loaded analyst context from ${file.name}.`
      : "The uploaded file was empty.";
  };
  reader.readAsText(file);
}

downloadButton.addEventListener("click", () => {
  reportModal.classList.remove("hidden");
  reportModal.setAttribute("aria-hidden", "false");
});

closeModal.addEventListener("click", closeReportModal);
cancelDownload.addEventListener("click", closeReportModal);
confirmDownload.addEventListener("click", () => {
  triggerDownload();
  closeReportModal();
});

reportModal.addEventListener("click", (event) => {
  if (event.target.classList.contains("modal-backdrop")) {
    closeReportModal();
  }
});

function closeReportModal() {
  reportModal.classList.add("hidden");
  reportModal.setAttribute("aria-hidden", "true");
}

updateHeatmap({
  features: {
    upfront_payment_count: 0,
    brand_mismatch: 0,
    spoofed_email_count: 0,
    remote_scam_count: 0,
    internship_exploitation_count: 0,
    genericity_score: 0,
    urgency_count: 0,
  },
});
renderTimeline();
