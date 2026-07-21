"""Etapa 2 — Inferencia bottom-up de procesos canónicos por gerencia.

Agrupa semánticamente las tareas declaradas en processed/posiciones.json en una
lista canónica de procesos por gerencia. No existe un catálogo previo: la
taxonomía de abajo fue construida leyendo las tareas de los 38 puestos
disponibles y agrupando las que describen el mismo proceso de negocio (aunque
estén redactadas distinto entre puestos gemelos TASA/TDB, o entre niveles de
seniority). La trazabilidad se arma haciendo *matching* de cada tarea cruda
contra palabras clave asociadas a cada proceso canónico, así el resultado es
auditable y reproducible en vez de una asignación manual opaca.
"""
import json
import re
from pathlib import Path

# Un puesto pertenece a una gerencia según el Department declarado en el PDF,
# salvo Kinto/Connected que en la jerarquía oficial (data/jerarquia) cuelgan
# del mismo Manager que AP & AR, no de una gerencia propia.
DEPARTMENT_TO_GERENCIA = {
    "Accounting": "Accounting",
    "AP & AR": "AP & AR",
    "Kinto": "AP & AR",
    "Profit Planning": "Profit Planning",
}

# Cada entrada: (nombre canónico, [keywords que identifican la tarea cruda])
# El matching es por substring case-insensitive sobre el texto de la tarea.
CANONICAL_DEFINITIONS = {
    "Accounting": [
        ("SOX Control Matrix & Internal Procedures", ["sox control matrix"]),
        ("Monthly Balance Sheet Account Reconciliations", ["account reconliations", "account reconciliations"]),
        ("Accounting Information for External Surveys & Reports (INDEC/Sustainability/Press)", ["for surveys"]),
        ("Bank Reconciliation & Loans Follow-up", ["bank account reconlic", "loans valuation"]),
        ("Annual Legal Financial Statements Preparation", ["annual legal financial statements"]),
        ("Monthly Closing Reporting via Conets", ["report by conets"]),
        ("Monthly Accounting Package to TMC", ["accounting package to tmc"]),
        ("Fixed Assets / Vehicles Impairment Testing", ["impairment test"]),
        ("Fixed Assets Inventory Taking & Disposal Management", ["fixed assets inventory taking"]),
        ("Inflation Adjustment of Non-Monetary Assets", ["adjust by inflation"]),
        ("Finished Goods Inventory Taking & Booking", ["finished good"]),
        ("Non-Operating Results Determination & Budget Follow-up", ["non operating results"]),
        ("USD Position Forecast & Follow-up", ["usd position forecast"]),
        ("TPA Units Accounting & Intercompany Control", ["tpa operation accounting booking"]),
        ("Dividend / IOE Payment Calculation", ["calculate dividend"]),
        ("Invoicing Dashboard Control & Credit Notes", ["invoicing dashboard"]),
        ("Inventory in Transit / Importation Tracking", ["inventories importation"]),
        ("Monthly Tax Credit Reversal", ["reversal of the tax credit"]),
        ("Government Bloco K Inventory Reporting (Brazil)", ["bloco k"]),
    ],
    "AP & AR": [
        ("AP Invoice/Document Analysis & Posting (Dealers, Suppliers, Auto Parts, Foreign)", [
            "analysis and accounting of dealer documents",
            "analysis and posting of service documents",
            "analysis and posting of auto parts suppliers",
            "analysis and posting of non-po invoices",
            "analysis and accounting of auto parts suppliers",
            "analysis and accounting of foreign suppliers",
        ]),
        ("Payment Proposal Preparation & Review", ["payment proposal"]),
        ("Supplier & Internal User Support (AP queries)", ["support for suppliers and internal users"]),
        ("Internal / External Audit Support", ["support for internal and external audits"]),
        ("TPA / Lexus / Insurance Collections Follow-up", ["tpa / lexus / insurance"]),
        ("Receipts & Tax Certificate Upload", ["upload of receipts and tax certificate"]),
        ("Aging Report Preparation & Collections Forecast", ["aging report"]),
        ("Customer/Dealer Portfolio Management & Due-Date Follow-up", [
            "customer portfolio management",
            "dealer portfolio management",
            "monitoring and management of due dates",
            "due date monitoring and management",
            "debt recovery follow-up",
        ]),
        ("Receipt/Invoice & Collections Reconciliation", [
            "receipt and invoice reconciliation",
            "invoice and credit card collection reconciliation",
        ]),
        ("Accounting/Account Integrity Assurance", [
            "responsible for ensuring account integrity",
            "responsible for the integrity of accounting information",
        ]),
        ("Credit & Business Risk Assessment", ["credit risk analysis", "business risk assessment"]),
        ("Kinto Dealer Invoice Approval & Share Operations Management", [
            "dealer invoice approval", "kinto share operations management",
        ]),
        ("Additional Services Control & Billing", ["additional services control", "control and billing of additional services"]),
        ("Kinto Fine Management & Commission Settlement", ["kinto fine management", "commission settlement"]),
        ("Overdue Kinto Share Accounts Monitoring", ["overdue kinto share accounts"]),
        ("Kinto One Billing, Control & Revenue/Expense Analysis", [
            "kinto one billing and control", "revenue and expense account analysis",
        ]),
        ("Kinto One Customer Support", ["kinto one customer support"]),
        ("Kinto Investment, Pricing & Residual Value Management", [
            "preparation and monitoring of investments",
            "pricing control and analysis",
            "residual value control and monitoring",
        ]),
        ("Kinto Business Performance Analysis", ["business performance analysis"]),
        ("Connected Services Billing (Local & Regional)", ["billing for connected services"]),
        ("Connected Systems Development & Testing", ["development and testing of management systems"]),
        ("Connected Controller", ["connected controller"]),
    ],
    "Profit Planning": [
        ("Monthly Financial Closing Process Oversight", ["closing process oversight"]),
        ("Financial Statement Preparation & P&L Analysis by Business Unit", ["financial statement preparation"]),
        ("Budget vs. Actual / Profitability Variance Analysis", [
            "variance analysis: monitor and analyze budget versus actual",
            "variance analysis: analyze and interpret variances in profitability",
        ]),
        ("Continuous Process Improvement", ["process improvement:", "continuous improvement:"]),
        ("Cross-functional Collaboration for Monthly Close", ["cross-functional collaboration"]),
        ("Financial Analysis of Profit Margins", ["financial analysis: deeply analysis"]),
        ("Financial Forecasting", ["forecasting:"]),
        ("Budgeting & Alignment with Profit Goals", ["budgeting:"]),
        ("Scenario Planning", ["scenario planning:"]),
        ("Financial Risk Management (Profit Planning)", ["risk management:"]),
        ("Management Reporting & Dashboards", ["reporting: generate regular reports"]),
        ("Profitability Analysis (Revenue/Cost/Margin)", ["profitability analysis: conduct detailed analyses"]),
        ("KPI Development & Monitoring (Profitability)", ["key performance indicators (kpis)"]),
        ("Product/Service Profitability Assessment", ["product/service profitability"]),
    ],
}


