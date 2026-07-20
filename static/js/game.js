let soundEnabled = localStorage.getItem("pixelHarvestSound") !== "off";
let audioContext;
let musicTimer;
let musicStarted = false;
let currentTheme;

const themes = {
  day: { wave: "square", tempo: 0.22, notes: [523, 659, 784, 659, 587, 659, 698, 587, 523, 440, 523, 659, 784, 698, 659, 523] },
  night: { wave: "triangle", tempo: 0.38, notes: [392, 440, 523, 440, 349, 392, 466, 392, 330, 392, 440, 523, 440, 392, 349, 330] },
};

document.addEventListener("DOMContentLoaded", () => {
  const game = document.querySelector("#game");
  if (!game) return;
  document.querySelector("#farm-grid").addEventListener("click", (event) => { const plot = event.target.closest(".plot"); if (plot) actOnPlot(plot, game.dataset.cropId); });
  document.querySelectorAll(".shop-item[data-crop-id]").forEach((item) => item.addEventListener("click", () => selectCrop(item, game)));
  document.querySelectorAll(".upgrade").forEach((item) => item.addEventListener("click", () => buyUpgrade(item.dataset.action)));
  document.querySelector("#sound-toggle").addEventListener("click", toggleSound);
  updateSoundToggle();
  updateDeviceTime();
  setInterval(updateDeviceTime, 1000);
  setInterval(() => { refreshFarm(); runIdleTick(); }, 10000);
});

async function ensureAudio() {
  if (!window.AudioContext && !window.webkitAudioContext) return false;
  audioContext ??= new (window.AudioContext || window.webkitAudioContext)();
  if (audioContext.state === "suspended") await audioContext.resume();
  return true;
}

function selectCrop(item, game) {
  document.querySelectorAll(".shop-item[data-crop-id]").forEach((button) => button.classList.toggle("selected", button === item));
  game.dataset.cropId = item.dataset.cropId;
  document.querySelector("#selected-seed").textContent = `${item.dataset.cropName} seeds`;
  document.querySelector("#seed-details").textContent = `Cost ${item.dataset.buy}G · sells for ${item.dataset.sell}G`;
  setStatus(`${item.dataset.cropName} seeds selected`); startMusic(); beep(660, .06);
}

function toggleSound() {
  soundEnabled = !soundEnabled;
  localStorage.setItem("pixelHarvestSound", soundEnabled ? "on" : "off");
  updateSoundToggle();
  if (soundEnabled) { startMusic(); beep(880, .08); } else stopMusic();
}

function updateSoundToggle() {
  const button = document.querySelector("#sound-toggle");
  if (button) { button.textContent = `SOUND & BGM: ${soundEnabled ? "ON" : "OFF"}`; button.setAttribute("aria-pressed", String(soundEnabled)); }
}

async function beep(frequency, duration) {
  if (!soundEnabled || !await ensureAudio()) return;
  const oscillator = audioContext.createOscillator(), gain = audioContext.createGain();
  oscillator.type = "square"; oscillator.frequency.value = frequency;
  gain.gain.setValueAtTime(.045, audioContext.currentTime); gain.gain.exponentialRampToValueAtTime(.001, audioContext.currentTime + duration);
  oscillator.connect(gain).connect(audioContext.destination); oscillator.start(); oscillator.stop(audioContext.currentTime + duration);
}

async function startMusic() {
  if (!soundEnabled || !await ensureAudio()) return;
  musicStarted = true;
  const theme = document.body.classList.contains("is-night") ? "night" : "day";
  if (theme === currentTheme && musicTimer) return;
  stopMusic(); currentTheme = theme; playTheme();
}

function playTheme() {
  if (!soundEnabled || !musicStarted || !audioContext) return;
  const theme = themes[currentTheme], start = audioContext.currentTime + .05;
  theme.notes.forEach((note, index) => {
    const oscillator = audioContext.createOscillator(), gain = audioContext.createGain(), at = start + index * theme.tempo;
    oscillator.type = theme.wave; oscillator.frequency.value = note;
    gain.gain.setValueAtTime(.065, at); gain.gain.exponentialRampToValueAtTime(.001, at + theme.tempo * .82);
    oscillator.connect(gain).connect(audioContext.destination); oscillator.start(at); oscillator.stop(at + theme.tempo);
  });
  musicTimer = window.setTimeout(playTheme, theme.notes.length * theme.tempo * 1000);
}

