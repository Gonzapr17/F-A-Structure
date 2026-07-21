"""Fase 5 — Dashboard interactivo (spec sección 4).

Genera dashboard/index.html: un archivo HTML autocontenido (sin dependencias
externas) que embebe los 5 JSON de processed/ y renderiza las dos vistas de
la spec:
  Vista A - Validación de procesos por gerencia (bottom-up vs top-down)
  Vista B - Reporte por nodo organizacional

Correr este script de nuevo regenera el dashboard con los datos más
recientes de processed/*.json (carga incremental: no hace falta tocar el
HTML a mano cuando cambian los JSON).
"""
import json
from pathlib import Path


def load(name):
    return json.loads(Path(f"processed/{name}").read_text(encoding="utf-8"))


def embed(obj):
    """JSON compacto y seguro para meter dentro de un <script> inline."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


HTML_TEMPLATE = r"""<!doctype html>
<meta charset="utf-8" />
<title>F&amp;A Structure — Mapeo y Validación de Procesos</title>
<style>
:root {
  --ink: #1c1b18;
  --ink-soft: #5c5952;
  --ink-muted: #8b8880;
  --paper: #f7f5f0;
  --card: #ffffff;
  --line: #e4e1d8;
  --brand: #1f4e4c;
  --brand-soft: #e7f0ef;
  --good: #0ca30c;
  --warning: #b9790a;
  --serious: #c9502b;
  --critical: #d03b3b;
  --good-bg: #e6f6e6;
  --warning-bg: #fdf1d9;
  --serious-bg: #fbe5da;
  --critical-bg: #fbe3e3;
  --seq-1: #86b6ef;
  --seq-2: #3987e5;
  --seq-3: #1c5cab;
  --admin: #b0a99c;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    --ink: #f2f0ea;
    --ink-soft: #c3c0b6;
    --ink-muted: #8b8880;
    --paper: #14140f;
    --card: #1c1c17;
    --line: #322f27;
    --brand: #5aa9a4;
    --brand-soft: #1d2d2b;
    --good: #34c759;
    --warning: #fab219;
    --serious: #ec835a;
    --critical: #e66767;
    --good-bg: #163019;
    --warning-bg: #332708;
    --serious-bg: #331d12;
    --critical-bg: #331414;
    --seq-1: #2a4f7a;
    --seq-2: #3987e5;
    --seq-3: #86b6ef;
    --admin: #6b6558;
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --ink: #f2f0ea;
  --ink-soft: #c3c0b6;
  --ink-muted: #8b8880;
  --paper: #14140f;
  --card: #1c1c17;
  --line: #322f27;
  --brand: #5aa9a4;
  --brand-soft: #1d2d2b;
  --good: #34c759;
  --warning: #fab219;
  --serious: #ec835a;
  --critical: #e66767;
  --good-bg: #163019;
  --warning-bg: #332708;
  --serious-bg: #331d12;
  --critical-bg: #331414;
  --seq-1: #2a4f7a;
  --seq-2: #3987e5;
  --seq-3: #86b6ef;
  --admin: #6b6558;
  color-scheme: dark;
}

* { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  -webkit-font-smoothing: antialiased;
}
body { overflow-x: hidden; }
h1, h2, h3, h4 { text-wrap: balance; margin: 0; }
button, select, textarea, input { font-family: inherit; }
.tabular { font-variant-numeric: tabular-nums; }

.shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 28px 24px 80px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.masthead {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--line);
}
.masthead .eyebrow {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--brand);
  font-weight: 600;
}
.masthead h1 {
  font-size: 26px;
  font-weight: 650;
  letter-spacing: -0.01em;
}
.masthead p {
  margin: 2px 0 0;
  color: var(--ink-soft);
  font-size: 14px;
  max-width: 62ch;
}

.tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--line);
}
.tab {
  appearance: none;
  border: none;
  background: none;
  color: var(--ink-soft);
  font-size: 14px;
  font-weight: 550;
  padding: 10px 4px;
  margin-right: 20px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: color .15s, border-color .15s;
}
.tab:hover { color: var(--ink); }
.tab.active { color: var(--brand); border-color: var(--brand); }
.tab:focus-visible { outline: 2px solid var(--brand); outline-offset: 2px; }

