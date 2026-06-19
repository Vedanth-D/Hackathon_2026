const form = document.getElementById("claim-form");
const submitBtn = document.getElementById("submit-btn");
const loadingEl = document.getElementById("loading");
const emptyEl = document.getElementById("empty-state");
const resultEl = document.getElementById("result");
const errorEl = document.getElementById("form-error");
const fileInput = document.getElementById("images");
const fileListEl = document.getElementById("file-list");

fileInput.addEventListener("change", () => {
  const names = Array.from(fileInput.files).map((f) => f.name);
  fileListEl.textContent = names.length ? names.join(", ") : "";
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorEl.textContent = "";

  const formData = new FormData(form);
  formData.set("mock_mode", document.getElementById("mock_mode").checked ? "true" : "false");

  submitBtn.disabled = true;
  emptyEl.classList.add("hidden");
  resultEl.classList.add("hidden");
  loadingEl.classList.remove("hidden");

  try {
    const res = await fetch("/api/review", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      errorEl.textContent = data.error || "Something went wrong.";
      emptyEl.classList.remove("hidden");
      return;
    }

    renderResult(data);
  } catch (err) {
    errorEl.textContent = "Request failed: " + err.message;
    emptyEl.classList.remove("hidden");
  } finally {
    loadingEl.classList.add("hidden");
    submitBtn.disabled = false;
  }
});

function renderResult(data) {
  const flags = (data.risk_flags || "")
    .split(";")
    .map((f) => f.trim())
    .filter(Boolean)
    .map((f) => `<span class="flag-pill">${escapeHtml(f)}</span>`)
    .join("") || "<span class=\"flag-pill\">none</span>";

  resultEl.innerHTML = `
    <span class="status-badge status-${data.claim_status}">${formatStatus(data.claim_status)}</span>

    <div class="justification">${escapeHtml(data.claim_status_justification || "")}</div>

    <dl class="kv-grid">
      <dt>Evidence standard met</dt><dd>${data.evidence_standard_met}</dd>
      <dt>Reason</dt><dd>${escapeHtml(data.evidence_standard_met_reason || "")}</dd>
      <dt>Issue type</dt><dd>${escapeHtml(data.issue_type || "")}</dd>
      <dt>Object part</dt><dd>${escapeHtml(data.object_part || "")}</dd>
      <dt>Severity</dt><dd>${escapeHtml(data.severity || "")}</dd>
      <dt>Supporting images</dt><dd>${escapeHtml(data.supporting_image_ids || "")}</dd>
      <dt>Valid image set</dt><dd>${data.valid_image}</dd>
    </dl>

    <div>
      <dt style="text-transform:uppercase;font-size:11px;color:#5b564c;">Risk flags</dt>
      <div style="margin-top:6px;">${flags}</div>
    </div>
  `;
  resultEl.classList.remove("hidden");
}

function formatStatus(status) {
  return (status || "").replace(/_/g, " ");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
