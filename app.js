/* JARVIS v3.0 — Compact AI Command Center */
const API = "/api", $ = id => document.getElementById(id);

// ── State ───────────────────────────────────────────
const S = {
  token: localStorage.getItem("jarvis_token"),
  user: JSON.parse(localStorage.getItem("jarvis_user") || "null"),
  sessionToken: localStorage.getItem("jarvis_session_token"),
  isListening: false, cmdCount: 0, chatCount: 0, acIdx: -1,
  currentSection: "dashboard", historyCache: [], recognition: null,
  inputHistory: JSON.parse(localStorage.getItem("jarvis_input_history") || "[]"),
  inputHistoryIdx: -1,
  settings: JSON.parse(localStorage.getItem("jarvis_settings") || JSON.stringify(
    { tts: true, rate: 1.0, lang: "en-US", autoswitch: true, notifications: false, autocomplete: true }
  )),
};

// ── Suggestions ─────────────────────────────────────
const SUGGESTIONS = [
  { text:"weather in Delhi",icon:"🌤️",tag:"weather" },{ text:"weather in Mumbai",icon:"🌤️",tag:"weather" },
  { text:"translate hello to Spanish",icon:"🌍",tag:"translate" },{ text:"translate good morning to French",icon:"🌍",tag:"translate" },
  { text:"define serendipity",icon:"📖",tag:"define" },{ text:"define ephemeral",icon:"📖",tag:"define" },
  { text:"convert 100 km to miles",icon:"🔄",tag:"convert" },{ text:"convert 37 celsius to fahrenheit",icon:"🔄",tag:"convert" },
  { text:"flip a coin",icon:"🪙",tag:"fun" },{ text:"roll a dice",icon:"🎲",tag:"fun" },
  { text:"what is the time",icon:"🕐",tag:"time" },{ text:"what is today's date",icon:"📅",tag:"date" },
  { text:"system info",icon:"💻",tag:"system" },{ text:"battery status",icon:"🔋",tag:"system" },
  { text:"disk usage",icon:"💾",tag:"system" },{ text:"my ip address",icon:"🌐",tag:"system" },
  { text:"take a screenshot",icon:"📸",tag:"system" },{ text:"volume up",icon:"🔊",tag:"system" },
  { text:"volume down",icon:"🔉",tag:"system" },{ text:"mute",icon:"🔇",tag:"system" },
  { text:"lock screen",icon:"🔒",tag:"system" },{ text:"open youtube",icon:"🖥️",tag:"apps" },
  { text:"open github",icon:"🖥️",tag:"apps" },{ text:"open spotify",icon:"🖥️",tag:"apps" },
  { text:"open gmail",icon:"🖥️",tag:"apps" },{ text:"open notepad",icon:"🖥️",tag:"apps" },
  { text:"search for AI news",icon:"🔍",tag:"search" },{ text:"play Shape of You",icon:"🎵",tag:"media" },
  { text:"tell me a joke",icon:"😄",tag:"fun" },{ text:"give me a quote",icon:"💬",tag:"fun" },
  { text:"set a reminder to call mom",icon:"⏰",tag:"reminder" },{ text:"set a timer for 5 minutes",icon:"⏱️",tag:"timer" },
  { text:"create a note",icon:"📝",tag:"notes" },{ text:"list files",icon:"📁",tag:"files" },
  { text:"git status",icon:"🛠️",tag:"dev" },{ text:"help",icon:"❓",tag:"help" },
  { text:"shutdown",icon:"🔌",tag:"power" },{ text:"restart",icon:"🔌",tag:"power" },
  { text:"what is 25 times 4",icon:"🧮",tag:"calc" },
];

// ── Init ────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  if (S.token && S.user) showMain();
  initSpeech(); initParticles("auth-particles"); initClock(); loadSettings();
  document.addEventListener("keydown", e => {
    if (e.ctrlKey && e.code === "Space") { e.preventDefault(); toggleListening(); }
    if (e.key === "Escape") { if (S.isListening) stopListening(); hideAC(); }
    if ((e.key==="ArrowUp"||e.key==="ArrowDown") && document.activeElement===$("manual-input")) {
      e.preventDefault(); navHistory(e.key==="ArrowUp"?1:-1);
    }
  });
  document.addEventListener("click", e => { if (!e.target.closest(".cmd-input-wrapper")) hideAC(); });
});