.view { display: none; flex-direction: column; gap: 18px; }
.view.active { display: flex; }

.selectorbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.selectorbar label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-muted);
  font-weight: 600;
}
select.picker {
  appearance: none;
  background: var(--card);
  border: 1px solid var(--line);
  color: var(--ink);
  font-size: 14px;
  font-weight: 550;
  padding: 9px 34px 9px 12px;
  border-radius: 8px;
  min-width: 260px;
  background-image: linear-gradient(45deg, transparent 50%, var(--ink-soft) 50%), linear-gradient(135deg, var(--ink-soft) 50%, transparent 50%);
  background-position: calc(100% - 18px) center, calc(100% - 13px) center;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
}
select.picker:focus-visible { outline: 2px solid var(--brand); outline-offset: 1px; }

.breadcrumb {
  font-size: 13px;
  color: var(--ink-muted);
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.breadcrumb .sep { color: var(--line); }
.breadcrumb .current { color: var(--ink); font-weight: 600; }

.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 18px 20px;
}
.card h3 {
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-muted);
  font-weight: 650;
  margin-bottom: 12px;
}

.tiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}
.tile {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.tile .label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-muted);
  font-weight: 600;
}
.tile .value {
  font-size: 26px;
  font-weight: 650;
  letter-spacing: -0.01em;
}
.tile .sub { font-size: 12.5px; color: var(--ink-soft); }
.tile.accent { border-color: var(--brand); background: var(--brand-soft); }

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  white-space: nowrap;
}
.chip .dot { width: 7px; height: 7px; border-radius: 50%; flex: none; }
.chip.good { background: var(--good-bg); color: var(--good); }
.chip.warning { background: var(--warning-bg); color: var(--warning); }
.chip.serious { background: var(--serious-bg); color: var(--serious); }
.chip.critical { background: var(--critical-bg); color: var(--critical); }
.chip.neutral { background: var(--line); color: var(--ink-soft); }

