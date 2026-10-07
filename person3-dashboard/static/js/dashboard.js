async function getJSON(url, options={}) {
  const r = await fetch(url, options);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}
function text(id, value) { const e=document.getElementById(id); if(e)e.textContent=value; }
function streakMessage(n) {
  if(n<=0) return "Start your streak today";
  if(n<3) return "Great start — keep going";
  if(n<7) return "You're building momentum";
  if(n<30) return "Amazing consistency";
  return "Legendary consistency";
}
function renderAchievements(items) {
  const grid=document.getElementById("achievementGrid");
  const earned=items.filter(x=>x.earned).length;
  text("achievementCount", `${earned} / ${items.length}`);
  grid.innerHTML=items.map(x=>`
    <article class="achievement-card ${x.earned?"earned":"locked"}">
      <div class="achievement-icon">${x.icon}</div><h4>${x.name}</h4>
      <p>${x.description}</p><span class="earned-label">${x.earned?"✓ EARNED":"🔒 LOCKED"}</span>
    </article>`).join("");
}
async function loadDashboard() {
  const summary=await getJSON("/api/progress/summary");
  const state=summary.state, p=state.progress||{}, completion=Number(p.completion_pct||0);
  text("role",state.role||"Learner"); text("xp",Number(p.xp||0).toLocaleString());
  text("level",p.level||1); text("streak",p.streak||0); text("streakBig",p.streak||0);
  text("streakMessage",streakMessage(Number(p.streak||0)));
  text("completion",`${completion}%`); text("completionSmall",`${completion}%`);
  text("heroCompletion",`${completion}%`);
  document.getElementById("progressBar").style.width=`${Math.min(100,Math.max(0,completion))}%`;
  document.querySelector(".hero-ring").style.background=`conic-gradient(#fff ${completion*3.6}deg,rgba(255,255,255,.28) 0deg)`;
  const mission=summary.next_mission;
  text("missionTitle",mission?mission.title:"All missions complete 🎉");
  text("nextMissionText",mission?`Your next mission is “${mission.title}”. Complete it to keep the roadmap moving.`:"Excellent work — all currently available missions are complete.");
  await getJSON("/api/progress/snapshot",{method:"POST"});
  renderAchievements((await getJSON("/api/achievements")).achievements);
}
document.getElementById("refreshBtn").addEventListener("click",async()=>{
  const b=document.getElementById("refreshBtn"); b.textContent="Refreshing…";
  try{await loadDashboard();}catch(e){console.error(e);alert("Unable to refresh. Check Person 2 /api/state.");}
  finally{b.textContent="↻ Refresh";}
});
document.addEventListener("DOMContentLoaded",async()=>{
  try{await loadDashboard();}catch(e){console.error(e);text("role","Backend connection required");text("nextMissionText","Start Person 2 or enable DEMO_MODE.");}
});
