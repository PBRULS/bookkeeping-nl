/**
 * app.js — Router and global utilities for the SPA.
 */

// ------------------------------------------------------------------ //
//  State                                                               //
// ------------------------------------------------------------------ //
const App = {
  jaar: new Date().getFullYear(),
  instellingen: {},
};

// ------------------------------------------------------------------ //
//  Formatting helpers                                                  //
// ------------------------------------------------------------------ //
function eur(amount) {
  if (amount == null) return "—";
  return new Intl.NumberFormat("nl-NL", {
    style: "currency", currency: "EUR", minimumFractionDigits: 2,
  }).format(amount);
}

function nlDate(isoString) {
  if (!isoString) return "—";
  const d = new Date(isoString.slice(0, 10));
  return d.toLocaleDateString("nl-NL");
}

function statusBadge(status) {
  const map = {
    concept:         ["grey",   "Concept"],
    verzonden:       ["blue",   "Verzonden"],
    betaald:         ["green",  "Betaald"],
    deels_betaald:   ["orange", "Deels betaald"],
    verlopen:        ["red",    "Verlopen"],
    gecrediteerd:    ["grey",   "Gecrediteerd"],
    ontvangen:       ["blue",   "Ontvangen"],
    goedgekeurd:     ["orange", "Goedgekeurd"],
    open:            ["blue",   "Open"],
    ingediend:       ["orange", "Ingediend"],
  };
  const [color, label] = map[status] || ["grey", status];
  return `<span class="badge badge-${color}">${label}</span>`;
}

function showAlert(msg, type = "info", container = "#content") {
  const el = document.querySelector(container);
  if (!el) return;
  const div = document.createElement("div");
  div.className = `alert alert-${type}`;
  div.textContent = msg;
  el.prepend(div);
  setTimeout(() => div.remove(), 5000);
}

function spin() {
  return '<div class="spinner"></div>';
}

// ------------------------------------------------------------------ //
//  Modal helpers                                                       //
// ------------------------------------------------------------------ //
function openModal(id) {
  document.getElementById(id).classList.add("open");
}
function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("open");
  }
  if (e.target.classList.contains("modal-close")) {
    e.target.closest(".modal-overlay").classList.remove("open");
  }
});

// ------------------------------------------------------------------ //
//  Router                                                              //
// ------------------------------------------------------------------ //
const routes = {};

function registerPage(hash, loader) {
  routes[hash] = loader;
}

async function navigate(hash) {
  const content = document.getElementById("content");
  const title   = document.getElementById("page-title");
  content.innerHTML = spin();

  // Update active nav link
  document.querySelectorAll("#sidebar nav a").forEach((a) => {
    a.classList.toggle("active", a.getAttribute("href") === hash);
  });

  const loader = routes[hash];
  if (loader) {
    try {
      await loader(content, title);
    } catch (err) {
      console.error(err);
      content.innerHTML = `<div class="alert alert-danger">Fout bij laden: ${err.message || JSON.stringify(err)}</div>`;
    }
  } else {
    content.innerHTML = `<div class="alert alert-warning">Pagina niet gevonden: ${hash}</div>`;
  }
}

window.addEventListener("hashchange", () => navigate(location.hash || "#dashboard"));

// ------------------------------------------------------------------ //
//  Boot                                                                //
// ------------------------------------------------------------------ //
document.addEventListener("DOMContentLoaded", async () => {
  // Load settings for global use
  try {
    App.instellingen = await Api.get("/instellingen/");
    document.title = (App.instellingen.bedrijfsnaam || "Boekhouding NL");
  } catch (_) {}

  // Year selector
  const yearSel = document.getElementById("jaar-select");
  if (yearSel) {
    const thisYear = new Date().getFullYear();
    for (let y = thisYear; y >= thisYear - 5; y--) {
      const opt = document.createElement("option");
      opt.value = y; opt.textContent = y;
      if (y === App.jaar) opt.selected = true;
      yearSel.appendChild(opt);
    }
    yearSel.addEventListener("change", () => {
      App.jaar = parseInt(yearSel.value);
      navigate(location.hash || "#dashboard");
    });
  }

  navigate(location.hash || "#dashboard");
});