.proc-table { display: flex; flex-direction: column; gap: 0; }
.proc-row {
  border-top: 1px solid var(--line);
  padding: 12px 0;
}
.proc-row:first-child { border-top: none; }
.proc-head {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  justify-content: space-between;
}
.proc-head .left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.proc-name { font-size: 14.5px; font-weight: 550; }
.proc-count { font-size: 12.5px; color: var(--ink-muted); flex: none; }
.proc-caret { color: var(--ink-muted); transition: transform .15s; flex: none; }
.proc-row.open .proc-caret { transform: rotate(90deg); }
.proc-detail { display: none; padding: 12px 4px 4px 4px; }
.proc-row.open .proc-detail { display: block; }
.proc-detail .evidence {
  font-size: 13px;
  color: var(--ink-soft);
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px 12px;
  margin-bottom: 10px;
}
.proc-detail .tasklist { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
.taskitem { font-size: 13px; color: var(--ink-soft); display: flex; gap: 8px; }
.taskitem .pos { color: var(--ink); font-weight: 600; flex: none; }
.wording-label {
  font-size: 11.5px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-muted);
  font-weight: 650;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
textarea.wording {
  width: 100%;
  min-height: 78px;
  margin-top: 6px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--ink);
  font-size: 13.5px;
  line-height: 1.45;
  padding: 10px 12px;
  resize: vertical;
}
textarea.wording:focus-visible { outline: 2px solid var(--brand); outline-offset: 1px; }
.resetbtn {
  appearance: none;
  border: none;
  background: none;
  color: var(--brand);
  font-size: 11.5px;
  font-weight: 650;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.edited-badge { color: var(--brand); font-weight: 650; }

.notebox {
  font-size: 13px;
  color: var(--ink-soft);
  background: var(--brand-soft);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px 14px;
  line-height: 1.5;
}

.progress-track {
  height: 8px;
  border-radius: 999px;
  background: var(--line);
  overflow: hidden;
}
.progress-fill { height: 100%; background: var(--brand); border-radius: 999px 0 0 999px; }

.seniority-bars { display: flex; flex-direction: column; gap: 8px; }
.seniority-row { display: grid; grid-template-columns: 110px 1fr 40px; align-items: center; gap: 10px; }
.seniority-row .lbl { font-size: 12.5px; color: var(--ink-soft); }
.seniority-row .barwrap { background: var(--line); border-radius: 4px; height: 12px; overflow: hidden; }
.seniority-row .barfill { height: 100%; border-radius: 4px; }
.seniority-row .cnt { font-size: 12.5px; text-align: right; color: var(--ink-muted); }

.chiprow { display: flex; flex-wrap: wrap; gap: 8px; }

.resplist { display: flex; flex-direction: column; gap: 8px; padding-left: 0; margin: 0; list-style: none; }
.resplist li {
  font-size: 14px;
  padding: 8px 12px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.resplist li b { font-variant-numeric: tabular-nums; color: var(--ink-muted); margin-right: 6px; font-weight: 600; }

.org-tree { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.org-self {
  background: var(--brand);
  color: #fff;
  border-radius: 10px;
  padding: 10px 18px;
  font-size: 13.5px;
  font-weight: 650;
  text-align: center;
  max-width: 320px;
}
.org-self .sub { font-weight: 500; font-size: 11.5px; opacity: .85; }
.org-connector { width: 1px; height: 16px; background: var(--line); }
.org-children {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  max-width: 100%;
  overflow-x: auto;
  padding: 4px 2px;
}
.org-child {
  border: 1px solid var(--line);
  background: var(--card);
  border-radius: 8px;
  padding: 7px 11px;
  font-size: 12px;
  min-width: 96px;
  max-width: 170px;
  text-align: center;
  line-height: 1.35;
}
.org-child .name { font-weight: 600; color: var(--ink); }
.org-child .lvl { color: var(--ink-muted); font-size: 10.5px; text-transform: uppercase; letter-spacing: .04em; margin-top: 2px; }
.org-child.is-node { border-color: var(--brand); }

.emptystate {
  padding: 40px 20px;
  text-align: center;
  color: var(--ink-soft);
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}
.emptystate .big { font-size: 34px; }

.footer-note {
  font-size: 12px;
  color: var(--ink-muted);
  padding-top: 8px;
  border-top: 1px solid var(--line);
}

@media (max-width: 640px) {
  .seniority-row { grid-template-columns: 90px 1fr 32px; }
}
</style>

<div class="shell">
  <div class="masthead">
    <div class="eyebrow">TLAC F&amp;A · Herramienta de Mapeo y Validación de Procesos</div>
    <h1>Estructura de Finanzas — Procesos y Organigrama</h1>
    <p>Vista A cruza lo que declaran los puestos (bottom-up) contra la visión de cada gerente (top-down). Vista B agrega nómina, complejidad y responsabilidades por nodo del organigrama.</p>
  </div>

  <div class="tabs" role="tablist">
    <button class="tab active" data-view="a" role="tab" aria-selected="true">Vista A · Validación por gerencia</button>
    <button class="tab" data-view="b" role="tab" aria-selected="false">Vista B · Reporte por nodo</button>
  </div>

  <section id="view-a" class="view active"></section>
  <section id="view-b" class="view"></section>

  <div class="footer-note">Generado desde processed/posiciones.json, procesos-canonicos.json, reconciliacion.json, jerarquia.json y agregacion-organizacional.json. Las redacciones reconciliadas son editables en este navegador (se guardan en localStorage) y no modifican los archivos fuente.</div>
</div>

<script>
const POSICIONES = @@POSICIONES_JSON@@;
const JERARQUIA = @@JERARQUIA_JSON@@;
const CANONICOS = @@CANONICOS_JSON@@;
const RECONCILIACION = @@RECONCILIACION_JSON@@;
const AGREGACION = @@AGREGACION_JSON@@;

// ---------- utilidades ----------
function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  if (attrs) for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined) continue;
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined) continue;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}

function statusChip(status) {
  const map = {
    aligned: ["good", "● Alineado"],
    solo_bottom_up: ["warning", "● Solo bottom-up"],
    solo_top_down: ["serious", "● Solo top-down"],
    sin_datos: ["neutral", "Sin datos suficientes"],
  };
  const [cls, label] = map[status] || ["neutral", status];
  return el("span", { class: "chip " + cls }, label);
}