// ── Auth ────────────────────────────────────────────
function switchTab(tab) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  $(`tab-${tab}`).classList.add("active");
  $("login-form").classList.toggle("active", tab==="login");
  $("register-form").classList.toggle("active", tab==="register");
}

async function apiFetch(url, opts={}) {
  const res = await fetch(`${API}${url}`, { headers: {"Content-Type":"application/json", ...(S.token?{Authorization:`Bearer ${S.token}`}:{})}, ...opts });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

async function handleLogin(e) {
  e.preventDefault(); $("login-error").textContent = "";
  try {
    const d = await apiFetch("/auth/login", { method:"POST", body: JSON.stringify({ username: $("login-username").value.trim(), password: $("login-password").value }) });
    S.token = d.access_token; S.user = d.user; S.sessionToken = d.session_token;
    localStorage.setItem("jarvis_token", S.token); localStorage.setItem("jarvis_user", JSON.stringify(S.user));
    localStorage.setItem("jarvis_session_token", S.sessionToken); showMain();
  } catch(err) { $("login-error").textContent = err.message; }
}

async function handleRegister(e) {
  e.preventDefault(); $("reg-error").textContent = "";
  try {
    await apiFetch("/auth/register", { method:"POST", body: JSON.stringify({ username:$("reg-username").value.trim(), email:$("reg-email").value.trim(), password:$("reg-password").value }) });
    $("login-username").value = $("reg-username").value; $("login-password").value = $("reg-password").value;
    switchTab("login"); await handleLogin({ preventDefault:()=>{} });
  } catch(err) { $("reg-error").textContent = err.message; }
}

function logout() {
  ["jarvis_token","jarvis_user","jarvis_session_token"].forEach(k => localStorage.removeItem(k));
  S.token = S.user = S.sessionToken = null;
  $("auth-screen").classList.add("active"); $("main-screen").classList.remove("active"); stopListening();
}

function showMain() {
  $("auth-screen").classList.remove("active"); $("main-screen").classList.add("active");
  const name = S.user?.username || "USER";
  $("hud-username").textContent = name.toUpperCase(); $("user-avatar").textContent = name[0].toUpperCase();
  if ($("settings-username")) $("settings-username").textContent = name;
  initParticles("bg-particles"); loadHistory(); updateStats(); setInterval(updateStats, 10000);
  showToast(`Welcome back, ${name}! JARVIS v3.0 ready.`, "success");
}

// ── Navigation ──────────────────────────────────────
function switchSection(name) {
  S.currentSection = name;
  document.querySelectorAll(".sidebar-btn").forEach(b => b.classList.toggle("active", b.dataset.section===name));
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  $(`section-${name}`)?.classList.add("active");
  if (name==="commands") setTimeout(()=>$("manual-input")?.focus(), 100);
  if (name==="analytics") loadAnalytics();
  if (name==="history") loadHistory();
  if (name==="settings") loadSettings();
}

// ── Voice ───────────────────────────────────────────
function initSpeech() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;
  if (S.recognition) try { S.recognition.abort(); } catch(_) {}
  const r = S.recognition = new SR();
  r.continuous = false; r.interimResults = true; r.lang = S.settings.lang || "en-US";
  r.onresult = e => {
    const interim = Array.from(e.results).map(r=>r[0].transcript).join("");
    if ($("transcript")) $("transcript").textContent = interim;
    const final = Array.from(e.results).filter(r=>r.isFinal).map(r=>r[0].transcript).join("");
    if (final) processCommand(final);
  };
  r.onend = () => { if (S.isListening) stopListening(); };
  r.onerror = e => {
    showToast(e.error==="not-allowed"?"Microphone denied.":e.error==="no-speech"?"No speech detected.":"Voice error.", "error");
    stopListening();
  };
}

function toggleListening() { S.isListening ? stopListening() : startListening(); }