def load_positions():
    data = json.loads(Path("processed/posiciones.json").read_text(encoding="utf-8"))
    return data["positions"]


def build_canonical_processes(positions):
    by_gerencia = {}
    for p in positions:
        gerencia = DEPARTMENT_TO_GERENCIA.get(p["department"], p["department"])
        by_gerencia.setdefault(gerencia, []).append(p)

    result = {}
    for gerencia, defs in CANONICAL_DEFINITIONS.items():
        positions_in_gerencia = by_gerencia.get(gerencia, [])
        processes = []
        matched_tasks = set()  # (position_id, task) ya asignados a algún proceso
        for name, keywords in defs:
            sources = []
            for p in positions_in_gerencia:
                for task in p["tasks_and_processes"]:
                    task_l = task.lower()
                    if any(kw in task_l for kw in keywords):
                        sources.append({"position_id": p["position_id"], "task": task})
                        matched_tasks.add((p["position_id"], task))
            if sources:
                processes.append({
                    "process": name,
                    "source_positions": sorted({s["position_id"] for s in sources}),
                    "traced_tasks": sources,
                })

        # Tareas que no matchearon ningún proceso canónico (control de cobertura)
        unmatched = []
        for p in positions_in_gerencia:
            for task in p["tasks_and_processes"]:
                if (p["position_id"], task) not in matched_tasks:
                    unmatched.append({"position_id": p["position_id"], "task": task})

        result[gerencia] = {
            "position_count": len(positions_in_gerencia),
            "positions": sorted(p["position_id"] for p in positions_in_gerencia),
            "canonical_processes": processes,
            "unmatched_tasks": unmatched,
        }
    return result


def main():
    positions = load_positions()
    result = build_canonical_processes(positions)

    out_path = Path("processed/procesos-canonicos.json")
    out_path.write_text(json.dumps({"by_gerencia": result}, indent=2, ensure_ascii=False), encoding="utf-8")

    for gerencia, data in result.items():
        print(f"\n=== {gerencia} ({data['position_count']} puestos) ===")
        for proc in data["canonical_processes"]:
            print(f"  - {proc['process']}  [{len(proc['source_positions'])} puestos]")
        if data["unmatched_tasks"]:
            print(f"  !! {len(data['unmatched_tasks'])} tareas sin matchear")
            for u in data["unmatched_tasks"]:
                print(f"     - ({u['position_id']}) {u['task']}")

    print(f"\nGuardado en {out_path}")


if __name__ == "__main__":
    main()