function pct(n) { return (n === null || n === undefined) ? "—" : n.toFixed(1) + "%"; }

// ---------- localStorage para redacciones editadas ----------
function wordingKey(gerencia, process) { return "recon::" + gerencia + "::" + process; }
function getWording(gerencia, process, original) {
  const saved = localStorage.getItem(wordingKey(gerencia, process));
  return { text: saved !== null ? saved : original, edited: saved !== null && saved !== original };
}
function setWording(gerencia, process, text) {
  localStorage.setItem(wordingKey(gerencia, process), text);
}
function resetWording(gerencia, process) {
  localStorage.removeItem(wordingKey(gerencia, process));
}

function wordingBlock(gerencia, process, original) {
  const state = getWording(gerencia, process, original);
  const label = el("div", { class: "wording-label" },
    "Redacción reconciliada propuesta",
    state.edited ? el("span", { class: "edited-badge" }, "· editado") : null
  );
  const ta = el("textarea", { class: "wording", "aria-label": "Redacción reconciliada para " + process }, state.text);
  ta.addEventListener("input", () => {
    setWording(gerencia, process, ta.value);
    edited.style.display = ta.value !== original ? "inline" : "none";
  });
  const edited = label.querySelector(".edited-badge") || el("span", { class: "edited-badge", style: "display:none" }, "· editado");
  if (!label.contains(edited)) label.appendChild(edited);
  edited.style.display = state.edited ? "inline" : "none";
  const reset = el("button", { class: "resetbtn", onclick: () => {
    resetWording(gerencia, process);
    ta.value = original;
    edited.style.display = "none";
  }}, "Restaurar original");
  return el("div", {}, label, ta, el("div", { style: "margin-top:4px" }, reset));
}

// ---------- Vista A ----------
const GERENCIAS_CONOCIDAS = (() => {
  const set = new Map();
  for (const p of JERARQUIA.positions) {
    if (p.hierarchical_level === "Manager" && p.department) set.set(p.department, true);
  }
  return Array.from(set.keys()).sort();
})();

function nodeForDepartment(dept) {
  return Object.entries(AGREGACION.by_node).find(([, n]) => n.node_type === "Gerencia" && n.department === dept);
}

