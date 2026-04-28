const form = document.getElementById("analyze-form");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

function setList(id, items) {
  const target = document.getElementById(id);
  target.innerHTML = "";
  (items && items.length ? items : ["None"]).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    target.appendChild(li);
  });
}

function setText(id, value) {
  document.getElementById(id).textContent = value;
}

function updateMeter(score) {
  const clamped = Math.max(0, Math.min(100, score));
  document.getElementById("meter-fill").style.width = `${100 - clamped}%`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const url = document.getElementById("url-input").value.trim();
  if (!url) {
    statusEl.textContent = "A URL is required.";
    return;
  }

  statusEl.textContent = "Fetching posting content and running fraud analysis...";
  resultsEl.classList.add("hidden");

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

    setText("risk-score", data.overall_risk_score.toFixed(1));
    setText("fake-percentage", `${data.fake_percentage.toFixed(1)}%`);
    setText("classification", data.model_prediction.label);
    setText("recommendation", data.explanation.recommendation);
    setText("risk-meter", data.risk_meter);
    setText("summary-text", data.explanation.summary);
    setText("job-title", data.posting.title);
    setText("company-name", data.posting.company_name || "Unknown company");
    setText("fraud-category", data.model_prediction.category.replaceAll("_", " "));
    setText("confidence", `${data.confidence_score.toFixed(1)}%`);
    setText("domain", data.posting.domain_info.root_domain);
    setText("salary", data.posting.salary_text || "Not stated");
    setList("red-flags", data.explanation.red_flags);
    setList("trust-signals", data.explanation.trust_signals);
    setList("rule-matches", data.explanation.triggered_rules);
    setList("feature-triggers", data.explanation.triggered_features);
    setList("model-reasoning", data.explanation.model_reasoning);
    document.getElementById("json-output").textContent = JSON.stringify(data.dashboard, null, 2);
    updateMeter(data.overall_risk_score);

    resultsEl.classList.remove("hidden");
    statusEl.textContent = "Analysis complete.";
  } catch (error) {
    statusEl.textContent = error.message;
  }
});
