/**
 * Fitness Buddy — Main JavaScript
 * Dark mode · Chat interface · Calculators · Charts · Dashboard
 */

"use strict";

/* ═══════════════════════════════════════════════════════════════
   1. THEME (Dark / Light Mode)
═══════════════════════════════════════════════════════════════ */
const THEME_KEY = "fb_theme";

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY) || "light";
  applyTheme(saved);
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem(THEME_KEY, theme);
  const icon = document.getElementById("themeIcon");
  if (icon) {
    icon.className = theme === "dark" ? "fa-solid fa-sun" : "fa-solid fa-moon";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  const toggle = document.getElementById("themeToggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme");
      applyTheme(current === "dark" ? "light" : "dark");
      // Re-render charts on theme change
      setTimeout(() => { if (typeof renderCharts === "function") renderCharts(); }, 50);
    });
  }
});

/* ═══════════════════════════════════════════════════════════════
   2. UTILITIES
═══════════════════════════════════════════════════════════════ */
function getCsrfToken() {
  const m = document.cookie.match(/csrf_token=([^;]+)/);
  return m ? m[1] : "";
}

function getThemeColors() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  return {
    text    : isDark ? "#f1f5f9" : "#0f172a",
    muted   : isDark ? "#94a3b8" : "#64748b",
    border  : isDark ? "#334155" : "#e2e8f0",
    surface : isDark ? "#1e293b" : "#ffffff",
    accent  : "#6366f1",
    success : "#10b981",
    warning : "#f59e0b",
    danger  : "#ef4444",
    orange  : "#f97316",
    gridLine: isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
  };
}

function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  const icon  = btn.querySelector("i");
  if (input.type === "password") {
    input.type = "text";
    icon.className = "fa-regular fa-eye-slash";
  } else {
    input.type = "password";
    icon.className = "fa-regular fa-eye";
  }
}

/* ═══════════════════════════════════════════════════════════════
   3. CHAT INTERFACE
═══════════════════════════════════════════════════════════════ */
let currentSessionId  = null;
let isSending         = false;

// Markdown → safe HTML renderer (via marked.js)
function renderMarkdown(text) {
  if (typeof marked === "undefined") return escapeHtml(text);
  return marked.parse(text, { breaks: true, gfm: true });
}

function escapeHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function autoResizeTextarea(ta) {
  ta.style.height = "auto";
  ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
}

function handleChatKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function sendSuggestedPrompt(prompt) {
  const input = document.getElementById("chatInput");
  if (input) { input.value = prompt; }
  sendMessage();
}