function renderViewA(selected) {
  const root = document.getElementById("view-a");
  root.innerHTML = "";

  const select = el("select", { class: "picker", onchange: (e) => renderViewA(e.target.value) },
    ...GERENCIAS_CONOCIDAS.map(g => el("option", { value: g, selected: g === selected ? "selected" : null }, g))
  );
  root.appendChild(el("div", { class: "selectorbar" }, el("label", {}, "Gerencia"), select));

  const recon = RECONCILIACION.by_gerencia[selected];
  const canon = CANONICOS.by_gerencia[selected];
  const nodeEntry = nodeForDepartment(selected);

  if (!recon || !canon) {
    const [, node] = nodeEntry || [undefined, null];
    root.appendChild(el("div", { class: "card" },
      el("div", { class: "emptystate" },
        el("div", { class: "big" }, "—"),
        el("div", {}, el("b", {}, "Sin PDFs de posición relevados todavía para " + selected + ".")),
        node ? el("div", {}, "Nómina real según jerarquía: " + node.nomina_dependiente_total + " personas dependientes. Cobertura de datos: 0%.") : null
      )
    ));
    return;
  }

  // completitud de carga
  const cov = nodeEntry ? nodeEntry[1].cobertura_datos : null;
  root.appendChild(el("div", { class: "card" },
    el("h3", {}, "Completitud de carga"),
    el("div", { style: "display:flex;justify-content:space-between;font-size:13px;color:var(--ink-soft);margin-bottom:6px" },
      el("span", {}, (cov ? cov.puestos_parseados : canon.position_count) + " puestos parseados de " + (cov ? cov.staff_real_total_gerencias_con_datos : canon.position_count) + " reales"),
      el("span", { class: "tabular" }, cov ? pct(cov.pct_cobertura_gerencias_con_datos) : "100%")
    ),
    el("div", { class: "progress-track" }, el("div", { class: "progress-fill", style: "width:" + (cov ? cov.pct_cobertura_gerencias_con_datos : 100) + "%" }))
  ));

  // semaforo resumen
  const s = recon.summary;
  root.appendChild(el("div", { class: "tiles" },
    el("div", { class: "tile" }, el("div", { class: "label" }, "Alineados"), el("div", { class: "value tabular" }, String(s.aligned)), statusChip("aligned")),
    el("div", { class: "tile" }, el("div", { class: "label" }, "Solo bottom-up"), el("div", { class: "value tabular" }, String(s.solo_bottom_up)), statusChip("solo_bottom_up")),
    el("div", { class: "tile" }, el("div", { class: "label" }, "Solo top-down"), el("div", { class: "value tabular" }, String(s.solo_top_down)), statusChip("solo_top_down")),
  ));

  if (recon.note) root.appendChild(el("div", { class: "notebox" }, recon.note));

  // tabla de procesos
  const rows = [];
  const alignedByProc = new Map(recon.aligned.map(a => [a.process, a]));
  const soloBUByProc = new Map(recon.solo_bottom_up.map(a => [a.process, a]));
  for (const cp of canon.canonical_processes) {
    if (alignedByProc.has(cp.process)) {
      rows.push({ process: cp.process, status: "aligned", source_positions: cp.source_positions, traced_tasks: cp.traced_tasks, evidence: alignedByProc.get(cp.process).top_down_evidence });
    } else if (soloBUByProc.has(cp.process)) {
      rows.push({ process: cp.process, status: "solo_bottom_up", source_positions: cp.source_positions, traced_tasks: cp.traced_tasks, wording: soloBUByProc.get(cp.process).reconciled_wording });
    } else {
      rows.push({ process: cp.process, status: "aligned", source_positions: cp.source_positions, traced_tasks: cp.traced_tasks, evidence: null });
    }
  }
  for (const t of recon.solo_top_down) {
    rows.push({ process: t.process, status: "solo_top_down", source_positions: [], traced_tasks: [], evidence: t.evidence, wording: t.reconciled_wording });
  }
  const order = { solo_top_down: 0, solo_bottom_up: 1, aligned: 2 };
  rows.sort((a, b) => order[a.status] - order[b.status] || b.source_positions.length - a.source_positions.length);

  const table = el("div", { class: "proc-table" });
  for (const r of rows) {
    const row = el("div", { class: "proc-row" });
    const head = el("div", { class: "proc-head", onclick: () => row.classList.toggle("open") },
      el("div", { class: "left" }, statusChip(r.status), el("div", { class: "proc-name" }, r.process)),
      el("div", { style: "display:flex;align-items:center;gap:10px" },
        el("div", { class: "proc-count tabular" }, r.source_positions.length ? r.source_positions.length + " puesto(s)" : "—"),
        el("div", { class: "proc-caret" }, "▸")
      )
    );
    const detail = el("div", { class: "proc-detail" });
    if (r.evidence) detail.appendChild(el("div", { class: "evidence" }, "Visión del gerente: " + r.evidence));
    if (r.traced_tasks && r.traced_tasks.length) {
      const tl = el("div", { class: "tasklist" });
      for (const t of r.traced_tasks) tl.appendChild(el("div", { class: "taskitem" }, el("span", { class: "pos" }, t.position_id + ":"), t.task));
      detail.appendChild(tl);
    }
    if (r.wording !== undefined) detail.appendChild(wordingBlock(selected, r.process, r.wording));
    row.appendChild(head);
    row.appendChild(detail);
    table.appendChild(row);
  }
  root.appendChild(el("div", { class: "card" }, el("h3", {}, "Mapa de procesos y trazabilidad"), table));

  if (recon.source_doc) root.appendChild(el("div", { class: "footer-note" }, "Fuente top-down: " + recon.source_doc));
}

// ---------- Vista B ----------
function breadcrumbFor(code) {
  const chain = [];
  let cur = code;
  while (cur) {
    const n = AGREGACION.by_node[cur];
    if (!n) break;
    chain.unshift({ code: cur, name: n.name, node_type: n.node_type });
    cur = n.parent_code;
  }
  return chain;
}

