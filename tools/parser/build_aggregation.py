"""Etapa 4 — Agregación organizacional (spec sección "Etapa 4").

Para cada nodo del organigrama (Jefatura/Gerencia/Gerencia General/Dirección)
en processed/jerarquia.json, calcula por agregación de sus dependientes:
  1. Áreas/procesos dependientes (rollup de processed/procesos-canonicos.json)
  2. Complejidad (fórmula validada con Gonzalo, ver docstring de calc_complexity)
  3. Principales responsabilidades (síntesis de los procesos rolled-up)
  4. Dimensiones que se destacan (concentración temática o de seniority)
  5. Nómina dependiente total (de la jerarquía real, no sólo lo parseado)
  6. Distribución de seniority del staff dependiente
  7. Organigrama local (nodo + hijos directos, para el gráfico simple)

Limitación conocida: los PDFs de posición sólo declaran el Department/Gerencia
del puesto, no la Jefatura (Coordinador) a la que reporta — así lo señala la
spec ("la estructura jerárquica derivable directamente de las descripciones
de posición no incluye la pertenencia a Jefatura"). Por eso el rollup de
procesos en un nodo Jefatura es idéntico al de su Gerencia padre (no se puede
desagregar más fino todavía); queda marcado con "granularity": "gerencia".
Nómina y seniority sí son exactos por nodo porque salen directamente del
Excel de jerarquía, no de los PDFs parseados.
"""
import json
import math
from collections import Counter
from pathlib import Path

STAFF_LEVELS = ["Analyst Jr", "Analyst", "Analyst Senior", "Administrative"]

# Department (tal como aparece en el Excel de jerarquía) -> gerencia canónica
# de Fase 2 (donde Kinto/Connected quedaron bajo AP & AR). Sólo estas 3
# gerencias tienen PDFs de posición parseados hoy.
DEPARTMENT_TO_PROCESSED_GERENCIA = {
    "Accounting": "Accounting",
    "AP & AR": "AP & AR",
    "Kinto": "AP & AR",
    "Profit Planning": "Profit Planning",
}

# Impacto declarado por el gerente ("Importance": High/Mid) leído a mano de
# data/vision-gerentes/{Accounting,"Profit planning"}.pdf — son las únicas dos
# gerencias cuyo documento trae esa columna. AP & AR usa otro formato
# (organigrama + bullets por seniority, sin rating de impacto), así que no
# hay dato para sus procesos: se reporta como "Sin dato", no se inventa un
# valor neutro, para no penalizar a esa gerencia por un problema de formato
# del documento fuente (ver discusión con Gonzalo). Este indicador se muestra
# aparte de "complejidad" — no se mezcla en el score por la misma razón.
DECLARED_IMPACT = {
    "Accounting": {
        "Annual Legal Financial Statements Preparation": "High",
        "Monthly Closing Reporting via Conets": "High",
        "Monthly Accounting Package to TMC": "High",
        "SOX Control Matrix & Internal Procedures": "High",
        "Inflation Adjustment of Non-Monetary Assets": "High",
        "Non-Operating Results Determination & Budget Follow-up": "High",
        "USD Position Forecast & Follow-up": "High",
        "TPA Units Accounting & Intercompany Control": "High",
        "Monthly Balance Sheet Account Reconciliations": "High",
        "Fixed Assets / Vehicles Impairment Testing": "Mid",
        "Dividend / IOE Payment Calculation": "High",
        "Finished Goods Inventory Taking & Booking": "High",
        "Monthly Tax Credit Reversal": "High",
        "Government Bloco K Inventory Reporting (Brazil)": "High",
        "Inventory in Transit / Importation Tracking": "High",
        "Fixed Assets Inventory Taking & Disposal Management": "High",
        "Accounting Information for External Surveys & Reports (INDEC/Sustainability/Press)": "Mid",
        "Bank Reconciliation & Loans Follow-up": "High",
        "Invoicing Dashboard Control & Credit Notes": "High",
    },
    "Profit Planning": {
        "Financial Analysis of Profit Margins": "High",
        "Financial Forecasting": "High",
        "Scenario Planning": "High",
        "Management Reporting & Dashboards": "High",
        "Monthly Financial Closing Process Oversight": "High",
        "Financial Statement Preparation & P&L Analysis by Business Unit": "High",
        "Budget vs. Actual / Profitability Variance Analysis": "High",
        "Profitability Analysis (Revenue/Cost/Margin)": "High",
        "KPI Development & Monitoring (Profitability)": "High",
        "Product/Service Profitability Assessment": "High",
        # Sin rating explícito en la tabla "Importance" del documento:
        "Continuous Process Improvement": None,
        "Cross-functional Collaboration for Monthly Close": None,
        "Budgeting & Alignment with Profit Goals": None,
        "Financial Risk Management (Profit Planning)": None,
    },
    # AP & AR: el documento no tiene columna de Importance -> sin datos.
}

