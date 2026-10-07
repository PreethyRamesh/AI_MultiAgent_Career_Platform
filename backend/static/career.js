/* ==========================================================================
   AI Career Analysis module frontend (Person 1)
   Vanilla JS, mirrors the shared app.js conventions (api/esc helpers).
   ========================================================================== */

const $ = (sel) => document.querySelector(sel);

const state = {
  profile: null,
  resume: { content: "", result: null },
  projects: { items: [], result: null },
  coursework: { items: [], result: null },
  job: { title: "", description: "", result: null },
  analysis: null,
};

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

function esc(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function chips(items, cls = "") {
  if (!items || !items.length) return '<span class="empty">None</span>';
  return items.map((i) => `<span class="chip ${cls}">${esc(i)}</span>`).join(" ");
}

function levelDots(level) {
  const n = Math.max(0, Math.min(5, level || 0));
  return `<span class="level-dots">${Array.from({ length: 5 }, (_, i) =>
    `<span class="dot ${i < n ? "on" : ""}"></span>`).join("")}</span>`;
}

function statusBadge(status) {
  const map = {
    has: ["green", "✅ Has"],
    improving: ["amber", "🟠 Improving"],
    missing: ["red", "❌ Missing"],
  };
  const [cls, label] = map[status] || ["neutral", status];
  return `<span class="badge ${cls}">${label}</span>`;
}

/* --------------------------------------------------------------------------
 * Navigation
 * -------------------------------------------------------------------------- */

function showPanel(name) {
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.panel === name));
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("active", p.id === `panel-${name}`));
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => showPanel(btn.dataset.panel));
});

/* --------------------------------------------------------------------------
 * Overview + topbar
 * -------------------------------------------------------------------------- */

function renderTopbar() {
  const a = state.analysis;
  $("#ov-score").textContent = a?.match ? `${a.match.score}%` : "–";
  $("#ov-skills").textContent = a?.assessment?.summary?.total_skills ?? 0;
  $("#ov-has").textContent = a?.assessment?.summary?.has_count ?? 0;
  const gapCount = (a?.gaps)
    ? (a.gaps.improving?.length || 0) + (a.gaps.missing?.length || 0)
    : 0;
  $("#ov-gap").textContent = gapCount;
}

function renderOverview() {
  const a = state.analysis;
  const p = state.profile;

  if (!a) {
    $("#ov-score-big").textContent = "—";
    $("#ov-score-bar").style.width = "0%";
    $("#ov-grade").textContent = "No analysis yet";
    $("#ov-skills-big").textContent = "0";
    $("#ov-has-sub").textContent = "0 strong · 0 improving";
    $("#ov-strength").textContent = "—";
    $("#ov-categories").textContent = "—";
    $("#ov-target").textContent = "—";
    $("#ov-goal").textContent = "—";
    $("#ov-report").style.display = "none";
    return;
  }

  const s = a.assessment?.summary || {};
  $("#ov-score-big").textContent = a.match ? `${a.match.score}%` : "—";
  $("#ov-score-bar").style.width = `${a.match?.score || 0}%`;
  $("#ov-grade").textContent = a.match ? `${a.match.grade} match for ${esc(a.job?.title_hint || state.job.title || "target role")}` : "Add a job description to score";
  $("#ov-skills-big").textContent = s.total_skills ?? 0;
  $("#ov-has-sub").textContent = `${s.has_count ?? 0} strong · ${s.improving_count ?? 0} improving`;
  $("#ov-strength").textContent = s.strongest || "—";
  $("#ov-categories").textContent = (s.top_categories || []).join(" · ") || "—";
  $("#ov-target").textContent = p?.target_job_role || "—";
  $("#ov-goal").textContent = p?.career_goal || "Set a career goal in Profile";

  const rec = a.recommendations?.[0];
  $("#ov-report").style.display = "block";
  $("#ov-report-chips").innerHTML = [
    `<span class="badge neutral">Score ${a.match ? a.match.score + "%" : "n/a"}</span>`,
    `<span class="badge green">${s.has_count || 0} strong skills</span>`,
    `<span class="badge amber">${(a.gaps?.improving || []).length} improving</span>`,
    `<span class="badge red">${(a.gaps?.missing || []).length} missing</span>`,
    rec ? `<span class="badge neutral">🎯 Best fit: ${esc(rec.role)} (${rec.match_pct}%)</span>` : "",
  ].filter(Boolean).join(" ");
  renderTopbar();
}

/* --------------------------------------------------------------------------
 * Resume
 * -------------------------------------------------------------------------- */