function appendMessage(role, content) {
  const container = document.getElementById("chatMessages");
  const welcome   = document.getElementById("chatWelcome");
  if (welcome) welcome.style.display = "none";

  const div   = document.createElement("div");
  div.className = `chat-message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = role === "user" ? "user-avatar" : "ai-avatar-xs";
  avatar.innerHTML = role === "user"
    ? (document.querySelector(".user-avatar")?.textContent?.trim() || "U")
    : '<i class="fa-solid fa-robot"></i>';

  const bubble = document.createElement("div");
  bubble.className = "message-content";
  bubble.innerHTML = role === "assistant" ? renderMarkdown(content) : escapeHtml(content);

  div.appendChild(avatar);
  div.appendChild(bubble);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

async function sendMessage() {
  if (isSending) return;
  const input = document.getElementById("chatInput");
  const text  = (input?.value || "").trim();
  if (!text) return;

  isSending = true;
  input.value = "";
  input.style.height = "auto";
  document.getElementById("sendBtn")?.setAttribute("disabled", "true");

  appendMessage("user", text);

  // Show typing indicator
  const typing = document.getElementById("typingIndicator");
  if (typing) typing.classList.remove("d-none");
  document.getElementById("chatMessages").scrollTop = 99999;

  try {
    const resp = await fetch("/chat/send", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ message: text, session_id: currentSessionId }),
    });
    const data = await resp.json();

    if (typing) typing.classList.add("d-none");

    if (data.reply) {
      appendMessage("assistant", data.reply);
      currentSessionId = data.session_id;
      updateSessionList(data.session_id, data.title);
    } else {
      appendMessage("assistant", "⚠️ Sorry, I couldn't process your request. Please try again.");
    }
  } catch (err) {
    if (typing) typing.classList.add("d-none");
    appendMessage("assistant", "⚠️ Network error. Please check your connection and try again.");
  } finally {
    isSending = false;
    document.getElementById("sendBtn")?.removeAttribute("disabled");
    input.focus();
  }
}

async function loadSession(sessionId, element) {
  // Highlight active session
  document.querySelectorAll(".chat-history-item").forEach(el => el.classList.remove("active"));
  if (element) element.classList.add("active");

  try {
    const resp = await fetch(`/chat/session/${sessionId}`);
    const data = await resp.json();

    currentSessionId = data.session_id;
    const container  = document.getElementById("chatMessages");
    const welcome    = document.getElementById("chatWelcome");

    container.innerHTML = "";
    if (welcome) container.appendChild(welcome);

    if (data.messages && data.messages.length > 0) {
      if (welcome) welcome.style.display = "none";
      data.messages.forEach(m => appendMessage(m.role === "user" ? "user" : "assistant", m.content));
    } else {
      if (welcome) welcome.style.display = "flex";
    }
  } catch (e) {
    console.error("Failed to load session:", e);
  }
}

async function startNewChat() {
  try {
    const resp = await fetch("/chat/session/new", { method: "POST" });
    const data = await resp.json();
    currentSessionId = data.session_id;

    // Reset UI
    const container = document.getElementById("chatMessages");
    const welcome   = document.getElementById("chatWelcome");
    container.innerHTML = "";
    if (welcome) {
      welcome.style.display = "flex";
      container.appendChild(welcome);
    }
    document.querySelectorAll(".chat-history-item").forEach(el => el.classList.remove("active"));

    // Add to list
    const list = document.getElementById("sessionList");
    if (list) {
      const item = document.createElement("div");
      item.className = "chat-history-item active";
      item.dataset.sessionId = data.session_id;
      item.innerHTML = `<i class="fa-regular fa-message me-2"></i><span class="session-title">New Chat</span>
        <button class="btn-delete-session ms-auto" onclick="deleteSession(event, ${data.session_id})"><i class="fa-solid fa-trash-can"></i></button>`;
      item.addEventListener("click", (e) => { if (!e.target.closest(".btn-delete-session")) loadSession(data.session_id, item); });
      list.prepend(item);
    }
  } catch (e) { console.error("Failed to create session:", e); }
}

function updateSessionList(sessionId, title) {
  const list = document.getElementById("sessionList");
  if (!list) return;
  let item = list.querySelector(`[data-session-id="${sessionId}"]`);
  if (!item) {
    item = document.createElement("div");
    item.className = "chat-history-item active";
    item.dataset.sessionId = sessionId;
    item.innerHTML = `<i class="fa-regular fa-message me-2"></i><span class="session-title"></span>
      <button class="btn-delete-session ms-auto" onclick="deleteSession(event, ${sessionId})"><i class="fa-solid fa-trash-can"></i></button>`;
    item.addEventListener("click", (e) => { if (!e.target.closest(".btn-delete-session")) loadSession(sessionId, item); });
    list.prepend(item);
  }
  const titleEl = item.querySelector(".session-title");
  if (titleEl) titleEl.textContent = (title || "New Chat").slice(0, 35);
  document.querySelectorAll(".chat-history-item").forEach(el => el.classList.remove("active"));
  item.classList.add("active");
}

async function deleteSession(event, sessionId) {
  event.stopPropagation();
  if (!confirm("Delete this chat?")) return;
  try {
    await fetch(`/chat/session/${sessionId}/delete`, { method: "DELETE" });
    const item = document.querySelector(`[data-session-id="${sessionId}"]`);
    if (item) item.remove();
    if (currentSessionId === sessionId) {
      currentSessionId = null;
      const container = document.getElementById("chatMessages");
      const welcome   = document.getElementById("chatWelcome");
      container.innerHTML = "";
      if (welcome) { welcome.style.display = "flex"; container.appendChild(welcome); }
    }
  } catch (e) { console.error("Failed to delete session:", e); }
}

function clearCurrentChat() {
  if (!currentSessionId) return;
  const container = document.getElementById("chatMessages");
  const welcome   = document.getElementById("chatWelcome");
  container.innerHTML = "";
  if (welcome) { welcome.style.display = "flex"; container.appendChild(welcome); }
}

function toggleChatSidebar() {
  const panel = document.getElementById("chatHistoryPanel");
  panel?.classList.toggle("open");
}

/* Handle pre-filled prompt from URL (e.g., from nutrition/workout pages) */
document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const prompt    = urlParams.get("prompt");
  if (prompt && document.getElementById("chatInput")) {
    document.getElementById("chatInput").value = decodeURIComponent(prompt);
    setTimeout(() => sendMessage(), 500);
  }
});

/* ═══════════════════════════════════════════════════════════════
   4. DASHBOARD CHARTS
═══════════════════════════════════════════════════════════════ */
let weightChartInstance  = null;
let calorieChartInstance = null;

function renderCharts() {
  const c = getThemeColors();
  const chartDefaults = {
    font: { family: "'Inter', sans-serif" },
    color: c.muted,
  };
  Chart.defaults.color = c.muted;
  Chart.defaults.font.family = "'Inter', sans-serif";

  // Weight Chart
  const wCanvas = document.getElementById("weightChart");
  if (wCanvas && typeof weightLabels !== "undefined") {
    if (weightChartInstance) weightChartInstance.destroy();
    weightChartInstance = new Chart(wCanvas, {
      type: "line",
      data: {
        labels  : weightLabels.length ? weightLabels : ["No data"],
        datasets: [{
          label       : "Weight (kg)",
          data        : weightData.length  ? weightData  : [0],
          borderColor : c.accent,
          backgroundColor: hexToRgba(c.accent, 0.1),
          borderWidth : 2.5,
          fill        : true,
          tension     : 0.4,
          pointBackgroundColor: c.accent,
          pointRadius : 4,
        }],
      },
      options: {
        responsive: true,
        plugins   : { legend: { display: false }, tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y} kg` } } },
        scales    : {
          x: { grid: { color: c.gridLine }, ticks: { color: c.muted, maxTicksLimit: 7 } },
          y: { grid: { color: c.gridLine }, ticks: { color: c.muted } },
        },
      },
    });
  }

  // Calorie Chart
  const calCanvas = document.getElementById("calorieChart");
  if (calCanvas && typeof calLabels !== "undefined") {
    if (calorieChartInstance) calorieChartInstance.destroy();
    calorieChartInstance = new Chart(calCanvas, {
      type: "bar",
      data: {
        labels  : calLabels,
        datasets: [{
          label          : "Calories",
          data           : calData,
          backgroundColor: hexToRgba(c.success, 0.7),
          borderColor    : c.success,
          borderWidth    : 1.5,
          borderRadius   : 6,
        }],
      },
      options: {
        responsive: true,
        plugins   : { legend: { display: false } },
        scales    : {
          x: { grid: { color: c.gridLine }, ticks: { color: c.muted } },
          y: { grid: { color: c.gridLine }, ticks: { color: c.muted } },
        },
      },
    });
  }
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("weightChart") || document.getElementById("calorieChart")) {
    renderCharts();
  }
});