# Buckets temáticos para detectar concentración de procesos en un nodo.
# Simple keyword-matching sobre el nombre del proceso canónico.
THEMATIC_BUCKETS = {
    "Kinto": ["kinto"],
    "Connected": ["connected"],
    "Fixed Assets / Inventario": ["fixed assets", "inventory", "inventor"],
    "Compliance / SOX / Tax": ["sox", "tax", "compliance", "government", "rota 2030"],
    "Cierre / Reporting Mensual": ["closing", "clos", "conets", "tmc", "reporting", "report"],
    "Conciliaciones": ["reconcil"],
    "Riesgo / Crédito": ["risk", "credit", "audit"],
    "Presupuesto / Variance": ["budget", "variance", "forecast"],
    "Rentabilidad": ["profitab", "kpi"],
    "Cobranzas / Clientes": ["collection", "portfolio", "customer", "dealer", "aging"],
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def shannon_entropy_normalized(counts):
    total = sum(counts)
    nonzero = [c for c in counts if c > 0]
    if total == 0 or len(nonzero) <= 1:
        return 0.0
    probs = [c / total for c in nonzero]
    h = -sum(p * math.log2(p) for p in probs)
    h_max = math.log2(len(counts))
    return h / h_max if h_max > 0 else 0.0


def build_indices(hierarchy):
    by_code = {p["code"]: p for p in hierarchy["positions"]}
    children_of = {p["code"]: p["children_codes"] for p in hierarchy["positions"]}

    def descendants(code):
        out = []
        for c in children_of.get(code, []):
            out.append(c)
            out.extend(descendants(c))
        return out

    return by_code, descendants


def find_gerencia_for_node(node, by_code, descendants):
    """Determina qué gerencia procesada (si alguna) cubre a este nodo.

    Un nodo Gerencia usa su propio Department. Un nodo Jefatura usa el
    Department de la Gerencia (Manager) de la que depende. Gerencia General y
    Dirección pueden cubrir más de una gerencia procesada entre sus hijos.
    """
    if node["department"] in DEPARTMENT_TO_PROCESSED_GERENCIA:
        return [DEPARTMENT_TO_PROCESSED_GERENCIA[node["department"]]]

    # Nodo de nivel superior (Gerencia General / Dirección): juntar todas las
    # gerencias procesadas entre los descendientes de tipo "Gerencia".
    found = set()
    for code in descendants(node["code"]):
        desc = by_code[code]
        if desc.get("node_type") == "Gerencia" and desc["department"] in DEPARTMENT_TO_PROCESSED_GERENCIA:
            found.add(DEPARTMENT_TO_PROCESSED_GERENCIA[desc["department"]])
    return sorted(found)


def rollup_processes(gerencias, canonical_by_gerencia):
    procesos = []
    for g in gerencias:
        for proc in canonical_by_gerencia[g]["canonical_processes"]:
            procesos.append({"gerencia": g, "process": proc["process"], "source_positions": proc["source_positions"]})
    return procesos


def synth_responsibilities(procesos, limit=6):
    """Top procesos por cantidad de puestos de origen, como síntesis de
    'principales responsabilidades' del nodo."""
    ranked = sorted(procesos, key=lambda p: len(p["source_positions"]), reverse=True)
    return [p["process"] for p in ranked[:limit]]


def detect_thematic_concentration(procesos, threshold=0.25):
    if not procesos:
        return []
    total = len(procesos)
    bucket_counts = Counter()
    for p in procesos:
        name_l = p["process"].lower()
        for bucket, keywords in THEMATIC_BUCKETS.items():
            if any(kw in name_l for kw in keywords):
                bucket_counts[bucket] += 1
    out = []
    for bucket, count in bucket_counts.most_common():
        share = count / total
        if share >= threshold:
            out.append({"dimension": bucket, "procesos": count, "share_pct": round(share * 100, 1)})
    return out


def seniority_distribution(node_code, by_code, descendants):
    staff = [by_code[c] for c in descendants(node_code) if by_code[c]["hierarchical_level"] in STAFF_LEVELS]
    hist = Counter(s["hierarchical_level"] for s in staff)
    return {level: hist.get(level, 0) for level in STAFF_LEVELS}, len(staff)


def declared_impact_summary(procesos):
    """Impacto declarado por el gerente (Importance: High/Mid del PDF de
    visión), reportado APARTE de la complejidad — no se mezcla en el score
    porque solo 2 de las 3 gerencias con datos tienen esa columna en su
    documento (ver DECLARED_IMPACT), y mezclarlo penalizaría a la gerencia
    cuyo documento no la incluye, no a sus procesos en sí."""
    if not procesos:
        return {"distribution": {}, "share_alto_pct": None, "cobertura_impacto_pct": None, "note": "Sin procesos para este nodo."}
    dist = Counter()
    rated = 0
    unrated_gerencias = set()
    for p in procesos:
        impact = DECLARED_IMPACT.get(p["gerencia"], {}).get(p["process"])
        dist[impact or "Sin dato"] += 1
        if impact:
            rated += 1
        else:
            unrated_gerencias.add(p["gerencia"])
    total = len(procesos)
    note = None
    if rated < total:
        if "AP & AR" in unrated_gerencias:
            note = (
                "Cobertura parcial: el PDF de visión de AP & AR no trae columna de Importance, "
                "así que sus procesos quedan como 'Sin dato' (no es que tengan bajo impacto)."
            )
        else:
            note = (
                f"Cobertura parcial: {total - rated} de {total} procesos no tienen un rating de "
                "Importance explícito en la tabla del documento de visión (no figuran en esa sección, "
                "no es que tengan bajo impacto)."
            )
    return {
        "distribution": dict(dist),
        "share_alto_pct": round(dist.get("High", 0) / total * 100, 1),
        "cobertura_impacto_pct": round(rated / total * 100, 1),
        "note": note,
    }


def data_coverage(gerencias_fuente, node_type, staff_count, parsed_counts_by_gerencia, gerencia_staff_totals):
    """% de la nómina real (staff) que ya tiene PDF de posición parseado.

    Reporta dos números distintos porque conflan cosas distintas:
      - pct_cobertura_gerencias_con_datos: de las gerencias que sí tienen
        algún proceso relevado bajo este nodo, qué fracción de SU staff está
        parseada. Siempre es exacto y comparable.
      - pct_cobertura_total_nodo: de TODO el staff real bajo este nodo
        (incluyendo gerencias sin ningún PDF, ej. Cost/Treasury/Budget/TAX),
        qué fracción está parseada. Sólo tiene sentido para nodos cuyo
        staff_count local abarca la organización completa bajo ellos
        (Gerencia General / Dirección) o coincide 1:1 con una gerencia
        (Gerencia) — NO para Jefatura, porque su staff_count local es sólo
        una fracción de la gerencia y el numerador (PDFs parseados) no se
        puede atribuir a un Coordinador específico; usar el staff local ahí
        da coberturas de +100% sin sentido. Para Jefatura sólo se informa el
        primer número, con nota explícita de que es el de la Gerencia padre.
    """
    parsed = sum(parsed_counts_by_gerencia.get(g, 0) for g in gerencias_fuente)
    total_gerencias = sum(gerencia_staff_totals.get(g, 0) for g in gerencias_fuente)
    pct_within_scope = round(parsed / total_gerencias * 100, 1) if total_gerencias else None

    pct_total_nodo = None
    if node_type != "Jefatura":
        pct_total_nodo = round(parsed / staff_count * 100, 1) if staff_count else None

    notes = []
    if node_type == "Jefatura" and gerencias_fuente:
        notes.append(
            "Corresponde a la Gerencia padre completa (no se puede desagregar por Jefatura/Coordinador "
            "con los datos actuales)."
        )
    if pct_within_scope is None or pct_within_scope < 100:
        notes.append(
            "Score de complejidad/impacto de este nodo es provisorio: se recalcula a medida "
            "que se cargan más descripciones de puesto (ver Etapa 5 de la spec)."
        )

    return {
        "puestos_parseados": parsed,
        "staff_real_total_gerencias_con_datos": total_gerencias,
        "pct_cobertura_gerencias_con_datos": pct_within_scope,
        "staff_real_total_nodo": staff_count,
        "pct_cobertura_total_nodo": pct_total_nodo,
        "note": " ".join(notes) or None,
    }


def calc_complexity(process_diversity, seniority_dispersion, has_process_data):
    """complejidad = 0.6 * diversidad_normalizada(procesos) + 0.4 * dispersion_normalizada(seniority)

    Fórmula validada con Gonzalo. La diversidad de procesos se normaliza contra
    el máximo observado entre los nodos que sí tienen datos de procesos (no
    hay catálogo total fijo). Si el nodo no tiene datos de procesos (gerencias
    sin PDFs relevados todavía: Cost/Treasury/Budget/TAX/Value Chain), no se
    computa un score comparable — se marca explícitamente en vez de asumir 0.
    """
    if not has_process_data:
        return None
    return {"process_diversity": process_diversity, "seniority_dispersion": round(seniority_dispersion, 3)}


def parsed_position_counts_by_gerencia():
    """Cuántos PDFs de posición (processed/posiciones.json) hay por gerencia,
    con el mismo mapeo Department->Gerencia usado en Fase 2/3 (Kinto/Connected
    bajo AP & AR)."""
    positions = load_json("processed/posiciones.json")["positions"]
    counts = Counter()
    for p in positions:
        gerencia = DEPARTMENT_TO_PROCESSED_GERENCIA.get(p["department"], p["department"])
        counts[gerencia] += 1
    return counts


def gerencia_staff_totals_from_hierarchy(hierarchy):
    """Total de staff (Analyst Jr/Analyst/Analyst Senior/Administrative) por
    gerencia procesada, contando TODA la jerarquía (no sólo bajo un nodo
    puntual) — es el denominador correcto para la cobertura de datos."""
    totals = Counter()
    for p in hierarchy["positions"]:
        if p["hierarchical_level"] in STAFF_LEVELS:
            gerencia = DEPARTMENT_TO_PROCESSED_GERENCIA.get(p["department"])
            if gerencia:
                totals[gerencia] += 1
    return totals


def main():
    hierarchy = load_json("processed/jerarquia.json")
    canonical = load_json("processed/procesos-canonicos.json")["by_gerencia"]
    parsed_counts = parsed_position_counts_by_gerencia()
    gerencia_staff_totals = gerencia_staff_totals_from_hierarchy(hierarchy)

    by_code, descendants = build_indices(hierarchy)
    org_nodes = [p for p in hierarchy["positions"] if p["is_org_node"]]

    # Paso 1: recolectar componentes crudos de cada nodo.
    raw = {}
    max_process_diversity = 0
    for node in org_nodes:
        gerencias = find_gerencia_for_node(node, by_code, descendants)
        granularity = "gerencia" if node["node_type"] == "Jefatura" else "nodo"
        procesos = rollup_processes(gerencias, canonical) if gerencias else []
        seniority_dist, staff_count = seniority_distribution(node["code"], by_code, descendants)
        dispersion = shannon_entropy_normalized([seniority_dist[l] for l in STAFF_LEVELS])
        n_descendants = len(descendants(node["code"]))

        process_diversity = len(procesos)
        if procesos:
            max_process_diversity = max(max_process_diversity, process_diversity)

        raw[node["code"]] = {
            "node": node,
            "gerencias_fuente": gerencias,
            "granularity": granularity,
            "procesos": procesos,
            "seniority_dist": seniority_dist,
            "staff_count": staff_count,
            "dispersion": dispersion,
            "n_descendants": n_descendants,
        }

    # Paso 2: normalizar diversidad de procesos contra el máximo observado y
    # calcular el score de complejidad para los nodos con datos.
    scored_codes = [c for c, v in raw.items() if v["procesos"]]
    scores = {}
    for code in scored_codes:
        v = raw[code]
        diversity_norm = v["procesos"] and (len(v["procesos"]) / max_process_diversity) or 0.0
        score = 0.6 * diversity_norm + 0.4 * v["dispersion"]
        scores[code] = score

    # Terciles sobre los nodos que sí tienen score (bucket relativo, no fijo).
    ordered = sorted(scores.values())

    def bucket_for(score):
        n = len(ordered)
        t1 = ordered[n // 3]
        t2 = ordered[(2 * n) // 3]
        if score <= t1:
            return "Baja"
        if score <= t2:
            return "Media"
        return "Alta"

    # Paso 3: armar la salida final por nodo.
    by_node_out = {}
    for code, v in raw.items():
        node = v["node"]
        procesos = v["procesos"]
        complexity = None
        if code in scores:
            complexity = {
                "process_diversity": len(procesos),
                "seniority_dispersion": round(v["dispersion"], 3),
                "score": round(scores[code], 3),
                "bucket": bucket_for(scores[code]),
            }

        by_node_out[code] = {
            "name": node["name"],
            "node_type": node["node_type"],
            "department": node["department"],
            "organization": node["organization"],
            "parent_code": node["parent_code"],
            "children_codes": node["children_codes"],
            "areas_procesos_dependientes": {
                "gerencias_fuente": v["gerencias_fuente"],
                "granularity": v["granularity"],
                "procesos": sorted({p["process"] for p in procesos}),
                "note": (
                    None if procesos else
                    "Sin procesos parseados todavía para esta gerencia (no hay PDFs de posición relevados)."
                ),
            },
            "complejidad": complexity if complexity else {
                "process_diversity": None,
                "seniority_dispersion": round(v["dispersion"], 3),
                "score": None,
                "bucket": "Sin datos suficientes",
            },
            "principales_responsabilidades": (
                synth_responsibilities(procesos) if procesos else
                ["Sin datos de puestos parseados todavía para esta gerencia."]
            ),
            "dimensiones_destacadas": detect_thematic_concentration(procesos),
            "impacto_declarado": declared_impact_summary(procesos),
            "cobertura_datos": data_coverage(
                v["gerencias_fuente"], node["node_type"], v["staff_count"], parsed_counts, gerencia_staff_totals
            ),
            "nomina_dependiente_total": v["n_descendants"],
            "seniority_distribution": v["seniority_dist"],
            "staff_count": v["staff_count"],
            "organigrama_local": {
                "self": {"code": code, "name": node["name"], "node_type": node["node_type"]},
                "children": [
                    {
                        "code": c,
                        "name": by_code[c]["name"],
                        "node_type": by_code[c].get("node_type"),
                        "is_org_node": by_code[c]["is_org_node"],
                        "hierarchical_level": by_code[c]["hierarchical_level"],
                    }
                    for c in node["children_codes"]
                ],
            },
        }

    out_path = Path("processed/agregacion-organizacional.json")
    out_path.write_text(
        json.dumps({"complexity_formula": "0.6*diversidad_normalizada(procesos) + 0.4*dispersion_normalizada(seniority), bucketizado por terciles",
                    "by_node": by_node_out}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for node_type in ["Dirección", "Gerencia General", "Gerencia", "Jefatura"]:
        codes = [c for c, v in by_node_out.items() if v["node_type"] == node_type]
        print(f"{node_type}: {len(codes)} nodos")

    print(f"\nGuardado en {out_path}")


if __name__ == "__main__":
    main()