function startListening() {
  if (!S.recognition) { showToast("Speech not supported. Use Chrome/Edge.", "error"); return; }
  if (S.settings.autoswitch) switchSection("commands");
  navigator.mediaDevices?.getUserMedia
    ? navigator.mediaDevices.getUserMedia({audio:true}).then(doListen).catch(()=>showToast("Microphone denied.","error"))
    : doListen();
}

function doListen() {
  S.isListening = true;
  $("main-orb")?.classList.add("listening"); $("orb-container")?.classList.add("listening");
  if ($("orb-state")) $("orb-state").textContent = "LISTENING...";
  setStatus("listening","LISTENING"); if ($("transcript")) $("transcript").textContent = "...";
  try { S.recognition.start(); } catch(_) { stopListening(); }
}

function stopListening() {
  S.isListening = false;
  $("main-orb")?.classList.remove("listening"); $("orb-container")?.classList.remove("listening");
  if ($("orb-state")) $("orb-state").innerHTML = 'Click the orb or press <kbd>Ctrl+Space</kbd> to speak';
  setStatus("active","SYSTEM ONLINE"); try { S.recognition?.stop(); } catch(_) {}
}

// ── Command Processing ──────────────────────────────
async function processCommand(text) {
  if (!text.trim()) return;
  stopListening(); hideAC();
  if (S.settings.autoswitch || S.currentSection==="commands") switchSection("commands");
  if (S.inputHistory[0] !== text) {
    S.inputHistory = [text, ...S.inputHistory].slice(0, 30);
    localStorage.setItem("jarvis_input_history", JSON.stringify(S.inputHistory));
  }
  S.inputHistoryIdx = -1;
  if ($("transcript")) $("transcript").textContent = text;
  $("main-orb")?.classList.add("processing");
  if ($("orb-state")) $("orb-state").textContent = "PROCESSING...";
  setStatus("active","PROCESSING");
  if ($("response-text")) { $("response-text").textContent=""; $("response-text").classList.add("typing"); }
  addChat(text, "user");
  try {
    const d = await apiFetch("/commands/process", { method:"POST", body: JSON.stringify({text, session_token:S.sessionToken}) });
    if ($("response-text")) { $("response-text").classList.remove("typing"); $("response-text").textContent=d.response; }
    S.cmdCount++; if ($("cmd-count")) $("cmd-count").textContent = S.cmdCount;
    if (S.settings.tts) speak(d.response, S.settings.rate);
    addChat(d.response, "jarvis"); handleAction(d.intent, d.action_data);
    showToast(`✓ ${d.intent.replace(/_/g," ").toUpperCase()}`, "success");
    if (S.settings.notifications && d.intent==="set_reminder") notify("JARVIS Reminder", d.response);
  } catch(err) {
    const msg = "Connection error. Is the server running?";
    if ($("response-text")) { $("response-text").classList.remove("typing"); $("response-text").textContent=msg; }
    addChat(msg, "jarvis"); showToast("Command failed — server unreachable", "error");
  } finally {
    $("main-orb")?.classList.remove("processing");
    if ($("orb-state")) $("orb-state").innerHTML = 'Click the orb or press <kbd>Ctrl+Space</kbd> to speak';
    setStatus("active","SYSTEM ONLINE");
  }
}

// ── TTS ─────────────────────────────────────────────
function speak(text, rate=1.0) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/\*\*/g,"").replace(/\*/g,""));
  u.rate = parseFloat(rate)||1.0; u.pitch = 0.9;
  const v = window.speechSynthesis.getVoices().find(v=>v.name.includes("Google UK English Male")||v.name.includes("Daniel")||v.name.includes("Microsoft David"));
  if (v) u.voice = v;
  window.speechSynthesis.speak(u);
}

// ── Action Handler ──────────────────────────────────
function handleAction(intent, ad) {
  const OPEN = {
    "web_search": ad?.query && `https://www.google.com/search?q=${encodeURIComponent(ad.query)}`,
    "weather":    ad?.location && `https://wttr.in/${encodeURIComponent(ad.location)}`,
    "news":       "https://news.google.com",
    "play_media": ad?.media && `https://www.youtube.com/results?search_query=${encodeURIComponent(ad.media)}`,
  };
  const url = OPEN[intent];
  if (url) setTimeout(()=>window.open(url,"_blank"), 1500);
}

