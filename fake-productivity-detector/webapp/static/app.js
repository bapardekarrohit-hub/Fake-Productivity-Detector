/* Fake Productivity Detector - front end (vanilla JS, no dependencies) */
"use strict";

// ------------------------------------------------------------------ icons
const ICON_PATHS = {
  activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  user: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  grid: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>',
  logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5M21 12H9"/>',
  trash: '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  menu: '<path d="M3 12h18M3 6h18M3 18h18"/>',
  up: '<path d="M23 6l-9.5 9.5-5-5L1 18"/><path d="M17 6h6v6"/>',
  down: '<path d="M23 18l-9.5-9.5-5 5L1 6"/><path d="M17 18h6v-6"/>',
  alert: '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4M12 17h.01"/>',
  award: '<circle cx="12" cy="8" r="7"/><path d="M8.21 13.89L7 23l5-3 5 3-1.21-9.12"/>',
  chart: '<path d="M18 20V10M12 20V4M6 20v-6"/>',
  layers: '<path d="M12 2l10 5-10 5L2 7z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/>',
  eye: '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
  bulb: '<path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z"/>',
  reset: '<path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>',
  check: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/>',
  filter: '<path d="M22 3H2l8 9.46V19l4 2v-8.54z"/>',
  lock: '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  target: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  phone: '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/>',
  coffee: '<path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4z"/><path d="M6 1v3M10 1v3M14 1v3"/>',
  briefcase: '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
};
const icon = (n) => `<span class="ico"><svg viewBox="0 0 24 24">${ICON_PATHS[n] || ""}</svg></span>`;
function hydrateIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((el) => { if (!el.firstChild) el.innerHTML = `<svg viewBox="0 0 24 24">${ICON_PATHS[el.dataset.icon] || ""}</svg>`; });
}

// ------------------------------------------------------------------ helpers
const $ = (s, r = document) => r.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const COLORS = { high: "#22c55e", mod: "#f59e0b", fake: "#ef4444", blue: "#3b82f6", violet: "#8b5cf6" };
const catKey = (c) => (c === "Highly Productive" ? "high" : c === "Moderately Productive" ? "mod" : "fake");
const badge = (c) => `<span class="badge ${catKey(c)}">${esc(c)}</span>`;
const fmtDT = (iso) => new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" });
const fmtDay = (iso) => new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
const hrs = (v) => `${Math.round(v * 10) / 10}h`;
const avg = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);

async function api(method, url, body) {
  const res = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  let data = {};
  try { data = await res.json(); } catch (_) { /* non-JSON */ }
  if (res.status === 401 && url !== "/api/login") { state.user = null; showLogin(); }
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}
function toast(msg, isErr) {
  const t = $("#toast"); t.textContent = msg; t.className = "toast" + (isErr ? " err" : ""); t.hidden = false;
  clearTimeout(toast.t); toast.t = setTimeout(() => (t.hidden = true), 3200);
}
function downloadFile(name, text, type = "text/csv") {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}
const csvCell = (v) => { const s = String(v ?? ""); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
const toCSV = (rows) => rows.map((r) => r.map(csvCell).join(",")).join("\n");

// ------------------------------------------------------------------ charts (inline SVG)
function niceMax(v) { if (v <= 0) return 1; const p = Math.pow(10, Math.floor(Math.log10(v))); const n = v / p; return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10) * p; }

function lineChart(points, color) {
  if (!points.length) return `<div class="empty">No data yet</div>`;
  const W = 1000, H = 250, L = 38, R = 20, T = 14, B = 34, iw = W - L - R, ih = H - T - B;
  const x = (i) => (points.length === 1 ? L + iw / 2 : L + (iw * i) / (points.length - 1));
  const y = (v) => T + ih * (1 - v / 100);
  let out = "";
  [0, 25, 50, 75, 100].forEach((t) => { out += `<line x1="${L}" x2="${W - R}" y1="${y(t)}" y2="${y(t)}" stroke="#e5e7eb" stroke-dasharray="3 4"/><text x="${L - 8}" y="${y(t) + 4}" text-anchor="end" font-size="11">${t}</text>`; });
  // smooth path (cardinal spline, control points clamped so the curve never overshoots the data)
  const pts = points.map((p, i) => [x(i), y(p.value)]);
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2, k = 0.18;
    const lo = Math.min(p1[1], p2[1]), hi = Math.max(p1[1], p2[1]);
    const c1y = Math.min(hi, Math.max(lo, p1[1] + (p2[1] - p0[1]) * k));
    const c2y = Math.min(hi, Math.max(lo, p2[1] - (p3[1] - p1[1]) * k));
    d += ` C${p1[0] + (p2[0] - p0[0]) * k},${c1y} ${p2[0] - (p3[0] - p1[0]) * k},${c2y} ${p2[0]},${p2[1]}`;
  }
  if (pts.length > 1) out += `<path d="${d}" fill="none" stroke="${color}" stroke-width="2"/>`;
  const step = Math.max(1, Math.ceil(points.length / 10));
  points.forEach((p, i) => {
    out += `<circle cx="${pts[i][0]}" cy="${pts[i][1]}" r="4" fill="${color}"><title>${esc(fmtDT(p.date))}: ${p.value}</title></circle>`;
    if (i % step === 0 || i === points.length - 1) out += `<text x="${pts[i][0]}" y="${H - 10}" text-anchor="middle" font-size="11">${esc(fmtDay(p.date))}</text>`;
  });
  return `<div class="chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Score trend">${out}</svg></div>`;
}

