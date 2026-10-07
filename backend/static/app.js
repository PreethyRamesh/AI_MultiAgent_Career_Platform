const $ = (sel) => document.querySelector(sel);

const state = { roadmap: null, missions: null, progress: null, tree: null, history: [] };

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

function renderProgress(p) {
  state.progress = p;
  $("#stat-xp").textContent = p.xp ?? 0;
  $("#stat-level").textContent = p.level ?? 1;
  $("#stat-streak").textContent = `${p.streak ?? 0}🔥`;
  const pct = p.completion_pct ?? 0;
  $("#stat-bar").style.width = `${pct}%`;
  $("#stat-pct").textContent = `${pct}% complete`;
}

function milestoneById(id) {
  if (!state.roadmap) return null;
  for (const phase of state.roadmap.phases) {
    for (const ms of phase.milestones) if (ms.id === id) return { ms, phase };
  }
  return null;
}

function renderRoadmap(r) {
  state.roadmap = r;
  const box = $("#roadmap-list");
  if (!r) { box.innerHTML = '<p class="empty">No roadmap yet — generate one in Setup.</p>'; return; }
  box.innerHTML = r.phases.map((phase, i) => `
    <div class="phase ${i === 0 ? "open" : ""}" data-phase="${phase.id}">
      <div class="phase-head" onclick="this.parentElement.classList.toggle('open')">
        <div>
          <h3>${i + 1}. ${esc(phase.title)}</h3>
          <div class="meta">${esc(phase.goal || "")}</div>
        </div>
        <span class="badge">${esc(phase.duration || "")}</span>
      </div>
      <div class="phase-body">
        ${phase.milestones.map((ms) => {
          const done = (state.progress?.completed_milestones || []).includes(ms.id);
          return `
          <div class="ms" style="${done ? "opacity:.55" : ""}">
            <h4>${done ? "✅ " : "📌 "}${esc(ms.title)} <span class="tag xp">+${ms.xp} XP</span></h4>
            <p>${esc(ms.details)}</p>
            <div class="tags">
              ${ms.skills.map((s) => `<span class="tag">${esc(s)}</span>`).join("")}
            </div>
            <div style="margin-top:8px">
              ${(ms.resources || []).map((r2) => r2.url
                ? `<a class="res" href="${esc(r2.url)}" target="_blank" rel="noopener">↗ ${esc(r2.title)}</a>`
                : `<span class="res">${esc(r2.title)}</span>`).join("")}
            </div>
          </div>`;
        }).join("")}
      </div>
    </div>`).join("");
}

function renderMissions(day) {
  state.missions = day;
  const box = $("#mission-list");
  if (!day || !day.items.length) {
    box.innerHTML = '<p class="empty">No missions yet — generate a roadmap first.</p>';
    return;
  }
  box.innerHTML = `<p class="hint">${day.date}</p>` + day.items.map((item) => `
    <div class="mission ${item.done ? "done" : ""}">
      <input type="checkbox" data-item="${item.id}" ${item.done ? "checked" : ""} />
      <div class="m-body">
        <div class="m-title">${esc(item.title)}</div>
        <div class="m-sub">+${item.xp} XP · ${esc(item.milestone_id || "daily")}</div>
      </div>
      <span class="badge ${item.type}">${item.type}</span>
    </div>`).join("");

  box.querySelectorAll("input[type=checkbox]").forEach((cb) => {
    cb.addEventListener("change", async () => {
      if (!cb.checked) return;
      try {
        const data = await api("/api/missions/complete", { method: "POST", body: { item_id: cb.dataset.item } });
        renderMissions(data.missions);
        renderProgress(data.progress);
        renderTree(data.tree);
        if (state.roadmap) renderRoadmap(state.roadmap);
      } catch (err) {
        cb.checked = false;
        alert(err.message);
      }
    });
  });
}

function renderTree(tree) {
  state.tree = tree;
  const grid = $("#tree-grid");
  if (!tree || !tree.nodes.length) {
    grid.innerHTML = '<p class="empty">Complete setup to grow your skill tree.</p>';
    return;
  }
  const icon = { completed: "✅", available: "🔓", locked: "🔒" };
  grid.innerHTML = tree.phases.map((ph) => {
    const nodes = tree.nodes.filter((n) => n.phase_id === ph.id);
    return `<div class="tree-col">
      <h3>${esc(ph.title)}</h3>
      ${nodes.map((n) => `
        <div class="node ${n.status}">
          <span class="status">${icon[n.status]} ${n.status}</span>
          <h4>${esc(n.title)}</h4>
          <div class="tags">${n.skills.map((s) => `<span class="tag">${esc(s)}</span>`).join("")}</div>
        </div>`).join("")}
    </div>`;
  }).join("");
}

function addMsg(text, who, thinking = false) {
  const div = document.createElement("div");
  div.className = `msg ${who}${thinking ? " thinking" : ""}`;
  div.textContent = text;
  $("#chat").appendChild(div);
  $("#chat").scrollTop = $("#chat").scrollHeight;
  return div;
}

function esc(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    $(`#tab-${tab.dataset.tab}`).classList.add("active");
  });
});

$("#setup-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = $("#btn-generate");
  const hint = $("#gen-hint");
  btn.disabled = true;
  hint.textContent = "Generating your personalized roadmap…";
  try {
    const body = {
      target_role: $("#f-role").value.trim(),
      current_skills: $("#f-skills").value.split(",").map((s) => s.trim()).filter(Boolean),
      skill_gaps: $("#f-gaps").value.split(",").map((s) => s.trim()).filter(Boolean),
      hours_per_week: Number($("#f-hours").value) || 7,
    };
    const data = await api("/api/roadmap", { method: "POST", body });
    renderRoadmap(data.roadmap);
    renderProgress(data.progress);
    const fresh = await api("/api/state");
    renderMissions(fresh.missions);
    renderTree(fresh.tree);
    hint.textContent = `Done! Roadmap built with ${data.source === "gemini" ? "Gemini AI 🤖" : "smart templates 🧩"}.`;
    document.querySelector('[data-tab="roadmap"]').click();
  } catch (err) {
    hint.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});

$("#chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#chat-text");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  addMsg(text, "user");
  state.history.push({ role: "user", content: text });
  const pending = addMsg("Thinking…", "bot", true);
  try {
    const data = await api("/api/mentor", { method: "POST", body: { message: text, history: state.history } });
    pending.remove();
    addMsg(data.reply, "bot");
    state.history.push({ role: "assistant", content: data.reply });
  } catch (err) {
    pending.remove();
    addMsg(`⚠️ ${err.message}`, "bot");
  }
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    $("#chat-text").value = chip.textContent;
    $("#chat-form").requestSubmit();
  });
});

(async function init() {
  try {
    const data = await api("/api/state");
    if (data.roadmap) renderRoadmap(data.roadmap);
    renderProgress(data.progress);
    renderMissions(data.missions);
    renderTree(data.tree);
    state.history = data.mentor_history || [];
  } catch (err) {
    console.error(err);
  }
})();
