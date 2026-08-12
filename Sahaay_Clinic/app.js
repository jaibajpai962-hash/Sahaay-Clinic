const DB_NAME="sahaayClinicDB", DB_VERSION=1;
let db, role="Health Worker", currentPatient=null;

const seedPatients=[
 {id:"SC-1001",name:"Ramesh Kumar",age:42,sex:"Male",language:"Hindi",symptoms:"Fever for 3 days, weakness",duration:"3 days",bp:"124/82",pulse:"82",spo2:"97",temp:"38.1",history:"No major history reported",meds:"None recorded",status:"Needs doctor review",risk:"amber",updated:"Today"},
 {id:"SC-1002",name:"Sunita Devi",age:58,sex:"Female",language:"Hindi",symptoms:"Routine follow-up",duration:"—",bp:"132/84",pulse:"76",spo2:"98",temp:"36.8",history:"Previous clinic visit",meds:"As per doctor record",status:"Doctor approved",risk:"green",updated:"Yesterday"}
];

function openDB(){
 return new Promise((resolve,reject)=>{
  const req=indexedDB.open(DB_NAME,DB_VERSION);
  req.onupgradeneeded=e=>{
   const d=e.target.result;
   if(!d.objectStoreNames.contains("patients")) d.createObjectStore("patients",{keyPath:"id"});
   if(!d.objectStoreNames.contains("queue")) d.createObjectStore("queue",{keyPath:"id",autoIncrement:true});
  };
  req.onsuccess=e=>{db=e.target.result;resolve(db)};
  req.onerror=()=>reject(req.error);
 });
}
function tx(store,mode="readonly"){return db.transaction(store,mode).objectStore(store)}
function getAll(store){return new Promise((res,rej)=>{const r=tx(store).getAll();r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)})}
function put(store,obj){return new Promise((res,rej)=>{const r=tx(store,"readwrite").put(obj);r.onsuccess=()=>res(obj);r.onerror=()=>rej(r.error)})}
async function seed(){const all=await getAll("patients");if(!all.length)for(const p of seedPatients)await put("patients",p)}

const app=document.getElementById("app");
const toast=document.getElementById("toast");
function showToast(msg){toast.textContent=msg;toast.classList.add("show");setTimeout(()=>toast.classList.remove("show"),2200)}
function nav(view){
 document.querySelectorAll(".nav-btn").forEach(b=>b.classList.toggle("active",b.dataset.view===view));
 render(view);
}
document.querySelectorAll(".nav-btn").forEach(b=>b.addEventListener("click",()=>nav(b.dataset.view)));
document.getElementById("roleBtn").onclick=()=>{role=role==="Health Worker"?"Doctor":"Health Worker";document.getElementById("roleBtn").textContent="Role: "+role;render("dashboard")};

function status(){
 const online=navigator.onLine;
 const badge=document.getElementById("networkBadge");
 badge.className="status "+(online?"online":"offline");
 badge.textContent=online?"● Online":"● Offline";
 document.getElementById("offlineNotice").classList.toggle("hidden",online);
}
window.addEventListener("online",()=>{status();showToast("Connection restored. Local records are ready to sync.")});
window.addEventListener("offline",()=>{status();showToast("Offline mode enabled.")});