function pieChart(slices) {
  const total = slices.reduce((s, x) => s + x.value, 0);
  if (!total) return `<div class="empty">No data yet</div>`;
  const W = 560, H = 230, cx = W / 2, cy = H / 2, r = 70;
  let a0 = -Math.PI / 2, out = "";
  slices.filter((s) => s.value > 0).forEach((s) => {
    const frac = s.value / total, a1 = a0 + frac * 2 * Math.PI, mid = (a0 + a1) / 2;
    if (frac >= 0.9999) out += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${s.color}"/>`;
    else {
      const [x0, y0, x1, y1] = [cx + r * Math.cos(a0), cy + r * Math.sin(a0), cx + r * Math.cos(a1), cy + r * Math.sin(a1)];
      out += `<path d="M${cx},${cy} L${x0},${y0} A${r},${r} 0 ${frac > 0.5 ? 1 : 0} 1 ${x1},${y1} Z" fill="${s.color}" stroke="#fff" stroke-width="1.5"><title>${esc(s.label)}: ${s.value}</title></path>`;
    }
    const lx = cx + (r + 16) * Math.cos(mid), ly = cy + (r + 16) * Math.sin(mid), right = Math.cos(mid) >= 0;
    out += `<text x="${lx}" y="${ly + 4}" text-anchor="${right ? "start" : "end"}" font-size="12" style="fill:${s.color}">${esc(s.label)}: ${Math.round(frac * 100)}%</text>`;
    a0 = a1;
  });
  return `<div class="chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Category split">${out}</svg></div>`;
}

function groupedBars(groups, series) {
  if (!groups.length) return `<div class="empty">No data yet</div>`;
  const W = 600, H = 250, L = 34, R = 10, T = 12, B = 30, iw = W - L - R, ih = H - T - B;
  const max = niceMax(Math.max(...groups.flatMap((g) => g.values), 1));
  let out = "";
  for (let i = 0; i <= 4; i++) { const v = (max * i) / 4, yy = T + ih * (1 - i / 4); out += `<line x1="${L}" x2="${W - R}" y1="${yy}" y2="${yy}" stroke="#e5e7eb" stroke-dasharray="3 4"/><text x="${L - 6}" y="${yy + 4}" text-anchor="end" font-size="11">${Math.round(v * 10) / 10}</text>`; }
  const gw = iw / groups.length, bw = Math.min(30, (gw * 0.7) / series.length);
  groups.forEach((g, gi) => {
    const start = L + gi * gw + (gw - bw * series.length - 2 * (series.length - 1)) / 2;
    g.values.forEach((v, si) => {
      const h = (v / max) * ih, bx = start + si * (bw + 2);
      out += `<rect x="${bx}" y="${T + ih - h}" width="${bw}" height="${Math.max(h, 0)}" rx="3" fill="${series[si].color}"><title>${esc(series[si].name)}: ${hrs(v)}</title></rect>`;
    });
    out += `<text x="${L + gi * gw + gw / 2}" y="${H - 10}" text-anchor="middle" font-size="11">${esc(g.label)}</text>`;
  });
  const legend = series.map((s) => `<span><i style="background:${s.color}"></i>${esc(s.name)}</span>`).join("");
  return `<div class="chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Activity breakdown">${out}</svg><div class="legend">${legend}</div></div>`;
}