/* ═══════════════════════════════════════════════════════════════
   5. WATER TRACKER (Dashboard)
═══════════════════════════════════════════════════════════════ */
async function addWater(amount) {
  try {
    const res  = await fetch("/api/water/add", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ amount_ml: amount }),
    });
    const data = await res.json();
    updateWaterUI(data.total_ml, data.goal_ml);
  } catch (e) { console.error("Water log error:", e); }
}

function updateWaterUI(totalMl, goalMl) {
  const mlEl    = document.getElementById("waterMl");
  const circle  = document.getElementById("waterCircle");

  if (mlEl) mlEl.textContent = Math.round(totalMl);

  if (circle) {
    const circumference = 251.2;
    const pct    = Math.min(totalMl / goalMl, 1);
    const offset = circumference - circumference * pct;
    circle.style.strokeDashoffset = offset;
  }
}

/* ═══════════════════════════════════════════════════════════════
   6. WEIGHT LOGGING (Dashboard quick log)
═══════════════════════════════════════════════════════════════ */
async function logWeight() {
  const input = document.getElementById("weightInput");
  const val   = parseFloat(input?.value);
  if (!val) return;

  try {
    const res  = await fetch("/profile/weight/log", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ weight_kg: val }),
    });
    const data = await res.json();
    const fb   = document.getElementById("weightLogFeedback");
    if (data.success) {
      if (fb) fb.innerHTML = `<span class="text-success"><i class="fa-solid fa-check me-1"></i>Logged! BMI: ${data.new_bmi || "—"}</span>`;
      input.value = "";
      setTimeout(() => location.reload(), 1500);
    }
  } catch (e) { console.error("Weight log error:", e); }
}

