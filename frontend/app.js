const form = document.getElementById("analyze-form");
const statusEl = document.getElementById("status");
const downloadButton = document.getElementById("download-report");
const scanAnotherButton = document.getElementById("scan-another");
const historyBody = document.getElementById("history-body");

const scanHistory = [];
let latestResult = null;

function setText(id, value) {
  document.getElementById(id).textContent = value;
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

function riskPillClass(level) {
  const key = (level || "").toLowerCase();
  if (key === "low") return "pill pill-low";
  if (key === "medium") return "pill pill-medium";
  if (key === "high") return "pill pill-high";
  if (key === "critical") return "pill pill-critical";
  return "pill pill-neutral";
}

function tablePillClass(level) {
  const key = (level || "").toLowerCase();
  if (key === "low") return "table-pill pill-low";
  if (key === "medium") return "table-pill pill-medium";
  return "table-pill pill-high";
}

function updateArc(id, score) {
  const element = document.getElementById(id);
  element.style.setProperty("--arc-progress", `${Math.max(0, Math.min(100, score))}%`);
}

function inferJobType(posting) {
  const text = `${posting.title} ${posting.job_description}`.toLowerCase();
  if (text.includes("intern")) return "Internship";
  if (text.includes("remote")) return "Remote";
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

function renderHistory() {
  historyBody.innerHTML = "";
  if (!scanHistory.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 5;
    cell.className = "empty-row";
    cell.textContent = "No scans yet.";
    row.appendChild(cell);
    historyBody.appendChild(row);
    return;
  }

  scanHistory.slice().reverse().forEach((entry) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${entry.title} / ${entry.company}</td>
      <td>${entry.score}</td>
      <td><span class="${tablePillClass(entry.level)}">${entry.level}</span></td>
      <td>${entry.result}</td>
      <td>${entry.time}</td>
    `;
    historyBody.appendChild(row);
  });
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
  if (scanHistory.length > 8) {
    scanHistory.shift();
  }
  renderHistory();
}

function populateDashboard(data) {
  latestResult = data;
  const posting = data.posting;
  const features = data.features;
  const primaryTriggerList = data.explanation.triggered_features.slice(0, 4);
  const topRedFlags = data.explanation.red_flags.slice(0, 4);

  setText("risk-score", `${data.overall_risk_score.toFixed(0)} / 100`);
  setText("risk-label", `${data.risk_meter} Risk`);
  setText("fake-percentage", `${data.fake_percentage.toFixed(0)}%`);
  setText("confidence", `Confidence Score: ${data.confidence_score.toFixed(0)}%`);
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
  setText("report-fake", `${data.fake_percentage.toFixed(0)}%`);
  setText("report-level", data.risk_meter);
  setText("report-recommendation", data.explanation.recommendation);
  setText("report-score-center", `${data.overall_risk_score.toFixed(0)}`);
  setText("report-label-center", data.risk_meter);
  setText("report-pattern", formatPattern(data.model_prediction.category));
  setText("report-timestamp", new Date().toLocaleString());

  setList("red-flags", data.explanation.red_flags, "No red flags found.");
  setList("trust-signals", data.explanation.trust_signals, "No trust signals found.");
  setList("top-triggers", primaryTriggerList, "No major triggers captured.");
  setList("feature-triggers", data.explanation.triggered_features, "No feature triggers found.");
  setList("rule-matches", data.explanation.triggered_rules, "No rule matches found.");
  setList("model-reasoning", data.explanation.model_reasoning, "No model reasoning available.");
  setList("report-red-flags", topRedFlags, "No major red flags.");

  document.getElementById("risk-meter").className = riskPillClass(data.risk_meter);
  document.getElementById("risk-meter").textContent = data.risk_meter.toUpperCase();
  document.getElementById("fake-bar").style.width = `${Math.max(4, data.fake_percentage)}%`;
  updateArc("arc-fill", data.overall_risk_score);
  updateArc("report-arc-fill", data.overall_risk_score);

  recordHistory(data);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = document.getElementById("url-input").value.trim();
  if (!url) {
    statusEl.textContent = "A URL is required.";
    return;
  }

  statusEl.textContent = "Fetching posting content and running fraud analysis...";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.details || data.error || "Analysis failed.");
    }

    populateDashboard(data);
    statusEl.textContent = "Analysis complete.";
  } catch (error) {
    statusEl.textContent = error.message;
  }
});

scanAnotherButton.addEventListener("click", () => {
  form.reset();
  document.getElementById("url-input").focus();
  statusEl.textContent = "Ready for another scan.";
});

downloadButton.addEventListener("click", () => {
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
  };

  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "jobguard-report.json";
  link.click();
  URL.revokeObjectURL(link.href);
});

renderHistory();