function gauge(score, color) {
  const r = 52, c = 2 * Math.PI * r, off = c * (1 - Math.min(100, Math.max(0, score)) / 100);
  return `<div class="gauge"><svg width="150" height="150" viewBox="0 0 150 150" role="img" aria-label="Score ${score} out of 100">
    <circle cx="75" cy="75" r="${r}" fill="none" stroke="#e5e7eb" stroke-width="10"/>
    <circle cx="75" cy="75" r="${r}" fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round" stroke-dasharray="${c}" stroke-dashoffset="${off}" transform="rotate(-90 75 75)"/>
    <text x="75" y="80" text-anchor="middle" font-size="34" style="fill:#111">${score}</text>
    <text x="75" y="100" text-anchor="middle" font-size="11" style="fill:#6b7280">Score</text></svg></div>`;
}

// ------------------------------------------------------------------ state / shell
const state = { user: null, history: [], mode: "login" };
const PAGES = [
  { id: "dashboard", label: "Dashboard", icon: "grid", title: "Dashboard", sub: "Overview of your productivity analytics" },
  { id: "upload", label: "Upload CSV", icon: "upload", title: "Upload CSV", sub: "Batch analyze productivity data from CSV files" },
  { id: "manual", label: "Manual Analysis", icon: "activity", title: "Manual Analysis", sub: "Analyze individual productivity data" },
  { id: "reports", label: "Reports", icon: "file", title: "Reports", sub: "View and export your productivity reports" },
  { id: "history", label: "History", icon: "clock", title: "History", sub: "Track your productivity over time" },
  { id: "model", label: "Model Insights", icon: "layers", title: "Model Insights", sub: "How the machine learning model was trained and how well it performs" },
  { id: "profile", label: "Profile", icon: "user", title: "Profile", sub: "Your account information and statistics" },
];

function showLogin() { $("#login-view").hidden = false; $("#app-view").hidden = true; }
function showApp() {
  $("#login-view").hidden = true; $("#app-view").hidden = false;
  $("#chip-name").textContent = state.user.username;
  $("#chip-avatar").textContent = state.user.username.charAt(0).toUpperCase();
  $("#nav").innerHTML = PAGES.map((p) => `<a class="nav-item" href="#/${p.id}" data-page="${p.id}">${icon(p.icon)}<span class="nav-label">${p.label}</span><span class="dot"></span></a>`).join("");
  route();
}
async function loadHistory() { state.history = (await api("GET", "/api/history")).analyses; return state.history; }

async function route() {
  if (!state.user) return;
  const id = (location.hash.replace("#/", "") || "dashboard");
  const page = PAGES.find((p) => p.id === id) || PAGES[0];
  document.querySelectorAll(".nav-item").forEach((a) => a.classList.toggle("active", a.dataset.page === page.id));
  $("#page-title").textContent = page.title; $("#page-sub").textContent = page.sub; $("#page-actions").innerHTML = "";
  try { await RENDER[page.id](); } catch (e) { $("#page").innerHTML = `<div class="card panel empty">Could not load this page: ${esc(e.message)}</div>`; }
  hydrateIcons($("#page"));
}

// ------------------------------------------------------------------ pages
const stat = (cls, ic, color, val, cap) => `<div class="stat ${cls}"><div class="sicon" style="background:${color}">${icon(ic)}</div><div class="val">${val}</div><div class="cap">${cap}</div></div>`;
const trendOf = (h) => (h.length >= 2 ? h[0].score - h[1].score : 0); // history is newest-first
const emptyState = (msg) => `<div class="empty">${msg}<br><a class="btn btn-primary" href="#/manual">Run your first analysis</a></div>`;