function dashboard(){
 return `<div class="page-head"><div><div class="eyebrow">Sahaay Clinic</div><h1>Good day, ${role} 👋</h1><p class="muted">One simple workspace for rural care.</p></div><button class="btn" onclick="nav('intake')">+ New Patient</button></div>
 <div class="grid stats">
  <div class="card"><div class="stat-label">Patients today</div><div class="stat-number stat-accent">12</div></div>
  <div class="card"><div class="stat-label">Awaiting review</div><div class="stat-number stat-warn">4</div></div>
  <div class="card"><div class="stat-label">Urgent referrals</div><div class="stat-number stat-danger">1</div></div>
  <div class="card"><div class="stat-label">Saved offline</div><div class="stat-number">7</div></div>
 </div>
 <div class="grid two" style="margin-top:16px">
  <div class="grid two">
   <div class="action-card teal"><div><h3>New Patient Intake</h3><p>Capture symptoms, history, vitals and records in one short form.</p></div><button onclick="nav('intake')">Start intake →</button></div>
   <div class="action-card blue"><div><h3>Sahaay Triage</h3><p>Create a structured preliminary case summary without replacing a doctor.</p></div><button onclick="nav('triage')">Open triage →</button></div>
  </div>
  <div class="card"><div class="section-title"><h2>Care Gate</h2><span class="chip amber">Safety first</span></div><p class="muted">The frontend never makes a final diagnosis. Preliminary suggestions remain clearly separated from doctor approval.</p><div class="notice">If a case appears urgent, the interface directs the health worker toward professional medical care / referral rather than self-management.</div></div>
 </div>
 <div class="section-title"><h2>Recent patients</h2><button class="small-btn" onclick="nav('records')">View all</button></div>
 <div id="recentPatients" class="card"></div>`;
}
async function renderDashboard(){app.innerHTML=dashboard();const ps=await getAll("patients");document.getElementById("recentPatients").innerHTML=ps.slice(-5).reverse().map(patientRow).join("")||'<div class="empty">No patients yet.</div>'}
function patientRow(p){return `<div class="patient-row"><div><div class="patient-name">${esc(p.name)}</div><div class="muted">${p.id} • ${p.age} yrs • ${esc(p.symptoms||"No symptoms entered")}</div></div><div class="chips"><span class="chip ${p.risk==="red"?"red":p.risk==="amber"?"amber":"green"}">${esc(p.status||"Saved")}</span><button class="small-btn" onclick="openPatient('${p.id}')">Open</button></div></div>`}

function intake(){
 return `<div class="page-head"><div><div class="eyebrow">Module 1</div><h1>New Patient Intake</h1><p class="muted">Designed for quick entry at a village health centre.</p></div></div>
 <div class="card"><form id="patientForm" class="form-grid">
  <div class="field"><label>Patient name *</label><input name="name" required placeholder="e.g. Ramesh Kumar"></div>
  <div class="field"><label>Age *</label><input name="age" type="number" min="0" max="120" required></div>
  <div class="field"><label>Sex</label><select name="sex"><option>Female</option><option>Male</option><option>Other</option></select></div>
  <div class="field"><label>Preferred language</label><select name="language"><option>Hindi</option><option>English</option><option>Other</option></select></div>
  <div class="field full"><label>Symptoms & duration *</label><textarea name="symptoms" required placeholder="Describe what the patient reports and how long it has been present."></textarea></div>
  <div class="field"><label>Blood pressure</label><input name="bp" placeholder="e.g. 124/82"></div>
  <div class="field"><label>Pulse (bpm)</label><input name="pulse" placeholder="e.g. 82"></div>
  <div class="field"><label>Oxygen level (SpO₂ %)</label><input name="spo2" placeholder="e.g. 97"></div>
  <div class="field"><label>Temperature (°C)</label><input name="temp" placeholder="e.g. 37.2"></div>
  <div class="field full"><label>Basic medical history</label><textarea name="history" placeholder="Known conditions, previous visits, allergies, etc."></textarea></div>
  <div class="field full"><label>Existing prescriptions / medical reports</label><textarea name="meds" placeholder="Type a short note. Document/OCR upload can be connected by the backend later."></textarea></div>
  <div class="field full"><label>Photo / injury note</label><textarea name="imageNote" placeholder="Describe any image captured for the record."></textarea></div>
  <div class="form-actions full"><button type="reset" class="btn secondary">Clear</button><button class="btn">Save patient locally</button></div>
 </form></div>
 <div class="notice" style="margin-top:12px">Offline-first: this form is saved to IndexedDB on the device. No external API is called from this frontend prototype.</div>`;
}
async function savePatient(e){
 e.preventDefault();const f=new FormData(e.target);
 const p={id:"SC-"+Date.now().toString().slice(-6),name:f.get("name"),age:Number(f.get("age")),sex:f.get("sex"),language:f.get("language"),symptoms:f.get("symptoms"),duration:"Not separately recorded",bp:f.get("bp"),pulse:f.get("pulse"),spo2:f.get("spo2"),temp:f.get("temp"),history:f.get("history"),meds:f.get("meds"),imageNote:f.get("imageNote"),status:"Awaiting preliminary review",risk:"amber",updated:"Just now"};
 await put("patients",p);currentPatient=p;showToast("Patient saved on this device.");nav("triage");
}