// ── Input ───────────────────────────────────────────
function handleManualKey(e) {
  if (e.key==="Enter") { hideAC(); sendManual(); }
  else if (e.key==="Tab") { e.preventDefault(); acceptAC(); }
  else if (e.key==="ArrowDown") { e.preventDefault(); moveAC(1); }
  else if (e.key==="ArrowUp") { e.preventDefault(); moveAC(-1); }
}
function sendManual() { const t=$("manual-input").value.trim(); if(!t)return; $("manual-input").value=""; processCommand(t); }
function handleChatKey(e) { if(e.key==="Enter") sendChat(); }
function sendChat() { const t=$("chat-input").value.trim(); if(!t)return; $("chat-input").value=""; processCommand(t); }

function navHistory(dir) {
  if (!S.inputHistory.length) return;
  S.inputHistoryIdx = Math.max(-1, Math.min(S.inputHistory.length-1, S.inputHistoryIdx+dir));
  const inp = $("manual-input"); if (!inp) return;
  inp.value = S.inputHistoryIdx>=0 ? S.inputHistory[S.inputHistoryIdx] : "";
  inp.setSelectionRange(inp.value.length, inp.value.length);
}

// ── Autocomplete ────────────────────────────────────
function handleAutoComplete(val) {
  if (!S.settings.autocomplete || !val.trim() || val.length<2) { hideAC(); return; }
  const q=val.toLowerCase(), matches=SUGGESTIONS.filter(s=>s.text.toLowerCase().includes(q)).slice(0,7);
  if (!matches.length) { hideAC(); return; }
  const dd=$("autocomplete-dropdown"); if (!dd) return;
  S.acIdx=-1;
  dd.innerHTML = matches.map((s,i)=>`<div class="autocomplete-item" data-idx="${i}" onclick="selectAC('${esc(s.text)}')">
    <span class="ac-icon">${s.icon}</span><span class="ac-text">${hlMatch(s.text,q)}</span><span class="ac-tag">${s.tag}</span></div>`).join("");
  dd.style.display="block";
}
function hlMatch(text,q) { const i=text.toLowerCase().indexOf(q); if(i<0)return esc(text); return esc(text.slice(0,i))+`<strong style="color:var(--primary)">${esc(text.slice(i,i+q.length))}</strong>`+esc(text.slice(i+q.length)); }
function moveAC(dir) {
  const dd=$("autocomplete-dropdown"); if (!dd||dd.style.display==="none") return;
  const items=dd.querySelectorAll(".autocomplete-item"); if(!items.length)return;
  items[S.acIdx>=0?S.acIdx:0]?.classList.remove("selected");
  S.acIdx=Math.max(0,Math.min(items.length-1,S.acIdx+dir)); items[S.acIdx].classList.add("selected");
  const inp=$("manual-input"); if(inp) inp.value=items[S.acIdx].querySelector(".ac-text").textContent;
}
function acceptAC() {
  const dd=$("autocomplete-dropdown"); if(!dd||dd.style.display==="none")return;
  const sel=dd.querySelector(".autocomplete-item.selected")||dd.querySelector(".autocomplete-item");
  if(sel&&$("manual-input")) $("manual-input").value=sel.querySelector(".ac-text").textContent; hideAC();
}
function selectAC(text) { if($("manual-input")) $("manual-input").value=text; hideAC(); $("manual-input")?.focus(); }
function hideAC() { const dd=$("autocomplete-dropdown"); if(dd)dd.style.display="none"; S.acIdx=-1; }

// ── Chat ────────────────────────────────────────────
function addChat(text, from) {
  const el=document.createElement("div"); el.className=`chat-msg ${from}`;
  const init=from==="jarvis"?"J":(S.user?.username?.[0]?.toUpperCase()||"U");
  el.innerHTML=`<div class="chat-avatar">${init}</div><div class="chat-bubble">${esc(text)}</div>`;
  const msgs=$("chat-messages"); if(msgs){msgs.appendChild(el);msgs.scrollTop=msgs.scrollHeight;}
  S.chatCount++; if($("chat-badge"))$("chat-badge").textContent=S.chatCount;
}