function renderResume(r) {
  const box = $("#resume-results");
  if (!r) { box.innerHTML = ""; return; }
  const ai = r.ai_source === "gemini"
    ? '<span class="badge neutral">✨ refined by Gemini</span>'
    : '<span class="badge neutral">rule-based extraction</span>';
  const kvCard = (title, list) => `
    <div class="card res-section">
      <h3>${title}</h3>
      ${list && list.length
        ? `<ul>${list.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>`
        : '<p class="empty">Not detected</p>'}
    </div>`;
  box.innerHTML = `
    <div class="result-grid">
      ${kvCard("🎓 Education", r.education)}
      ${kvCard("💻 Projects", r.projects)}
      ${kvCard("💼 Experience", r.experience)}
      ${kvCard("🏅 Certifications", r.certifications)}
    </div>
    <div class="card">
      <h3>Extracted skills ${ai}</h3>
      <div class="chips">
        ${(r.matched_skills || []).map((s) =>
          `<span class="chip ${s.category === "Soft Skills" ? "soft" : ""}" title="${esc(s.category)} · ${s.count} mention(s)">${esc(s.name)} <small>${esc(s.category)}</small></span>`).join(" ")}
      </div>
    </div>`;
}

/* --------------------------------------------------------------------------
 * Projects & coursework dynamic lists
 * -------------------------------------------------------------------------- */

function renderProjectRows() {
  const box = $("#project-rows");
  box.innerHTML = state.projects.items.map((p, i) => `
    <div class="entry-card">
      <div class="entry-head"><label>Project #${i + 1}</label>
        <button class="btn ghost" data-remove-project="${i}">Remove</button></div>
      <div class="row"><input data-p-title="${i}" value="${esc(p.title)}" placeholder="Project title" /></div>
      <div class="row"><textarea data-p-desc="${i}" rows="3" placeholder="What did you build? Tech used…">${esc(p.description)}</textarea></div>
    </div>`).join("");
  box.querySelectorAll("[data-remove-project]").forEach((b) =>
    b.addEventListener("click", () => { state.projects.items.splice(Number(b.dataset.removeProject), 1); renderProjectRows(); }));
  box.querySelectorAll("[data-p-title]").forEach((inp) =>
    inp.addEventListener("input", () => { state.projects.items[Number(inp.dataset.pTitle)].title = inp.value; }));
  box.querySelectorAll("[data-p-desc]").forEach((inp) =>
    inp.addEventListener("input", () => { state.projects.items[Number(inp.dataset.pDesc)].description = inp.value; }));
}

function renderCourseRows() {
  const box = $("#course-rows");
  box.innerHTML = state.coursework.items.map((c, i) => `
    <div class="entry-card">
      <div class="entry-head"><label>Subject #${i + 1}</label>
        <button class="btn ghost" data-remove-course="${i}">Remove</button></div>
      <div class="row"><input data-c-name="${i}" value="${esc(c.name)}" placeholder="Subject name, e.g. DBMS" /></div>
      <div class="row"><input data-c-desc="${i}" value="${esc(c.description)}" placeholder="Optional: brief description" /></div>
    </div>`).join("");
  box.querySelectorAll("[data-remove-course]").forEach((b) =>
    b.addEventListener("click", () => { state.coursework.items.splice(Number(b.dataset.removeCourse), 1); renderCourseRows(); }));
  box.querySelectorAll("[data-c-name]").forEach((inp) =>
    inp.addEventListener("input", () => { state.coursework.items[Number(inp.dataset.cName)].name = inp.value; }));
  box.querySelectorAll("[data-c-desc]").forEach((inp) =>
    inp.addEventListener("input", () => { state.coursework.items[Number(inp.dataset.cDesc)].description = inp.value; }));
}

function renderProjectsResults(r) {
  const box = $("#projects-results");
  box.innerHTML = (r?.projects || []).map((p) => `
    <div class="card">
      <h4>${esc(p.title)}</h4>
      ${p.summary ? `<p class="muted">${esc(p.summary)}</p>` : ""}
      <div class="tags">${(p.skills || []).map((s) => `<span class="tag">${esc(s)}</span>`).join("") || '<span class="empty">No technical skills detected</span>'}</div>
    </div>`).join("") || '<p class="empty">No projects analyzed yet.</p>';
}

function renderCoursesResults(r) {
  const box = $("#courses-results");
  box.innerHTML = (r?.courses || []).map((c) => `
    <div class="card">
      <h4>${esc(c.name)}</h4>
      <div class="tags">${(c.skills || []).map((s) => `<span class="tag">${esc(s)}</span>`).join("") || '<span class="empty">No skills mapped</span>'}</div>
    </div>`).join("") || '<p class="empty">No coursework analyzed yet.</p>';
}

/* --------------------------------------------------------------------------
 * Skill profile
 * -------------------------------------------------------------------------- */

function renderSkillProfile(a) {
  if (!a) return;
  const s = a.assessment || {};
  $("#sk-strength-count").textContent = (s.strengths || []).length;
  $("#sk-strengths").innerHTML = (s.strengths || []).length
    ? (s.strengths || []).map((st) => `
      <div class="kv"><b>${esc(st.skill)}</b><span class="badge green">${esc(st.category)}</span>${levelDots(st.level)}</div>`).join("")
    : '<p class="empty">No strong skills yet — add projects, coursework or update your profile.</p>';

  $("#sk-categories").innerHTML = (s.categories || []).length
    ? (s.categories || []).map((c) => `
      <div class="category-item">
        <div class="category-head">
          <span><b>${esc(c.category)}</b> · ${c.skill_count} skill(s)</span>
          <span class="muted">avg ${c.avg_level}/5</span>
        </div>
        <div class="bar"><div class="bar-fill" style="width:${c.pct}%"></div></div>
        <div class="category-tags">${(c.skills || []).map((sk) => `<span class="tag">${esc(sk)}</span>`).join("")}</div>
      </div>`).join("")
    : '<p class="empty">No skills detected yet.</p>';

  $("#sk-all").innerHTML = chips((s.skills || []).map((k) => `${k.skill} · L${k.level}`));
}

/* --------------------------------------------------------------------------
 * Target job
 * -------------------------------------------------------------------------- */

function renderJob(j) {
  const box = $("#job-results");
  if (!j) { box.innerHTML = ""; return; }
  const ai = j.ai_source === "gemini"
    ? '<span class="badge neutral">✨ refined by Gemini</span>'
    : '<span class="badge neutral">rule-based extraction</span>';
  box.innerHTML = `
    <div class="result-grid">
      <div class="card">
        <h3>Required skills ${ai}</h3>
        <div class="chips">${(j.required_skills || []).map((s) =>
          `<span class="chip" title="${esc(s.category)}">${esc(s.name)} <small>×${s.count}</small></span>`).join(" ") || '<span class="empty">None detected</span>'}</div>
      </div>
      <div class="card">
        <h3>Soft skills</h3>
        <div class="chips">${(j.soft_skills || []).map((s) => `<span class="chip soft">${esc(s.name)}</span>`).join(" ") || '<span class="empty">None detected</span>'}</div>
        <h3 style="margin-top:14px">Technologies</h3>
        <div class="chips">${chips(j.technologies)}</div>
      </div>
      <div class="card">
        <h3>Qualifications</h3>
        ${(j.qualifications || []).length
          ? `<ul>${j.qualifications.map((q) => `<li>${esc(q)}</li>`).join("")}</ul>`
          : '<p class="empty">None detected</p>'}
      </div>
    </div>`;
}

/* --------------------------------------------------------------------------
 * Gaps / Match / Recommendations / Mapping
 * -------------------------------------------------------------------------- */

function renderGaps(g) {
  if (!g) return;
  $("#gap-has-count").textContent = g.has.length;
  $("#gap-improving-count").textContent = g.improving.length;
  $("#gap-missing-count").textContent = g.missing.length;
  $("#gap-has").innerHTML = chips(g.has.map((h) => `${h.skill} (L${h.level})`), "soft");
  $("#gap-improving").innerHTML = chips(g.improving.map((i) => `${i.skill} (L${i.level})`));
  $("#gap-missing").innerHTML = chips(g.missing.map((m) => m.skill));
  $("#gap-extra").innerHTML = chips(g.extra_skills, "soft");
}

function renderMatch(m) {
  if (!m) return;
  $("#match-score").textContent = `${m.score}%`;
  $("#match-grade").textContent = m.grade;
  $("#match-bar").style.width = `${m.score}%`;

  $("#match-factors").innerHTML = (m.factors || []).map((f) => `
    <div class="factor-row">
      <span class="factor-name">${esc(f.name)}</span>
      <span class="factor-val">${Math.round(f.value * 100)}% <small>(weight ${f.weight})</small></span>
      <span class="factor-impact ${f.impact === "positive" ? "badge green" : f.impact === "negative" ? "badge red" : "badge neutral"}">${f.impact}</span>
    </div>`).join("");

  $("#match-matched").innerHTML = chips(m.matched_skills, "soft");
  $("#match-missing").innerHTML = chips(m.missing_skills);
}

function renderRecs(recs) {
  const box = $("#rec-list");
  box.innerHTML = (recs || []).map((r) => `
    <div class="card rec-card">
      <div class="rec-head">
        <h3>${esc(r.role)} ${r.goal_match ? '<span class="rec-goal">⭐ matches your stated goal</span>' : ""}</h3>
        <span class="badge ${r.match_pct >= 60 ? "green" : r.match_pct >= 40 ? "amber" : "red"}">${r.match_pct}% fit</span>
      </div>
      <div class="bar"><div class="bar-fill" style="width:${r.match_pct}%;background:linear-gradient(90deg,var(--accent),var(--accent2))"></div></div>
      <p class="rec-reason">${esc(r.summary)}</p>
      <p class="rec-reason"><b>Why it fits:</b> you have <b>${r.matched.length}</b> of ${r.matched.length + r.missing.length} key skills
        (${esc(r.matched.slice(0, 5).join(", ") || "none yet")})
        ${r.missing.length ? `· missing: ${esc(r.missing.slice(0, 5).join(", "))}` : "· all key skills covered! 🎉"}</p>
      <div class="rec-tags">
        <span class="badge neutral">Have: ${r.matched.length}</span>
        <span class="badge missing">Missing: ${r.missing.length}</span>
      </div>
    </div>`).join("") || '<p class="empty">Run the analysis to get recommendations.</p>';
}

function renderMapping(mm) {
  const box = $("#mapping-list");
  box.innerHTML = (mm?.mappings || []).map((m) => `
    <div class="map-row">
      <span class="map-req">${esc(m.requirement)} <small class="muted">${esc(m.category)}</small></span>
      <span>${statusBadge(m.status)}</span>
      <span class="map-src">${(m.satisfied_by || []).length
        ? `<ul>${m.satisfied_by.map((s) => `<li>${esc(s.label)} <small>(+${s.weight})</small></li>`).join("")}</ul>`
        : '<span class="empty">—</span>'}</span>
      <span class="map-note">${esc(m.note)}</span>
    </div>`).join("") || '<p class="empty">Add a job description and run the analysis.</p>';
}

/* --------------------------------------------------------------------------
 * Full analysis render
 * -------------------------------------------------------------------------- */

function renderAnalysis() {
  const a = state.analysis;
  if (!a) return;
  renderOverview();
  renderSkillProfile(a);
  renderGaps(a.gaps);
  renderMatch(a.match);
  renderRecs(a.recommendations);
  renderMapping(a.mapping);
  renderTopbar();
}

/* --------------------------------------------------------------------------
 * Wiring
 * -------------------------------------------------------------------------- */

$("#profile-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const hint = $("#profile-hint");
  const body = {
    name: $("#f-name").value.trim(),
    degree: $("#f-degree").value.trim(),
    year_of_study: $("#f-year").value.trim(),
    current_skills: $("#f-skills").value.split(",").map((s) => s.trim()).filter(Boolean),
    target_job_role: $("#f-target").value.trim(),
    career_goal: $("#f-goal").value.trim(),
  };
  try {
    const data = await api("/api/career/profile", { method: "POST", body });
    state.profile = data.profile;
    hint.textContent = "✅ Profile saved.";
    renderOverview();
  } catch (err) {
    hint.textContent = err.message;
  }
});