function stopMusic() { window.clearTimeout(musicTimer); musicTimer = undefined; currentTheme = undefined; }

function updateDeviceTime() {
  const now = new Date(), hour = now.getHours(), night = hour >= 19 || hour < 6;
  const themeChanged = (night ? "night" : "day") !== currentTheme;
  document.body.classList.toggle("is-night", night); document.body.classList.toggle("is-dawn", !night && hour < 9);
  document.querySelector("#device-time").textContent = now.toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"});
  document.querySelector("#time-period").textContent = night ? "NIGHT ON YOUR DEVICE" : hour < 9 ? "MORNING LIGHT" : "DAYLIGHT";
  if (musicStarted && themeChanged) startMusic();
}

async function actOnPlot(plot, cropId) {
  startMusic();
  if (plot.dataset.state === "EMPTY") return requestAction("/api/plant", {plot_id:plot.dataset.id,crop_id:Number(cropId)});
  if (plot.classList.contains("is-ready")) return requestAction("/api/harvest", {plot_id:plot.dataset.id});
  setStatus("Still growing — check back soon."); beep(180,.08);
}

async function requestAction(url, body) {
  try { const response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}),data=await response.json(); if (!data.success) { setStatus(data.error); return beep(160,.14); } updatePlayer(data); renderPlot(data); setStatus(data.crop ? `${data.crop} planted!` : "Harvest complete!"); beep(data.crop ? 520 : 820, .1); } catch (_) { setStatus("Could not reach the farm server."); }
}
async function buyUpgrade(action) { try { const response=await fetch("/api/upgrade",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action})}),data=await response.json(); if (!data.success) { setStatus(data.error); return beep(160,.14); } updatePlayer(data); setStatus(data.message); beep(880,.14); await refreshFarm(); } catch (_) { setStatus("Could not buy that upgrade."); } }
async function refreshFarm() { try { const response=await fetch("/api/farm"); if (!response.ok) return; const data=await response.json(); updatePlayer(data); data.plots.forEach(renderPlot); updateCropLocks(data.crops); } catch (_) {} }
async function runIdleTick() { try { const response=await fetch("/api/idle-tick",{method:"POST"}); const data=await response.json(); if (data.worked) { updatePlayer(data); data.plots.forEach(renderPlot); setStatus(`Farm keeper tended ${data.worked} plot${data.worked > 1 ? "s" : ""}.`); beep(740,.06); } } catch (_) {} }
function renderPlot(data) { let plot=document.querySelector(`#plot-${data.plot_id}`); if (!plot) { plot=document.createElement("button"); plot.className="plot"; plot.id=`plot-${data.plot_id}`; plot.dataset.id=data.plot_id; plot.type="button"; plot.setAttribute("aria-label", "New farm plot"); document.querySelector("#farm-grid").append(plot); } plot.dataset.state=data.state; plot.classList.toggle("is-ready",Boolean(data.is_ready)); plot.innerHTML=`<span class="terrain-layer"></span><span class="soil-layer"></span>${data.crop ? `<span class="crop-layer crop-${data.crop.toLowerCase()} stage-${data.stage}" aria-label="${data.crop}"></span>` : ""}`; }
function updatePlayer(data) { if (data.gold !== undefined) document.querySelector("#gold").textContent=data.gold; if (data.seed_tier !== undefined) { document.querySelector("#seed-tier").textContent=data.seed_tier; document.querySelector("#plot-upgrade").textContent=`${data.plot_cost}G · level ${data.plot_level}`; document.querySelector("#seed-upgrade").textContent=data.seed_cost ? `${data.seed_cost}G` : "MAXED"; document.querySelector("#keeper-upgrade").textContent=data.farmkeeper_level ? "HIRED" : "350G"; document.querySelector('[data-action="seeds"]').disabled=data.seed_tier >= 3; document.querySelector('[data-action="farmkeeper"]').disabled=Boolean(data.farmkeeper_level); } }
function updateCropLocks(crops) { crops.forEach((crop) => { const button=document.querySelector(`[data-crop-id="${crop.id}"]`); if (!button) return; button.disabled=!crop.unlocked; if (crop.unlocked) button.querySelector("small").textContent=`${crop.buy_price}G seed · sells ${crop.sell_price}G`; }); }
function setStatus(text) { document.querySelector("#farm-status").textContent=text; }
