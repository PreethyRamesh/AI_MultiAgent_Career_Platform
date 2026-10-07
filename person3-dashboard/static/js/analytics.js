async function getJSON(url){const r=await fetch(url);if(!r.ok)throw new Error(`${r.status} ${r.statusText}`);return r.json();}
async function loadAnalytics(){
  const summary=await getJSON("/api/progress/summary");
  const history=(await getJSON("/api/progress/history")).history||[];
  const state=summary.state,p=state.progress||{};
  document.getElementById("insightXp").textContent=Number(p.xp||0).toLocaleString();
  document.getElementById("insightStreak").textContent=`${p.streak||0} days`;
  document.getElementById("insightSnapshots").textContent=history.length;
  const skills=state.skill_tree||[];
  new Chart(document.getElementById("skillChart"),{
    type:"bar",
    data:{labels:skills.map(s=>s.name),datasets:[
      {label:"Current Coverage",data:skills.map(s=>s.current),borderRadius:7},
      {label:"Target",data:skills.map(s=>s.target),borderRadius:7}
    ]},
    options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,max:100}},plugins:{legend:{position:"bottom"}}}
  });
  const labels=history.map(x=>x.snapshot_date);
  new Chart(document.getElementById("phaseChart"),{
    type:"line",
    data:{labels,datasets:[{label:"Phase Progress",data:history.map(x=>x.phase_progress),tension:.35,fill:true,borderWidth:3,pointRadius:3}]},
    options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true,max:100}},plugins:{legend:{position:"bottom"}}}
  });
  new Chart(document.getElementById("hoursChart"),{
    type:"bar",
    data:{labels,datasets:[{label:"Hours Invested",data:history.map(x=>x.hours_invested),borderRadius:7}]},
    options:{responsive:true,maintainAspectRatio:false,scales:{y:{beginAtZero:true}},plugins:{legend:{position:"bottom"}}}
  });
}
document.addEventListener("DOMContentLoaded",async()=>{
  try{await getJSON("/api/progress/snapshot",{method:"POST"});await loadAnalytics();}
  catch(e){console.error(e);document.querySelectorAll(".chart-wrap").forEach(x=>x.innerHTML='<p class="muted">Unable to load analytics. Check the Person 2 /api/state connection.</p>');}
});
