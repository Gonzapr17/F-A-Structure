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
    "Profit Planning": "Profit Planning",
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


def main():
    hierarchy = load_json("processed/jerarquia.json")
    canonical = load_json("processed/procesos-canonicos.json")["by_gerencia"]

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