/* ═══════════════════════════════════════════════════════════════
   7. FITNESS CALCULATORS
═══════════════════════════════════════════════════════════════ */
// Tab switching
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-calc]").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".calc-panel").forEach(p => p.classList.add("d-none"));
      document.querySelectorAll("[data-calc]").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const panel = document.getElementById(`calc-${btn.dataset.calc}`);
      if (panel) panel.classList.remove("d-none");
    });
  });
});

// BMI
async function calculateBMI() {
  const weight = parseFloat(document.getElementById("bmiWeight")?.value);
  const height = parseFloat(document.getElementById("bmiHeight")?.value);
  if (!weight || !height) { alert("Please enter valid weight and height."); return; }

  try {
    const res  = await fetch("/calculators/bmi", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ weight_kg: weight, height_cm: height }),
    });
    const data = await res.json();

    document.getElementById("bmiResult").style.display = "block";
    document.getElementById("bmiVal").textContent      = data.bmi;
    document.getElementById("bmiCategory").textContent = data.category;
    document.getElementById("bmiIdeal").textContent    = `${data.ideal_low} – ${data.ideal_high} kg`;

    const actionLabel = document.getElementById("bmiActionLabel");
    const actionVal   = document.getElementById("bmiAction");
    if (data.to_lose > 0)      { actionLabel.textContent = "To Lose";  actionVal.textContent = `${data.to_lose} kg`; }
    else if (data.to_gain > 0) { actionLabel.textContent = "To Gain";  actionVal.textContent = `${data.to_gain} kg`; }
    else                        { actionLabel.textContent = "Status";   actionVal.textContent = "Ideal"; }

    // Colour the circle
    const circle = document.getElementById("bmiCircle");
    circle.style.borderColor = data.category === "Normal weight" ? "#10b981"
      : data.category === "Underweight"                          ? "#3b82f6"
      : data.category === "Overweight"                           ? "#f59e0b"
      : "#ef4444";
  } catch (e) { alert("Calculation error. Please try again."); }
}

// BMR
async function calculateBMR() {
  const weight = parseFloat(document.getElementById("bmrWeight")?.value);
  const height = parseFloat(document.getElementById("bmrHeight")?.value);
  const age    = parseInt(document.getElementById("bmrAge")?.value);
  const gender = document.getElementById("bmrGender")?.value;
  if (!weight || !height || !age) { alert("Please fill all fields."); return; }

  const res  = await fetch("/calculators/bmr", {
    method : "POST",
    headers: { "Content-Type": "application/json" },
    body   : JSON.stringify({ weight_kg: weight, height_cm: height, age, gender }),
  });
  const data = await res.json();
  document.getElementById("bmrResult").style.display = "block";
  document.getElementById("bmrVal").textContent      = data.bmr;

  // Auto-fill TDEE page
  const tdeeBMR = document.getElementById("tdeeBMR");
  if (tdeeBMR) tdeeBMR.value = data.bmr;
}