function seniorityBar(dist) {
  const order = [["Analyst Jr", "var(--seq-1)"], ["Analyst", "var(--seq-2)"], ["Analyst Senior", "var(--seq-3)"], ["Administrative", "var(--admin)"]];
  const max = Math.max(1, ...Object.values(dist));
  const wrap = el("div", { class: "seniority-bars" });
  for (const [lvl, color] of order) {
    const v = dist[lvl] || 0;
    wrap.appendChild(el("div", { class: "seniority-row" },
      el("div", { class: "lbl" }, lvl),
      el("div", { class: "barwrap" }, el("div", { class: "barfill", style: "width:" + (v / max * 100) + "%;background:" + color })),
      el("div", { class: "cnt tabular" }, String(v))
    ));
  }
  return wrap;
}

function renderViewB(selectedCode) {
  const root = document.getElementById("view-b");
  root.innerHTML = "";

  const groups = { "Dirección": [], "Gerencia General": [], "Gerencia": [], "Jefatura": [] };
  for (const [code, n] of Object.entries(AGREGACION.by_node)) groups[n.node_type].push([code, n]);
  for (const k in groups) groups[k].sort((a, b) => a[1].name.localeCompare(b[1].name));

  const select = el("select", { class: "picker", onchange: (e) => renderViewB(e.target.value) },
    ...Object.entries(groups).map(([type, items]) => el("optgroup", { label: type },
      ...items.map(([code, n]) => el("option", { value: code, selected: code === selectedCode ? "selected" : null }, n.name))
    ))
  );
  root.appendChild(el("div", { class: "selectorbar" }, el("label", {}, "Nodo"), select));

  const node = AGREGACION.by_node[selectedCode];
  if (!node) return;

  const crumbs = breadcrumbFor(selectedCode);
  const bc = el("div", { class: "breadcrumb" });
  crumbs.forEach((c, i) => {
    if (i > 0) bc.appendChild(el("span", { class: "sep" }, "›"));
    bc.appendChild(el("span", { class: i === crumbs.length - 1 ? "current" : "" }, c.name));
  });
  root.appendChild(bc);

  const complexity = node.complejidad;
  const complexChip = complexity.bucket === "Sin datos suficientes" ? "neutral" : { Baja: "good", Media: "warning", Alta: "critical" }[complexity.bucket];
  const cov = node.cobertura_datos;

  root.appendChild(el("div", { class: "tiles" },
    el("div", { class: "tile accent" }, el("div", { class: "label" }, "Nómina dependiente"), el("div", { class: "value tabular" }, String(node.nomina_dependiente_total)), el("div", { class: "sub" }, "personas bajo este nodo")),
    el("div", { class: "tile" }, el("div", { class: "label" }, "Complejidad"), el("div", { class: "value" }, el("span", { class: "chip " + complexChip }, complexity.bucket)), el("div", { class: "sub" }, complexity.score !== null ? "score " + complexity.score.toFixed(2) : "sin procesos parseados en esta gerencia")),
    el("div", { class: "tile" }, el("div", { class: "label" }, "Cobertura de datos"), el("div", { class: "value tabular" }, pct(cov.pct_cobertura_gerencias_con_datos)), el("div", { class: "sub" }, cov.puestos_parseados + " puestos parseados"))
  ));

  if (cov.note) root.appendChild(el("div", { class: "notebox" }, cov.note));

  const grid = el("div", { style: "display:grid;grid-template-columns:1fr 1fr;gap:18px" });
  if (window.innerWidth < 760) grid.style.gridTemplateColumns = "1fr";

  grid.appendChild(el("div", { class: "card" },
    el("h3", {}, "Distribución de seniority (staff dependiente)"),
    seniorityBar(node.seniority_distribution)
  ));

  const imp = node.impacto_declarado;
  const impCard = el("div", { class: "card" }, el("h3", {}, "Impacto declarado por el gerente"));
  if (imp.distribution && Object.keys(imp.distribution).length) {
    const total = Object.values(imp.distribution).reduce((a, b) => a + b, 0);
    const order = [["High", "var(--critical)"], ["Mid", "var(--warning)"], ["Sin dato", "var(--admin)"]];
    const bars = el("div", { class: "seniority-bars" });
    for (const [k, color] of order) {
      const v = imp.distribution[k] || 0;
      if (!v) continue;
      bars.appendChild(el("div", { class: "seniority-row" },
        el("div", { class: "lbl" }, k),
        el("div", { class: "barwrap" }, el("div", { class: "barfill", style: "width:" + (v / total * 100) + "%;background:" + color })),
        el("div", { class: "cnt tabular" }, String(v))
      ));
    }
    impCard.appendChild(bars);
    if (imp.note) impCard.appendChild(el("div", { class: "notebox", style: "margin-top:10px" }, imp.note));
  } else {
    impCard.appendChild(el("div", { class: "notebox" }, "Sin procesos parseados para calcular impacto en este nodo."));
  }
  grid.appendChild(impCard);
  root.appendChild(grid);

  root.appendChild(el("div", { class: "card" },
    el("h3", {}, "Principales responsabilidades"),
    el("ol", { class: "resplist" }, ...node.principales_responsabilidades.map((r, i) => el("li", {}, el("b", {}, String(i + 1) + "."), r)))
  ));

  const dims = node.dimensiones_destacadas;
  root.appendChild(el("div", { class: "card" },
    el("h3", {}, "Dimensiones que se destacan"),
    dims.length
      ? el("div", { class: "chiprow" }, ...dims.map(d => el("span", { class: "chip good" }, d.dimension + " · " + d.share_pct + "%")))
      : el("div", { class: "notebox" }, "Sin concentración temática por encima del umbral (25%) en este nodo.")
  ));

  const areas = node.areas_procesos_dependientes;
  const areasCard = el("div", { class: "card" }, el("h3", {}, "Áreas / procesos dependientes"));
  if (areas.note) {
    areasCard.appendChild(el("div", { class: "notebox" }, areas.note));
  } else {
    if (areas.granularity === "gerencia") areasCard.appendChild(el("div", { class: "notebox", style: "margin-bottom:10px" }, "Heredado de la Gerencia padre — no se puede desagregar por Jefatura/Coordinador con los datos actuales."));
    areasCard.appendChild(el("div", { class: "chiprow" }, ...areas.procesos.map(p => el("span", { class: "chip neutral" }, p))));
  }
  root.appendChild(areasCard);

  // organigrama local
  const children = node.organigrama_local.children;
  const treeCard = el("div", { class: "card" }, el("h3", {}, "Organigrama local"));
  const tree = el("div", { class: "org-tree" },
    el("div", { class: "org-self" }, node.name, el("div", { class: "sub" }, node.node_type)),
    children.length ? el("div", { class: "org-connector" }) : null,
    children.length ? el("div", { class: "org-children" }, ...children.map(c => el("div", { class: "org-child" + (c.is_org_node ? " is-node" : "") },
      el("div", { class: "name" }, c.name),
      el("div", { class: "lvl" }, c.node_type || c.hierarchical_level)
    ))) : el("div", { class: "notebox" }, "Nodo sin dependientes directos (puesto individual de base).")
  );
  treeCard.appendChild(tree);
  root.appendChild(treeCard);
}

// ---------- tabs ----------
document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(b => { b.classList.remove("active"); b.setAttribute("aria-selected", "false"); });
    document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    document.getElementById("view-" + btn.dataset.view).classList.add("active");
  });
});

renderViewA(GERENCIAS_CONOCIDAS.includes("AP & AR") ? "AP & AR" : GERENCIAS_CONOCIDAS[0]);
renderViewB("TLAC-CFO");
</script>
"""


def main():
    html = HTML_TEMPLATE
    html = html.replace("@@POSICIONES_JSON@@", embed(load("posiciones.json")))
    html = html.replace("@@JERARQUIA_JSON@@", embed(load("jerarquia.json")))
    html = html.replace("@@CANONICOS_JSON@@", embed(load("procesos-canonicos.json")))
    html = html.replace("@@RECONCILIACION_JSON@@", embed(load("reconciliacion.json")))
    html = html.replace("@@AGREGACION_JSON@@", embed(load("agregacion-organizacional.json")))

    out_path = Path("dashboard/index.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard generado en {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
