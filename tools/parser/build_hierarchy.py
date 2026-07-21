"""Etapa 1 (complemento) — Árbol organizacional a partir de data/jerarquia/.

processed/jerarquia.json no existía en el repo, así que se reconstruye acá
desde data/jerarquia/TLAC_FA_Structure_DB.xlsx (fuente de verdad para la
pertenencia jerárquica, según la spec). Cada fila del Excel es una posición
con su "Reports To"; acá se resuelve esa cadena en un árbol y se etiquetan
los 4 niveles de nodo organizacional de la spec:

    CFO              -> Dirección
    General Manager  -> Gerencia General
    Manager          -> Gerencia
    Assistant Manager -> Jefatura

El resto de los niveles (Analyst Senior/Analyst/Analyst Jr/Administrative)
son staff — cuentan para nómina/seniority pero no son "nodos" del organigrama.
"""
import json
from pathlib import Path

import openpyxl

NODE_TYPE_BY_LEVEL = {
    "CFO": "Dirección",
    "General Manager": "Gerencia General",
    "Manager": "Gerencia",
    "Assistant Manager": "Jefatura",
}
STAFF_LEVELS = {"Analyst Jr", "Analyst", "Analyst Senior", "Administrative"}


def load_rows():
    wb = openpyxl.load_workbook("data/jerarquia/TLAC_FA_Structure_DB.xlsx", data_only=True)
    ws = wb["TLAC F&A Structure"]
    cols = ["code", "organization", "location", "name", "reports_to", "hierarchical_level", "scope", "department", "status"]
    return [dict(zip(cols, r)) for r in ws.iter_rows(min_row=2, values_only=True)]


def resolve_parent(reports_to, name_to_code, all_rows):
    if reports_to in name_to_code:
        return name_to_code[reports_to]
    # El Excel a veces trunca el "Reports To" (ej. "Regional CFO" en vez de
    # "Regional CFO - Finance Director"); se resuelve por prefijo.
    for r in all_rows:
        if r["name"].startswith(reports_to):
            return r["code"]
    return None


def build():
    rows = load_rows()
    name_to_code = {r["name"]: r["code"] for r in rows}

    for r in rows:
        r["parent_code"] = resolve_parent(r["reports_to"], name_to_code, rows)
        r["is_org_node"] = r["hierarchical_level"] in NODE_TYPE_BY_LEVEL
        r["node_type"] = NODE_TYPE_BY_LEVEL.get(r["hierarchical_level"])

    children_by_parent = {}
    for r in rows:
        if r["parent_code"]:
            children_by_parent.setdefault(r["parent_code"], []).append(r["code"])
    for r in rows:
        r["children_codes"] = children_by_parent.get(r["code"], [])

    roots = [r["code"] for r in rows if r["parent_code"] is None]

    return {
        "source": "data/jerarquia/TLAC_FA_Structure_DB.xlsx",
        "node_levels": NODE_TYPE_BY_LEVEL,
        "staff_levels": sorted(STAFF_LEVELS),
        "roots": roots,
        "positions": rows,
    }


def main():
    tree = build()
    out_path = Path("processed/jerarquia.json")
    out_path.write_text(json.dumps(tree, indent=2, ensure_ascii=False), encoding="utf-8")

    n_nodes = sum(1 for r in tree["positions"] if r["is_org_node"])
    n_staff = len(tree["positions"]) - n_nodes
    print(f"{len(tree['positions'])} posiciones totales -> {n_nodes} nodos de organigrama, {n_staff} staff")
    print(f"Guardado en {out_path}")


if __name__ == "__main__":
    main()