// TDEE
async function calculateTDEE() {
  const bmr      = parseFloat(document.getElementById("tdeeBMR")?.value);
  const activity = document.getElementById("tdeeActivity")?.value;
  if (!bmr) { alert("Please enter your BMR first."); return; }

  const res  = await fetch("/calculators/tdee", {
    method : "POST",
    headers: { "Content-Type": "application/json" },
    body   : JSON.stringify({ bmr, activity_level: activity }),
  });
  const data = await res.json();
  document.getElementById("tdeeResult").style.display = "block";
  document.getElementById("tdeeLoss").textContent     = data.weight_loss;
  document.getElementById("tdeeMaint").textContent    = data.maintenance;
  document.getElementById("tdeeGain").textContent     = data.weight_gain;

  // Auto-fill macros
  const macrosTDEE = document.getElementById("macrosTDEE");
  if (macrosTDEE) macrosTDEE.value = data.maintenance;
}

// Water
async function calculateWater() {
  const weight   = parseFloat(document.getElementById("waterWeight")?.value);
  const activity = document.getElementById("waterActivity")?.value;
  const climate  = document.getElementById("waterClimate")?.value;
  if (!weight) { alert("Please enter your weight."); return; }

  const res  = await fetch("/calculators/water", {
    method : "POST",
    headers: { "Content-Type": "application/json" },
    body   : JSON.stringify({ weight_kg: weight, activity_level: activity, climate }),
  });
  const data = await res.json();
  document.getElementById("waterResult").style.display = "block";
  document.getElementById("waterLiters").textContent   = data.water_liters;
  document.getElementById("waterGlasses").textContent  = data.glasses_250ml;
}

// Macros
let macroChartInstance = null;
async function calculateMacros() {
  const tdee  = parseFloat(document.getElementById("macrosTDEE")?.value);
  const goal  = document.getElementById("macrosGoal")?.value;
  const diet  = document.getElementById("macrosDiet")?.value;
  if (!tdee) { alert("Please enter your TDEE."); return; }

  const res  = await fetch("/calculators/macros", {
    method : "POST",
    headers: { "Content-Type": "application/json" },
    body   : JSON.stringify({ tdee, goal, diet }),
  });
  const data = await res.json();
  document.getElementById("macrosResult").style.display   = "block";
  document.getElementById("macrosCals").textContent       = data.calories;
  document.getElementById("macrosProtein").textContent    = `${data.protein_g}g`;
  document.getElementById("macrosCarbs").textContent      = `${data.carbs_g}g`;
  document.getElementById("macrosFat").textContent        = `${data.fat_g}g`;

  // Doughnut chart
  const canvas = document.getElementById("macroChart");
  if (canvas) {
    if (macroChartInstance) macroChartInstance.destroy();
    macroChartInstance = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels  : ["Protein", "Carbs", "Fat"],
        datasets: [{ data: [data.protein_g * 4, data.carbs_g * 4, data.fat_g * 9], backgroundColor: ["#3b82f6","#f59e0b","#10b981"], borderWidth: 0 }],
      },
      options: {
        cutout     : "65%",
        responsive : true,
        plugins    : { legend: { position: "bottom", labels: { font: { family: "'Inter',sans-serif" }, padding: 12 } } },
      },
    });
  }
}

/* ═══════════════════════════════════════════════════════════════
   8. AUTO-DISMISS FLASH ALERTS
═══════════════════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    document.querySelectorAll(".fb-alert").forEach(el => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert?.close();
    });
  }, 5000);
});