const RENDER = {
  async dashboard() {
    const h = await loadHistory();
    $("#page-actions").innerHTML = `<span class="date-chip">${icon("clock")} ${new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" })}</span>`;
    const by = (c) => h.filter((r) => r.category === c).length;
    const chrono = [...h].reverse();
    const pie = pieChart([
      { label: "Highly Productive", value: by("Highly Productive"), color: COLORS.high },
      { label: "Moderately Productive", value: by("Moderately Productive"), color: COLORS.mod },
      { label: "Fake Productivity", value: by("Fake Productivity"), color: COLORS.fake }]);
    const last5 = chrono.slice(-5).map((r) => ({ label: fmtDay(r.created_at), values: [r.task_hours, r.idle_hours, r.social_hours] }));
    $("#page").innerHTML = `
      <div class="stats s4">
        ${stat("blue", "users", "#3b82f6", h.length, "Total Analyses")}
        ${stat("violet", "up", "#a855f7", Math.round(avg(h.map((r) => r.score))), "Average Score")}
        ${stat("rose", "alert", "#ef4444", by("Fake Productivity"), "Fake Productivity")}
        ${stat("green", "award", "#22c55e", by("Highly Productive"), "Highly Productive")}
      </div>
      <div class="grid2" style="margin-top:16px">
        <div class="card panel"><h4>Productivity Categories</h4>${pie}</div>
        <div class="card panel"><h4>Recent Activity Breakdown</h4>${groupedBars(last5, [{ name: "Productive", color: COLORS.blue }, { name: "Idle", color: COLORS.fake }, { name: "Social", color: COLORS.mod }])}</div>
      </div>
      <div class="card panel" style="margin-top:16px"><h4>Productivity Trend</h4>${lineChart(chrono.slice(-12).map((r) => ({ date: r.created_at, value: r.score })), COLORS.violet)}</div>
      ${h.length ? "" : emptyState("No analyses yet.")}`;
  },

  async upload() {
    $("#page-actions").innerHTML = `<button class="btn btn-green" id="tpl">${icon("download")} Download Template</button>`;
    $("#page").innerHTML = `
      <div class="card panel"><h3 style="color:var(--ink)">CSV File Upload</h3>
        <div class="drop" id="drop"><div>${icon("upload")}</div><b id="file-name">productivity_dataset.csv</b><span>or click to browse</span>
          <small>Expected columns: Task_Hours, Idle_Hours, Social_Media_Usage, Break_Frequency, Tasks_Completed</small></div>
        <input id="file" type="file" accept=".csv,text/csv" hidden>
        <div class="btn-row"><button class="btn btn-primary" id="analyze-csv">${icon("check")} Analyze CSV</button><button class="btn btn-ghost" id="clear-csv">${icon("trash")} Clear</button></div>
        <div id="csv-error" class="form-error"></div></div>
      <div class="card panel" id="csv-results" style="margin-top:16px" hidden></div>`;
    let text = null, results = [];
    const setFile = async (f) => { if (!f) return; text = await f.text(); $("#file-name").textContent = f.name; $("#csv-error").textContent = ""; };
    $("#tpl").onclick = () => downloadFile("productivity_template.csv", toCSV([
      ["Task_Hours", "Idle_Hours", "Social_Media_Usage", "Break_Frequency", "Tasks_Completed"],
      [7.5, 1, 1.2, 3, 9], [6, 2, 2.5, 4, 5], [5, 3, 4, 6, 2], [9, 1.5, 2, 3, 1]]));
    $("#drop").onclick = () => $("#file").click();
    $("#file").onchange = (e) => setFile(e.target.files[0]);
    ["dragover", "dragenter"].forEach((ev) => $("#drop").addEventListener(ev, (e) => { e.preventDefault(); $("#drop").classList.add("over"); }));
    ["dragleave", "drop"].forEach((ev) => $("#drop").addEventListener(ev, (e) => { e.preventDefault(); $("#drop").classList.remove("over"); }));
    $("#drop").addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));
    $("#clear-csv").onclick = () => { text = null; results = []; $("#file").value = ""; $("#file-name").textContent = "productivity_dataset.csv"; $("#csv-results").hidden = true; $("#csv-error").textContent = ""; };
    $("#analyze-csv").onclick = async () => {
      if (!text) { $("#csv-error").textContent = "Choose a CSV file first."; return; }
      const btn = $("#analyze-csv"); btn.disabled = true;
      try {
        const data = await api("POST", "/api/analyze_csv", { csv: text });
        results = data.results; $("#csv-error").textContent = data.errors.length ? `${data.errors.length} row(s) skipped (first: row ${data.errors[0].row}, ${data.errors[0].error}).` : "";
        const box = $("#csv-results"); box.hidden = false;
        box.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><h3 style="margin:0;color:var(--ink)">Analysis Results (${results.length} entries)</h3><button class="btn btn-blue" id="export-csv">${icon("download")} Export Results</button></div>
          <div class="results">${results.map((r) => `<div class="res ${catKey(r.category)}"><div class="top"><span>Row ${r.row}</span><b>${r.score}</b></div>${badge(r.category)}</div>`).join("")}</div>`;
        hydrateIcons(box);
        $("#export-csv").onclick = () => downloadFile("productivity_results.csv", toCSV([["Row", "Task_Hours", "Idle_Hours", "Social_Media_Usage", "Break_Frequency", "Tasks_Completed", "Score", "Category"], ...results.map((r) => [r.row, r.task_hours, r.idle_hours, r.social_hours, r.break_frequency, r.tasks_completed, r.score, r.category])]));
        toast(`Analyzed ${results.length} rows. Saved to your history.`);
      } catch (e) { $("#csv-error").textContent = e.message; } finally { btn.disabled = false; }
    };
  },

  async manual() {
    const fields = [
      ["task_hours", "Task Hours", "target", "Hours spent on productive tasks", 0.5],
      ["idle_hours", "Idle Hours", "clock", "Hours of unproductive time", 0.5],
      ["social_hours", "Social Media (hours)", "phone", "Time spent on social platforms", 0.5],
      ["break_frequency", "Break Frequency", "coffee", "Number of breaks taken", 1],
      ["tasks_completed", "Tasks Completed", "check", "Number of tasks finished", 1]];
    $("#page").innerHTML = `
      <div class="grid-form">
        <div class="card panel"><h3 style="color:var(--ink)"><span class="ico" style="color:#7c3aed"><svg viewBox="0 0 24 24">${ICON_PATHS.activity}</svg></span>Activity Input</h3>
          <form id="manual-form" novalidate>
            ${fields.map(([k, l, ic, help, step]) => `<div class="field"><label for="f-${k}">${icon(ic)}${l}</label><input id="f-${k}" name="${k}" type="number" min="0" step="${step}" inputmode="decimal" placeholder="0"><small>${help}</small></div>`).join("")}
            <div id="manual-error" class="form-error"></div>
            <div class="btn-row"><button class="btn btn-primary" type="submit">${icon("activity")} Analyze Productivity</button><button class="btn btn-ghost" type="button" id="reset">${icon("reset")} Reset</button></div>
          </form></div>
        <div class="card panel" id="analysis-panel"><h3 style="color:var(--ink)">${icon("chart")} Productivity Analysis</h3><div class="placeholder">Enter your activity data and press <b>Analyze Productivity</b> to see your score, a breakdown and model-based suggestions.</div></div>
      </div>`;
    $("#reset").onclick = () => { $("#manual-form").reset(); $("#manual-error").textContent = ""; };
    $("#manual-form").onsubmit = async (e) => {
      e.preventDefault();
      const body = {}; for (const [k] of fields) { const v = $(`#f-${k}`).value; if (v === "") { $("#manual-error").textContent = "Fill in all five fields."; return; } body[k] = Number(v); }
      $("#manual-error").textContent = "";
      try {
        const r = await api("POST", "/api/analyze", body);
        const key = catKey(r.category), color = COLORS[key];
        const items = Object.entries(r.breakdown), colors = [COLORS.blue, COLORS.fake, COLORS.mod, COLORS.violet];
        const max = niceMax(Math.max(...items.map((i) => i[1]), 1)), W = 520, H = 220, L = 34, T = 10, B = 28, iw = W - L - 10, ih = H - T - B;
        let svg = ""; for (let i = 0; i <= 4; i++) { const yy = T + ih * (1 - i / 4); svg += `<line x1="${L}" x2="${W - 10}" y1="${yy}" y2="${yy}" stroke="#e5e7eb" stroke-dasharray="3 4"/><text x="${L - 6}" y="${yy + 4}" text-anchor="end" font-size="11">${Math.round(((max * i) / 4) * 10) / 10}</text>`; }
        items.forEach(([name, v], i) => { const bw = iw / items.length, h = (v / max) * ih, bx = L + i * bw + bw * 0.15; svg += `<rect x="${bx}" y="${T + ih - h}" width="${bw * 0.7}" height="${h}" rx="4" fill="${colors[i]}"><title>${esc(name)}: ${v}</title></rect><text x="${bx + bw * 0.35}" y="${H - 8}" text-anchor="middle" font-size="11">${esc(name)}</text>`; });
        $("#analysis-panel").innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center"><h3 style="color:var(--ink)">${icon("chart")} Productivity Analysis</h3><button class="btn btn-blue" id="export-one">${icon("download")} Export</button></div>
          ${gauge(r.score, color)}<div class="pill ${key}"><span>${icon(key === "fake" ? "alert" : "up")}${esc(r.category)}</span></div>
          <h4>Activity Breakdown (hours)</h4><div class="chart"><svg viewBox="0 0 ${W} ${H}">${svg}</svg></div>
          <div class="tips"><h4>${icon("bulb")} Improvement Suggestions</h4><ul>${r.suggestions.map((s) => `<li>${esc(s)}</li>`).join("")}</ul></div>`;
        hydrateIcons($("#analysis-panel"));
        $("#export-one").onclick = () => downloadFile("productivity_analysis.csv", toCSV([["Task_Hours", "Idle_Hours", "Social_Media_Usage", "Break_Frequency", "Tasks_Completed", "Score", "Category"], [body.task_hours, body.idle_hours, body.social_hours, body.break_frequency, body.tasks_completed, r.score, r.category]]));
      } catch (err) { $("#manual-error").textContent = err.message; }
    };
  },

  async reports() {
    const h = await loadHistory();
    $("#page-actions").innerHTML = `<button class="btn btn-primary" id="export-all">${icon("download")} Export All</button>`;
    const scores = h.map((r) => r.score), tr = trendOf(h);
    $("#page").innerHTML = `
      <div class="stats s4">
        ${stat("blue", "chart", "#3b82f6", scores.length ? avg(scores).toFixed(1) : "-", "Average Score")}
        ${stat("green", "award", "#22c55e", scores.length ? Math.max(...scores).toFixed(1) : "-", "Highest Score")}
        ${stat("rose", "alert", "#ef4444", scores.length ? Math.min(...scores).toFixed(1) : "-", "Lowest Score")}
        ${stat("violet", tr >= 0 ? "up" : "down", "#a855f7", `<span class="${tr >= 0 ? "pos" : "neg"}">${tr.toFixed(1)}</span>`, "Trend (latest vs previous)")}
      </div>
      <div class="card filters" style="margin-top:16px">${icon("filter")}<b style="font-size:12px">Filters:</b>
        <select id="f-cat"><option value="">All Categories</option><option>Highly Productive</option><option>Moderately Productive</option><option>Fake Productivity</option></select>
        <select id="f-sort"><option value="date_desc">Sort by Date</option><option value="date_asc">Oldest first</option><option value="score_desc">Score: high to low</option><option value="score_asc">Score: low to high</option></select>
        <span class="count" id="count"></span></div>
      <div class="card panel" style="margin-top:16px"><h3 style="color:var(--ink)">${icon("file")} All Reports</h3><div class="tbl-wrap"><table><thead><tr><th>Date &amp; Time</th><th>Score</th><th>Category</th><th>Productive</th><th>Idle</th><th>Social</th></tr></thead><tbody id="tbody"></tbody></table></div></div>`;
    let view = h;
    const draw = () => {
      const cat = $("#f-cat").value, sort = $("#f-sort").value;
      view = h.filter((r) => !cat || r.category === cat);
      view.sort({ date_desc: (a, b) => (a.created_at < b.created_at ? 1 : -1), date_asc: (a, b) => (a.created_at > b.created_at ? 1 : -1), score_desc: (a, b) => b.score - a.score, score_asc: (a, b) => a.score - b.score }[sort]);
      $("#count").textContent = `Showing ${view.length} of ${h.length} reports`;
      $("#tbody").innerHTML = view.length ? view.map((r) => `<tr><td>${fmtDT(r.created_at)}</td><td><b>${r.score}</b></td><td>${badge(r.category)}</td><td>${hrs(r.task_hours)}</td><td>${hrs(r.idle_hours)}</td><td>${hrs(r.social_hours)}</td></tr>`).join("") : `<tr><td colspan="6" class="empty">No reports match.</td></tr>`;
    };
    $("#f-cat").onchange = draw; $("#f-sort").onchange = draw; draw();
    $("#export-all").onclick = () => { if (!h.length) return toast("Nothing to export yet.", true); downloadFile("productivity_reports.csv", toCSV([["Date", "Source", "Task_Hours", "Idle_Hours", "Social_Media_Usage", "Break_Frequency", "Tasks_Completed", "Score", "Category"], ...h.map((r) => [r.created_at, r.source, r.task_hours, r.idle_hours, r.social_hours, r.break_frequency, r.tasks_completed, r.score, r.category])])); };
  },

  async history() {
    const h = await loadHistory(), tr = trendOf(h);
    $("#page").innerHTML = `<div class="card panel"><h3>${icon("clock")} Productivity History</h3>
      <div class="stats s3">
        <div class="stat blue"><div class="cap">Total Analyses</div><div class="val">${h.length}</div></div>
        <div class="stat violet"><div class="cap">Average Score</div><div class="val">${Math.round(avg(h.map((r) => r.score)))}</div></div>
        <div class="stat rose"><div class="cap">Recent Trend ${icon(tr >= 0 ? "up" : "down")}</div><div class="val ${tr >= 0 ? "pos" : "neg"}">${tr}</div></div></div>
      <h4 style="margin-top:18px">Score Trend</h4>${lineChart([...h].reverse().slice(-15).map((r) => ({ date: r.created_at, value: r.score })), COLORS.blue)}
      <h4 style="margin-top:14px">Recent Analyses</h4>
      <div class="list">${h.length ? h.slice(0, 50).map((r) => `<div class="row-item"><div><small>${fmtDT(r.created_at)}</small>${badge(r.category)}<span class="who">${esc(r.row_label || state.user.username)}</span></div><div class="score">${r.score}</div></div>`).join("") : `<div class="empty">No history yet.</div>`}</div>
      <button class="btn btn-danger" id="del-all" style="margin-top:16px" ${h.length ? "" : "disabled"}>${icon("trash")} Delete All History</button></div>`;
    $("#del-all").onclick = async () => { if (!confirm("Delete all of your analysis history? This cannot be undone.")) return; await api("DELETE", "/api/history"); toast("History deleted."); route(); };
  },

  async model() {
    const m = await api("GET", "/api/model");
    const maxImp = Math.max(...Object.values(m.feature_importance));
    const names = { productive_ratio: "Productive time share", tasks_completed: "Tasks completed", tasks_per_task_hour: "Tasks per task-hour", social_hours: "Social media hours", idle_hours: "Idle hours", breaks_per_hour: "Breaks per hour", social_ratio: "Social time share", idle_ratio: "Idle time share", task_hours: "Task hours", break_frequency: "Break frequency", total_hours: "Total hours" };
    const cm = m.confusion_matrix, short = ["Fake", "Moderate", "High"], tot = cm.flat().reduce((a, b) => a + b, 0);
    const cell = (v, diag) => `<div style="background:${diag ? `rgba(99,102,241,${0.15 + 0.7 * v / tot * 3})` : `rgba(239,68,68,${Math.min(0.5, v / tot * 8)})`}">${v}</div>`;
    $("#page").innerHTML = `
      <div class="stats s4">
        ${stat("blue", "layers", "#3b82f6", esc(m.best_model), "Selected model (best CV error)")}
        ${stat("violet", "target", "#a855f7", m.test.mae.toFixed(2), "Test MAE (score points)")}
        ${stat("green", "check", "#22c55e", (m.test.r2 * 100).toFixed(1) + "%", "Test R-squared")}
        ${stat("rose", "award", "#ef4444", (m.test.category_accuracy * 100).toFixed(1) + "%", "Category accuracy")}
      </div>
      <div class="grid2" style="margin-top:16px">
        <div class="card panel"><h3>${icon("chart")} What drives the score</h3><p style="font-size:11.5px;color:var(--muted);margin-bottom:14px">Permutation importance: how much the error grows when a feature is shuffled.</p>
          ${Object.entries(m.feature_importance).map(([k, v]) => `<div class="bar-h"><span>${esc(names[k] || k)}</span><div class="track"><div class="fill" style="width:${(v / maxImp) * 100}%"></div></div><span class="mono">${v.toFixed(2)}</span></div>`).join("")}</div>
        <div class="card panel"><h3>${icon("grid")} Category confusion matrix</h3><p style="font-size:11.5px;color:var(--muted);margin-bottom:14px">Rows = true category, columns = predicted (held-out test set, ${m.n_test} rows).</p>
          <div class="cm"><div class="h"></div>${short.map((s) => `<div class="h">Pred. ${s}</div>`).join("")}
          ${cm.map((row, i) => `<div class="h" style="text-align:right">True ${short[i]}</div>${row.map((v, j) => cell(v, i === j)).join("")}`).join("")}</div></div>
      </div>
      <div class="grid2" style="margin-top:16px">
        <div class="card panel"><h3>${icon("layers")} Model comparison (5-fold CV)</h3><table><thead><tr><th>Model</th><th>MAE</th><th>R&sup2;</th></tr></thead><tbody>
          ${m.cv.map((r) => `<tr><td>${esc(r.model)}${r.model === m.best_model ? " " + badge("Highly Productive").replace("Highly Productive", "selected") : ""}</td><td>${r.cv_mae}</td><td>${r.cv_r2}</td></tr>`).join("")}</tbody></table></div>
        <div class="card panel"><h3>${icon("users")} Training data</h3>
          <p style="font-size:12px;margin-bottom:10px">${m.n_rows.toLocaleString()} rows (${m.n_train.toLocaleString()} train / ${m.n_test.toLocaleString()} test).</p>
          ${Object.entries(m.class_distribution).map(([k, v]) => `<div class="bar-h"><span>${esc(k)}</span><div class="track"><div class="fill" style="width:${(v / m.n_rows) * 100}%;background:${COLORS[catKey(k)]}"></div></div><span class="mono">${v}</span></div>`).join("")}
          <p style="font-size:11.5px;color:var(--muted)">Score &ge; ${m.thresholds.highly_from}: Highly Productive &middot; ${m.thresholds.fake_below}-${m.thresholds.highly_from - 1}: Moderately &middot; &lt; ${m.thresholds.fake_below}: Fake Productivity.</p></div>
      </div>
      <div class="note"><b>Honest note:</b> the training data is synthetic (generated from documented behaviour profiles plus noise) because real employee data is private. The scores show the pipeline works; they are not a measure of accuracy on real people. Use the result to start a conversation, never as the only basis for judging someone.</div>`;
  },

  async profile() {
    const h = await loadHistory(), s = h.map((r) => r.score);
    $("#page").innerHTML = `
      <div class="card profile-head"><div class="big">${icon("activity")}</div><div><h3>${esc(state.user.username)}</h3><p>${icon("briefcase")} Productivity Analyst</p></div></div>
      <div class="stats s3" style="margin-top:16px">
        ${stat("plain", "chart", "#3b82f6", h.length, "Total Analyses")}
        ${stat("plain", "award", "#a855f7", Math.round(avg(s)), "Average Score")}
        ${stat("plain", "award", "#22c55e", s.length ? Math.max(...s) : "-", "Best Score")}
      </div>
      <div class="card panel about" style="margin-top:16px"><h3 style="color:var(--ink)">${icon("user")} About</h3>
        <p>Welcome to your Fake Productivity Detector profile. This application analyzes your activity with a trained machine learning model, separates real output from busy-looking time, and gives data-driven suggestions.</p>
        <small>Academic Project &bull; Data Science &amp; Web Technologies &bull; Member since ${new Date(state.user.created_at).toLocaleDateString("en-US", { month: "long", year: "numeric" })}</small></div>`;
  },
};

// ------------------------------------------------------------------ boot / login
function setMode(mode) {
  state.mode = mode;
  $("#login-submit-text").textContent = mode === "login" ? "Sign In" : "Create Account";
  $("#mode-q").textContent = mode === "login" ? "New here?" : "Already have an account?";
  $("#mode-toggle").textContent = mode === "login" ? "Create account" : "Sign in";
  $("#lg-pass").autocomplete = mode === "login" ? "current-password" : "new-password";
  $("#login-error").textContent = "";
}

async function boot() {
  $("#logo-lg").innerHTML = icon("activity"); $("#logo-sm").innerHTML = icon("activity");
  hydrateIcons();
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
    $("#tab-user").hidden = t.dataset.tab !== "user"; $("#tab-google").hidden = t.dataset.tab !== "google";
  }));
  $("#toggle-pass").onclick = () => { const p = $("#lg-pass"); p.type = p.type === "password" ? "text" : "password"; };
  $("#mode-toggle").onclick = (e) => { e.preventDefault(); setMode(state.mode === "login" ? "register" : "login"); };
  $("#login-card").onsubmit = async (e) => {
    e.preventDefault(); const btn = $("#login-submit"); btn.disabled = true; $("#login-error").textContent = "";
    try {
      await api("POST", state.mode === "login" ? "/api/login" : "/api/register", { username: $("#lg-user").value, password: $("#lg-pass").value });
      state.user = (await api("GET", "/api/me")).user; $("#lg-pass").value = ""; showApp();
    } catch (err) { $("#login-error").textContent = err.message; } finally { btn.disabled = false; }
  };
  $("#logout-btn").onclick = async () => { await api("POST", "/api/logout"); state.user = null; location.hash = ""; showLogin(); };
  $("#menu-btn").onclick = () => document.body.classList.toggle("collapsed");
  window.addEventListener("hashchange", route);
  state.user = (await api("GET", "/api/me")).user;
  state.user ? showApp() : showLogin();
}
boot();
