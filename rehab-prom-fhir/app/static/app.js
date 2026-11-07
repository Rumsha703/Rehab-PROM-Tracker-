"use strict";
// All dynamic content is written with textContent / DOM APIs, never innerHTML.

const SCALE = ["0 None", "1 Mild", "2 Moderate", "3 Severe", "4 Extreme"];
const QUESTIONNAIRE_REF = "Questionnaire/rehab-check-1";

function el(tag, attrs = {}, text) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}

async function loadQuestionnaire() {
  const res = await fetch("/fhir/Questionnaire/rehab-check-1");
  const q = await res.json();
  const box = document.getElementById("items");
  for (const item of q.item) {
    const fs = el("fieldset");
    fs.appendChild(el("legend", {}, item.text));
    SCALE.forEach((label, i) => {
      const id = `${item.linkId}-${i}`;
      const input = el("input", { type: "radio", name: item.linkId, id, value: String(i), required: "" });
      const lab = el("label", { for: id }, label);
      fs.appendChild(input);
      fs.appendChild(lab);
    });
    box.appendChild(fs);
  }
}

document.getElementById("patient-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = document.getElementById("p-status");
  const patient = document.getElementById("p-id").value.trim();
  const items = [];
  for (const fs of document.querySelectorAll("#items fieldset")) {
    const checked = fs.querySelector("input:checked");
    if (!checked) { status.textContent = "Please answer every question."; return; }
    items.push({ linkId: checked.name, answer: [{ valueInteger: Number(checked.value) }] });
  }
  const body = { resourceType: "QuestionnaireResponse", status: "completed",
    questionnaire: QUESTIONNAIRE_REF, subject: { reference: `Patient/${patient}` }, item: items };
  const res = await fetch("/fhir/QuestionnaireResponse", { method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": document.getElementById("p-key").value },
    body: JSON.stringify(body) });
  const data = await res.json();
  status.textContent = res.ok ? "Thank you. Your answers were saved."
    : `Could not save: ${data.issue ? data.issue[0].diagnostics : res.status}`;
});

function drawChart(series) {
  const svg = document.getElementById("chart");
  svg.replaceChildren();
  const ns = "http://www.w3.org/2000/svg";
  const w = 320, h = 120, pad = 18, max = 20;
  const x = (i) => series.length === 1 ? w / 2 : pad + (i * (w - 2 * pad)) / (series.length - 1);
  const y = (v) => h - pad - (v / max) * (h - 2 * pad);
  const pts = series.map((s, i) => `${x(i)},${y(s.total)}`).join(" ");
  const line = document.createElementNS(ns, "polyline");
  line.setAttribute("points", pts); line.setAttribute("fill", "none");
  line.setAttribute("stroke", "#005eb8"); line.setAttribute("stroke-width", "2");
  svg.appendChild(line);
  series.forEach((s, i) => {
    const c = document.createElementNS(ns, "circle");
    c.setAttribute("cx", x(i)); c.setAttribute("cy", y(s.total)); c.setAttribute("r", "4");
    c.setAttribute("fill", s.needs_review ? "#b32100" : "#005eb8");
    svg.appendChild(c);
  });
}

document.getElementById("clin-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = document.getElementById("c-status");
  const id = document.getElementById("c-id").value.trim();
  const res = await fetch(`/api/patients/${encodeURIComponent(id)}/summary`,
    { headers: { "X-API-Key": document.getElementById("c-key").value } });
  const data = await res.json();
  const wrap = document.getElementById("chart-wrap");
  if (!res.ok) {
    wrap.hidden = true;
    status.textContent = `Could not load: ${data.issue ? data.issue[0].diagnostics : res.status}`;
    return;
  }
  status.textContent = `${data.responses} response(s). Trend: ${data.trend.replace("_", " ")}. ` +
    (data.latest_needs_review ? "Latest response needs clinician review." : "No review flag on latest response.");
  wrap.hidden = data.responses === 0;
  if (data.responses === 0) return;
  drawChart(data.series);
  const tbody = document.querySelector("#series tbody");
  tbody.replaceChildren();
  for (const s of data.series) {
    const tr = el("tr");
    tr.appendChild(el("td", {}, new Date(s.authored).toLocaleString("en-GB")));
    tr.appendChild(el("td", {}, String(s.total)));
    tr.appendChild(el("td", { class: s.needs_review ? "bad" : "ok" }, s.needs_review ? "Review" : "OK"));
    tbody.appendChild(tr);
  }
});

loadQuestionnaire();