// ── History ─────────────────────────────────────────
async function loadHistory() {
  const list=$("history-list"); if(!list)return;
  list.innerHTML=`<div class="skeleton skeleton-item"></div>`.repeat(3);
  try {
    const logs=await apiFetch("/commands/history?limit=50"); S.historyCache=logs; renderHistory(logs);
  } catch(_){ list.innerHTML=`<div class="history-empty">History unavailable.</div>`; }
}

function renderHistory(logs) {
  const list=$("history-list"); if(!list)return;
  if(!logs.length){list.innerHTML=`<div class="history-empty">No commands yet. Start speaking or typing.</div>`;return;}
  list.innerHTML="";
  logs.forEach(log=>{
    const item=document.createElement("div"); item.className="history-item";
    const ts=log.created_at?new Date(log.created_at).toLocaleTimeString("en-US",{hour:"2-digit",minute:"2-digit"}):"";
    item.innerHTML=`<div class="history-input">▸ ${esc(log.input||log.raw_input||"")}</div>
      <div class="history-response">${esc(log.response||"")}</div>
      <div class="history-meta">
        <span class="intent">${(log.intent||log.detected_intent||"").replace(/_/g," ")}</span>
        <span class="confidence">${log.confidence?Math.round((log.confidence||log.confidence_score)*100)+"%":""}</span>
        <span>${log.latency_ms?log.latency_ms+"ms":""}</span><span class="ts">${ts}</span></div>`;
    item.title="Click to re-run"; item.addEventListener("click",()=>{
      const cmd=log.input||log.raw_input||"";
      if(cmd){switchSection("commands");if($("manual-input"))$("manual-input").value=cmd;setTimeout(()=>$("manual-input")?.focus(),100);}
    });
    list.appendChild(item);
  });
}

function filterHistory(query) {
  if(!query.trim()){renderHistory(S.historyCache);return;}
  const q=query.toLowerCase();
  renderHistory(S.historyCache.filter(l=>(l.input||"").toLowerCase().includes(q)||(l.response||"").toLowerCase().includes(q)||(l.intent||"").toLowerCase().includes(q)));
}

async function exportHistory() {
  try {
    const d=await apiFetch("/commands/export");
    const a=document.createElement("a"); a.href=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:"application/json"}));
    a.download=`jarvis_history_${new Date().toISOString().slice(0,10)}.json`; a.click();
    showToast(`Exported ${d.total} commands`,"success");
  } catch(_){showToast("Export failed","error");}
}

// ── Analytics ───────────────────────────────────────
async function loadAnalytics() {
  try {
    const d=await apiFetch("/commands/stats");
    if($("stat-total"))$("stat-total").textContent=d.total_commands;
    if($("stat-latency"))$("stat-latency").textContent=d.avg_latency_ms+" ms";
    if($("stat-confidence"))$("stat-confidence").textContent=d.avg_confidence+"%";
    if($("stat-session"))$("stat-session").textContent=S.cmdCount;
    renderChart(d.intent_breakdown);
  } catch(_){}
}

function renderChart(intents) {
  const chart=$("intent-chart"); if(!chart)return;
  if(!intents?.length){chart.innerHTML=`<div class="analytics-empty">Run some commands to see patterns!</div>`;return;}
  const max=intents[0].count||1;
  chart.innerHTML=intents.slice(0,10).map(item=>{
    const pct=Math.round((item.count/max)*100), label=item.intent.replace(/_/g," ");
    return `<div class="intent-bar-row"><span class="intent-bar-label" title="${label}">${label}</span>
      <div class="intent-bar-track"><div class="intent-bar-fill" style="width:${pct}%"></div></div>
      <span class="intent-bar-count">${item.count}</span></div>`;
  }).join("");
}

