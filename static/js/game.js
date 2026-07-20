const spriteBase = "/static/sprites";

document.addEventListener("DOMContentLoaded", () => {
  const game = document.querySelector("#game");
  if (!game) return;
  document.querySelectorAll(".plot").forEach((plot) => plot.addEventListener("click", () => actOnPlot(plot, game.dataset.cropId)));
  updateDeviceTime();
  setInterval(updateDeviceTime, 1000);
  setInterval(refreshFarm, 10000);
});

function updateDeviceTime() {
  const now = new Date();
  const hour = now.getHours();
  const isNight = hour >= 19 || hour < 6;
  document.body.classList.toggle("is-night", isNight);
  document.body.classList.toggle("is-dawn", !isNight && hour < 9);
  const display = document.querySelector("#device-time");
  const period = document.querySelector("#time-period");
  if (display) display.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (period) period.textContent = isNight ? "NIGHT ON YOUR DEVICE" : hour < 9 ? "MORNING LIGHT" : "DAYLIGHT";
}

async function actOnPlot(plot, cropId) {
  if (plot.dataset.state === "EMPTY") return requestAction("/api/plant", { plot_id: plot.dataset.id, crop_id: Number(cropId) });
  if (plot.classList.contains("is-ready")) return requestAction("/api/harvest", { plot_id: plot.dataset.id });
  setStatus("Still growing — check back soon.");
}

async function requestAction(url, body) {
  try {
    const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await response.json();
    if (!data.success) return setStatus(data.error);
    updateGold(data.gold); renderPlot(data);
    setStatus(data.crop ? "Carrot planted!" : "Harvest complete! +10G");
  } catch (_) { setStatus("Could not reach the farm server."); }
}

async function refreshFarm() {
  try {
    const response = await fetch("/api/farm");
    if (!response.ok) return;
    const data = await response.json(); updateGold(data.gold); data.plots.forEach(renderPlot);
  } catch (_) { /* Keep the last visible state when offline. */ }
}

function renderPlot(data) {
  const plot = document.querySelector(`#plot-${data.plot_id}`); if (!plot) return;
  plot.dataset.state = data.state;
  plot.classList.toggle("is-ready", Boolean(data.is_ready));
  plot.innerHTML = `<img class="terrain-layer" src="${spriteBase}/terrain/grass.png" alt=""><img class="soil-layer" src="${spriteBase}/terrain/soil.png" alt="">${data.crop ? `<img class="crop-layer" src="${spriteBase}/crops/${data.crop.toLowerCase()}/stage${data.stage}.png" alt="${data.crop}">` : ""}`;
}

function updateGold(gold) { const target = document.querySelector("#gold"); if (target) target.textContent = gold; }
function setStatus(text) { const target = document.querySelector("#farm-status"); if (target) target.textContent = text; }