function triage(){
 return `<div class="page-head"><div><div class="eyebrow">Module 2</div><h1>Sahaay Triage</h1><p class="muted">Structured preliminary support — not a diagnosis.</p></div></div>
 <div class="card"><div class="field"><label>Select patient</label><select id="triagePatient"></select></div><div id="triagePanel" style="margin-top:16px"></div></div>`;
}
async function renderTriage(){
 app.innerHTML=triage();const ps=await getAll("patients"),sel=document.getElementById("triagePatient");
 sel.innerHTML=ps.map(p=>`<option value="${p.id}">${esc(p.name)} — ${p.id}</option>`).join("");
 if(currentPatient)sel.value=currentPatient.id;
 const draw=()=>showTriage(sel.value);sel.onchange=draw;draw();
}
async function showTriage(id){
 const ps=await getAll("patients"),p=ps.find(x=>x.id===id);currentPatient=p;if(!p)return;
 const text=(p.symptoms||"").toLowerCase();
 let risk="amber", title="Doctor review recommended", message="The information entered needs review by a qualified clinician.";
 if(/unconscious|severe|emergency|chest pain|difficulty breathing|heavy bleeding/.test(text)){risk="red";title="Urgent professional assessment";message="Potentially serious symptoms were entered. The prototype does not attempt to manage this case independently; follow local emergency/referral protocol."}
 else if(/routine|follow-up|stable/.test(text)){risk="green";title="Routine review";message="No urgent keyword was detected by this simple demo rule. This is not a clinical assessment."}
 document.getElementById("triagePanel").innerHTML=`
 <div class="hero-strip"><div><h2>${esc(p.name)}</h2><div class="muted">${p.age} yrs • ${esc(p.language)} • ${esc(p.id)}</div></div><span class="chip ${risk==="red"?"red":risk==="amber"?"amber":"green"}">${title}</span></div>
 <div class="signal-grid">
  <div class="signal">Symptoms<strong>${esc(p.symptoms||"—")}</strong></div>
  <div class="signal">Vitals<strong>BP ${esc(p.bp||"—")} • SpO₂ ${esc(p.spo2||"—")}</strong></div>
  <div class="signal">History<strong>${esc(p.history||"—")}</strong></div>
  <div class="signal">Records<strong>${esc(p.meds||"—")}</strong></div>
 </div>
 <div class="risk-box ${risk}"><strong>Preliminary support</strong><p>${message}</p><div class="notice">AI/automation output in the final product must be labelled preliminary, explainable and unverified. Doctor approval is required before a medical decision is treated as final.</div></div>
 <div class="form-actions"><button class="btn secondary" onclick="nav('records')">View patient record</button><button class="btn" onclick="sendToQueue('${p.id}','${risk}')">Add to doctor queue</button></div>`;
}

async function sendToQueue(id,risk){await tx("queue","readwrite").add({patientId:id,risk,status:"Waiting for doctor",created:new Date().toLocaleString()});showToast("Case added to care queue.");nav("queue")}

async function records(){
 const ps=await getAll("patients");
 return `<div class="page-head"><div><div class="eyebrow">Module 3</div><h1>Patient Records</h1><p class="muted">Local patient snapshots for low-connectivity clinics.</p></div><button class="btn" onclick="nav('intake')">+ Add patient</button></div>
 <div class="card"><div class="table-wrap"><table class="table"><thead><tr><th>Patient</th><th>Age</th><th>Symptoms</th><th>Risk</th><th>Status</th><th></th></tr></thead><tbody>${ps.map(p=>`<tr><td><strong>${esc(p.name)}</strong><br><small>${p.id}</small></td><td>${p.age}</td><td>${esc(p.symptoms||"—")}</td><td><span class="chip ${p.risk==="red"?"red":p.risk==="amber"?"amber":"green"}">${p.risk}</span></td><td>${esc(p.status||"Saved")}</td><td><button class="small-btn" onclick="openPatient('${p.id}')">Open</button></td></tr>`).join("")}</tbody></table></div></div>`;
}
async function openPatient(id){currentPatient=(await getAll("patients")).find(p=>p.id===id);nav("triage")}