// ── Settings ────────────────────────────────────────
function loadSettings() {
  const s=S.settings;
  [["setting-tts","tts",true],["setting-rate","rate",1.0],["setting-lang","lang","en-US"],
   ["setting-autoswitch","autoswitch",true],["setting-notifications","notifications",false],["setting-autocomplete","autocomplete",true]]
    .forEach(([id,key,def])=>{const el=$(id);if(!el)return; el.type==="checkbox"?el.checked=s[key]!==undefined?s[key]:def:el.value=s[key]||def;});
  if($("settings-username")&&S.user)$("settings-username").textContent=S.user.username;
}

function saveSetting(key, value) {
  S.settings[key]=value; localStorage.setItem("jarvis_settings",JSON.stringify(S.settings));
  if(key==="lang"&&S.recognition)S.recognition.lang=value;
  showToast(`Setting saved: ${key}`,"success");
}

function toggleNotifications(enabled) {
  if(enabled&&"Notification"in window)
    Notification.requestPermission().then(p=>p==="granted"?saveSetting("notifications",true):(($("setting-notifications").checked=false),showToast("Permission denied.","error")));
  else saveSetting("notifications",false);
}
function notify(title,body){if("Notification"in window&&Notification.permission==="granted")new Notification(title,{body,icon:"/favicon.ico"});}

// ── System Stats ────────────────────────────────────
async function updateStats() {
  try {
    const d=await apiFetch("/commands/system-stats");
    if($("cpu-val"))$("cpu-val").textContent=d.cpu_percent+"%"; if($("cpu-bar"))$("cpu-bar").style.width=d.cpu_percent+"%";
    if($("ram-val"))$("ram-val").textContent=d.ram_percent+"%"; if($("ram-bar"))$("ram-bar").style.width=d.ram_percent+"%";
    if(d.battery_percent>=0){if($("battery-val"))$("battery-val").textContent=d.battery_percent+"%";if($("battery-bar"))$("battery-bar").style.width=d.battery_percent+"%";}
    else if($("battery-val"))$("battery-val").textContent="N/A";
  } catch(_){}
}

// ── Clock ────────────────────────────────────────────
function initClock() {
  const update=()=>{if($("topbar-time"))$("topbar-time").textContent=new Date().toLocaleTimeString("en-US",{hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:true});};
  update(); setInterval(update,1000);
}

// ── Toast ────────────────────────────────────────────
function showToast(msg, type="info") {
  const c=$("toast-container"); if(!c)return;
  const t=document.createElement("div"); t.className=`toast ${type}`; t.textContent=msg;
  c.appendChild(t); setTimeout(()=>t.parentNode&&t.remove(),4000);
}

// ── Particles ────────────────────────────────────────
function initParticles(id) {
  const canvas=$(id); if(!canvas)return;
  const ctx=canvas.getContext("2d"); let w,h,pts=[];
  const resize=()=>{w=canvas.width=window.innerWidth;h=canvas.height=window.innerHeight;};
  resize(); window.addEventListener("resize",resize);
  for(let i=0;i<60;i++) pts.push({x:Math.random()*w,y:Math.random()*h,r:Math.random()*1.5+.5,vx:(Math.random()-.5)*.3,vy:(Math.random()-.5)*.3,a:Math.random()*.3+.1});
  (function draw(){
    ctx.clearRect(0,0,w,h);
    pts.forEach(p=>{
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0)p.x=w;if(p.x>w)p.x=0;if(p.y<0)p.y=h;if(p.y>h)p.y=0;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle=`rgba(108,140,255,${p.a})`;ctx.fill();
    });
    for(let i=0;i<pts.length;i++) for(let j=i+1;j<pts.length;j++){
      const dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y,dist=Math.sqrt(dx*dx+dy*dy);
      if(dist<120){ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(pts[j].x,pts[j].y);ctx.strokeStyle=`rgba(108,140,255,${.06*(1-dist/120)})`;ctx.stroke();}
    }
    requestAnimationFrame(draw);
  })();
}

// ── Utils ────────────────────────────────────────────
function setStatus(s,text){const dot=$("status-dot");if(dot)dot.className=`status-dot ${s}`;if($("status-text"))$("status-text").textContent=text;}
function esc(t){if(!t)return"";const d=document.createElement("div");d.textContent=t;return d.innerHTML;}