$("#btn-resume").addEventListener("click", async () => {
  const btn = $("#btn-resume");
  const hint = $("#resume-hint");
  const content = $("#ta-resume").value.trim();
  if (!content) { hint.textContent = "Paste or upload your resume first."; return; }
  btn.disabled = true;
  hint.textContent = "Analyzing resume…";
  try {
    const r = await api("/api/career/resume", { method: "POST", body: { content } });
    state.resume = { content, result: r };
    renderResume(r);
    hint.textContent = "Done.";
    showPanel("resume");
  } catch (err) {
    hint.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("#file-resume").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => { $("#ta-resume").value = String(reader.result || ""); };
  reader.readAsText(file);
});

$("#btn-add-project").addEventListener("click", () => {
  state.projects.items.push({ title: "", description: "" });
  renderProjectRows();
});

$("#btn-projects").addEventListener("click", async () => {
  const hint = $("#projects-hint");
  const items = state.projects.items.filter((p) => p.title.trim() || p.description.trim());
  if (!items.length) { hint.textContent = "Add at least one project."; return; }
  const btn = $("#btn-projects");
  btn.disabled = true;
  hint.textContent = "Analyzing projects…";
  try {
    const r = await api("/api/career/projects", { method: "POST", body: { projects: items } });
    state.projects.result = r;
    renderProjectsResults(r);
    hint.textContent = "Done.";
    showPanel("projects");
  } catch (err) {
    hint.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("#btn-add-course").addEventListener("click", () => {
  state.coursework.items.push({ name: "", description: "" });
  renderCourseRows();
});

$("#btn-courses").addEventListener("click", async () => {
  const hint = $("#courses-hint");
  const items = state.coursework.items.filter((c) => c.name.trim());
  if (!items.length) { hint.textContent = "Add at least one subject."; return; }
  const btn = $("#btn-courses");
  btn.disabled = true;
  hint.textContent = "Analyzing coursework…";
  try {
    const r = await api("/api/career/coursework", { method: "POST", body: { courses: items } });
    state.coursework.result = r;
    renderCoursesResults(r);
    hint.textContent = "Done.";
    showPanel("coursework");
  } catch (err) {
    hint.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("#btn-job").addEventListener("click", async () => {
  const hint = $("#job-hint");
  const description = $("#ta-job").value.trim();
  if (!description) { hint.textContent = "Paste a job description first."; return; }
  const btn = $("#btn-job");
  btn.disabled = true;
  hint.textContent = "Analyzing job description…";
  try {
    const j = await api("/api/career/job", { method: "POST", body: { title: $("#f-job-title").value.trim(), description } });
    state.job = { title: $("#f-job-title").value.trim(), description, result: j };
    renderJob(j);
    hint.textContent = "Done.";
    showPanel("job");
  } catch (err) {
    hint.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("#btn-analysis").addEventListener("click", async () => {
  const btn = $("#btn-analysis");
  const hint = $("#analysis-hint");
  btn.disabled = true;
  hint.textContent = "Running full analysis…";
  try {
    const a = await api("/api/career/analyze", { method: "POST", body: {} });
    state.analysis = a;
    renderAnalysis();
    hint.textContent = "✅ Analysis complete.";
    showPanel("overview");
  } catch (err) {
    hint.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("#btn-send-roadmap").addEventListener("click", async () => {
  const btn = $("#btn-send-roadmap");
  const hint = $("#analysis-hint");
  btn.disabled = true;
  hint.textContent = "Publishing skill gaps to the Learning Roadmap…";
  try {
    const gaps = await api("/api/career/skill-gaps", { method: "POST" });
    if (!gaps.target_role) throw new Error("Set a target job role first.");
    await api("/api/roadmap", {
      method: "POST",
      body: { ...gaps, hours_per_week: 7 },
    });
    hint.innerHTML = "✅ Skill gaps published to the Learning Roadmap — open the <a href='/' style='color:var(--accent)'>Learning Hub</a> to continue.";
  } catch (err) {
    hint.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("#btn-reset").addEventListener("click", async () => {
  if (!confirm("Reset all career analysis data?")) return;
  await api("/api/career/reset", { method: "POST" });
  location.reload();
});

/* --------------------------------------------------------------------------
 * Init: restore saved state
 * -------------------------------------------------------------------------- */

(async function init() {
  try {
    const data = await api("/api/career/state");
    if (data.profile) {
      state.profile = data.profile;
      $("#f-name").value = data.profile.name || "";
      $("#f-degree").value = data.profile.degree || "";
      $("#f-year").value = data.profile.year_of_study || "";
      $("#f-skills").value = (data.profile.current_skills || []).join(", ");
      $("#f-target").value = data.profile.target_job_role || "";
      $("#f-goal").value = data.profile.career_goal || "";
    }
    if (data.resume) {
      state.resume = data.resume;
      $("#ta-resume").value = data.resume.content || "";
      renderResume(data.resume.result);
    }
    if (data.projects) {
      state.projects = data.projects;
      renderProjectRows();
      renderProjectsResults(data.projects.result);
    }
    if (data.coursework) {
      state.coursework = data.coursework;
      renderCourseRows();
      renderCoursesResults(data.coursework.result);
    }
    if (data.job) {
      state.job = data.job;
      $("#f-job-title").value = data.job.title || "";
      $("#ta-job").value = data.job.description || "";
      renderJob(data.job.result);
    }
    if (data.analysis) {
      state.analysis = data.analysis;
      renderAnalysis();
    } else {
      renderOverview();
      $("#resume-results").innerHTML = '<p class="empty">Paste your resume and analyze it.</p>';
    }
  } catch (err) {
    console.error(err);
  }
})();

// keep the shared single-page-app interplay clean in case of leftover handlers
document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));