async function queue(){
 const qs=await getAll("queue"),ps=await getAll("patients");
 const cards=qs.slice().reverse().map(q=>{const p=ps.find(x=>x.id===q.patientId)||{};return `<div class="card queue-card ${q.risk==="red"?"urgent":""}" style="margin-bottom:10px"><div class="patient-row"><div><div class="patient-name">${esc(p.name||"Unknown")}</div><div class="muted">${p.id||""} • ${q.created}</div></div><span class="chip ${q.risk==="red"?"red":"amber"}">${q.risk==="red"?"Urgent":"Review"}</span></div><p>${esc(p.symptoms||"No symptom summary")}</p><button class="btn small" onclick="selectForReview('${p.id}')">Open doctor review</button></div>`}).join("");
 return `<div class="page-head"><div><div class="eyebrow">Module 4</div><h1>Care Queue</h1><p class="muted">Walk-in cases and digitally captured cases meet in one simple queue.</p></div></div>${cards||'<div class="card empty">No cases in the queue yet. Add a patient to triage first.</div>'}`;
}
function selectForReview(id){currentPatient=null;getAll("patients").then(ps=>{currentPatient=ps.find(p=>p.id===id);nav("review")})}

function review(){
 return `<div class="page-head"><div><div class="eyebrow">Module 5</div><h1>Doctor Review Gate</h1><p class="muted">The final clinical decision belongs to the qualified doctor.</p></div></div>
 <div id="reviewContent"></div>`;
}
async function renderReview(){
 app.innerHTML=review();const ps=await getAll("patients");const p=currentPatient||ps[0];
 if(!p){document.getElementById("reviewContent").innerHTML='<div class="card empty">No patient selected.</div>';return}
 document.getElementById("reviewContent").innerHTML=`<div class="grid two">
 <div class="card"><div class="section-title"><h2>Patient summary</h2><span class="chip amber">AI preliminary</span></div><div class="signal-grid"><div class="signal">Name<strong>${esc(p.name)}</strong></div><div class="signal">Age<strong>${p.age}</strong></div><div class="signal">Vitals<strong>BP ${esc(p.bp||"—")} / SpO₂ ${esc(p.spo2||"—")}</strong></div><div class="signal">Symptoms<strong>${esc(p.symptoms||"—")}</strong></div></div><div class="notice" style="margin-top:14px">Any AI-generated summary, OCR output or speech transcription should be treated as unverified until reviewed.</div></div>
 <div class="card"><div class="section-title"><h2>Doctor decision</h2><span class="chip green">Verified layer</span></div><div class="field"><label>Doctor note</label><textarea id="doctorNote" placeholder="Enter the clinician's assessment / approved plan."></textarea></div><div class="form-actions"><button class="btn secondary" onclick="saveReview('${p.id}','needs-referral')">Refer / escalate</button><button class="btn" onclick="saveReview('${p.id}','doctor-approved')">Approve case</button></div></div>
 </div>`;
}
async function saveReview(id,status){
 const ps=await getAll("patients"),p=ps.find(x=>x.id===id);if(!p)return;p.status=status==="doctor-approved"?"Doctor approved":"Referral required";p.doctorNote=document.getElementById("doctorNote").value;p.updated="Just now";await put("patients",p);showToast("Doctor decision saved locally.");nav("records");
}

function esc(v){return String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}

async function render(view="dashboard"){
 status();
 if(view==="dashboard")await renderDashboard();
 else if(view==="intake"){app.innerHTML=intake();document.getElementById("patientForm").onsubmit=savePatient}
 else if(view==="records")app.innerHTML=await records();
 else if(view==="triage")await renderTriage();
 else if(view==="queue")app.innerHTML=await queue();
 else if(view==="review")await renderReview();
}
(async()=>{await openDB();await seed();if("serviceWorker"in navigator)navigator.serviceWorker.register("sw.js").catch(()=>{});render()})();
