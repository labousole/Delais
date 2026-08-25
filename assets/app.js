const PRESTATION_LABELS = {
  prime_activite: "Prime d'activité",
  apl: "APL / aides au logement",
  rsa: "RSA",
  aah: "AAH",
};

// Seuils indicatifs (en jours) pour le badge "tampon". Volontairement
// simples : au-delà de 45 j on affiche "en retard", en-dessous de 15 j
// "dans les temps", entre les deux "sous tension". Ajustable librement.
function stampFor(avgDays) {
  if (avgDays === null) return { cls: "warn", label: "Données manquantes" };
  if (avgDays <= 15) return { cls: "ok", label: "Dans les temps" };
  if (avgDays <= 45) return { cls: "warn", label: "Sous tension" };
  return { cls: "late", label: "En retard" };
}

function average(delais) {
  const values = Object.values(delais || {});
  if (!values.length) return null;
  return Math.round(values.reduce((a, b) => a + b, 0) / values.length);
}

function cardTemplate(dept) {
  const avg = average(dept.delais);
  const stamp = stampFor(avg);
  const rows = Object.entries(dept.delais || {})
    .map(
      ([key, days]) => `
        <div class="dept-row">
          <span>${PRESTATION_LABELS[key] || key}</span>
          <span class="val">${days} j</span>
        </div>`
    )
    .join("");

  return `
    <article class="dept-card" data-name="${dept.name.toLowerCase()}" data-code="${dept.code}">
      <div class="dept-head">
        <div>
          <div class="dept-code">Dép. ${dept.code}</div>
          <h3 class="dept-name">${dept.name}</h3>
        </div>
        <span class="stamp ${stamp.cls}">${stamp.label}</span>
      </div>
      <div class="dept-rows">
        ${rows || '<p style="color:var(--ink-soft)">Aucun délai détecté pour l\'instant.</p>'}
      </div>
      <a class="source" href="${dept.source_url}" target="_blank" rel="noopener">Voir la source officielle →</a>
    </article>
  `;
}

async function loadData() {
  const res = await fetch("data/delais.json", { cache: "no-store" });
  if (!res.ok) throw new Error("Impossible de charger data/delais.json");
  return res.json();
}

function renderHeroStat(payload) {
  const all = payload.departments.flatMap((d) => Object.values(d.delais || {}));
  const avg = all.length ? Math.round(all.reduce((a, b) => a + b, 0) / all.length) : null;
  const el = document.getElementById("hero-avg");
  if (el) el.textContent = avg !== null ? avg : "—";
  const dateEl = document.getElementById("hero-date");
  if (dateEl) {
    const d = new Date(payload.generated_at);
    dateEl.textContent = d.toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" });
  }
}

function main() {
  const grid = document.getElementById("grid");
  const searchInput = document.getElementById("dept-search");
  const chips = Array.from(document.querySelectorAll(".chip[data-filter]"));
  const emptyState = document.getElementById("empty-state");

  let payload = null;
  let activeFilter = "all";

  function applyFilters() {
    const query = searchInput.value.trim().toLowerCase();
    let depts = payload.departments;

    if (query) {
      depts = depts.filter(
        (d) => d.name.toLowerCase().includes(query) || d.code.includes(query)
      );
    }

    if (activeFilter !== "all") {
      depts = depts.filter((d) => stampFor(average(d.delais)).cls === activeFilter);
    }

    depts = [...depts].sort((a, b) => (average(b.delais) || 0) - (average(a.delais) || 0));

    grid.innerHTML = depts.map(cardTemplate).join("");
    emptyState.hidden = depts.length !== 0;
  }

  loadData()
    .then((data) => {
      payload = data;
      renderHeroStat(payload);
      applyFilters();
    })
    .catch((err) => {
      grid.innerHTML = `<p class="empty-state">Erreur de chargement des données : ${err.message}</p>`;
      console.error(err);
    });

  searchInput.addEventListener("input", () => payload && applyFilters());
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.setAttribute("aria-pressed", "false"));
      chip.setAttribute("aria-pressed", "true");
      activeFilter = chip.dataset.filter;
      applyFilters();
    });
  });
}

document.addEventListener("DOMContentLoaded", main);
