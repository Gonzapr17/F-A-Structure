"""Etapa 3 — Reconciliación bottom-up vs. top-down (spec sección "Etapa 3").

Cruza la taxonomía canónica bottom-up (processed/procesos-canonicos.json,
salida de Fase 2) contra lo que cada gerente declara en su propio documento de
visión de sector (data/vision-gerentes/), que tiene un formato mucho menos
estructurado (organigramas, matrices RACI-like Main/Supporter, bullets por
seniority). Por eso la extracción del lado top-down y el matching semántico
fueron hechos por lectura/interpretación directa de cada PDF (no hay texto
homogéneo para keyword-matching automático como en Fase 2); lo que se
automatiza acá es el cruce, el cálculo de estados y el armado del JSON.

Cada proceso queda clasificado en uno de tres estados:
  - aligned: aparece en ambas fuentes.
  - solo_bottom_up: las posiciones lo declaran, el gerente no lo menciona.
  - solo_top_down: el gerente lo espera, ninguna posición relevada lo cubre.
Para los no alineados se agrega una redacción reconciliada propuesta (no
sobrescribe ninguna fuente original, es sólo una propuesta a revisar).
"""
import json
from pathlib import Path


def load_canonical():
    return json.loads(Path("processed/procesos-canonicos.json").read_text(encoding="utf-8"))["by_gerencia"]


def positions_for(canonical_gerencia, process_name):
    for proc in canonical_gerencia["canonical_processes"]:
        if proc["process"] == process_name:
            return proc["source_positions"]
    raise KeyError(process_name)


# ---------------------------------------------------------------------------
# Lado top-down: extraído a mano de data/vision-gerentes/{Accounting,
# "AP, AR & Kinto", "Profit planning"}.pdf. `evidence` son citas (resumidas)
# del documento original, para poder auditar de dónde salió cada lectura.
# ---------------------------------------------------------------------------

RECONCILIATION = {
    "Accounting": {
        "source_doc": "data/vision-gerentes/Accounting.pdf",
        # bottom_up canonical process -> evidencia top-down que lo confirma
        "aligned": {
            "SOX Control Matrix & Internal Procedures": "\"To perform/update SOX control matrix - To perfomr/update interal procedures\" (JOB DESCRIPTION DETAIL, SOX controls)",
            "Monthly Balance Sheet Account Reconciliations": "\"To make monthly account reconliations (AP,AR, Other credits, liabilities, Stock, FA)\" (Accounts valuation)",
            "Accounting Information for External Surveys & Reports (INDEC/Sustainability/Press)": "\"To prepare accounting information w/interal & external requeriment (INDEC), for Company reports (Sustaintability), for press media\"",
            "Bank Reconciliation & Loans Follow-up": "\"To perform monthly bank account reconliciation, reporting and follow up of pending points / Loans valuation\"",
            "Annual Legal Financial Statements Preparation": "\"Prepare full package of annual legal Financial Statements\" (Annual Financial Statements)",
            "Monthly Closing Reporting via Conets": "\"To report by Conets each accounting closing figures\" (TMC reports figures)",
            "Monthly Accounting Package to TMC": "\"To prepare monthly accounting package to TMC\" (TMC reports figures)",
            "Fixed Assets / Vehicles Impairment Testing": "\"To perform Fixed asset impairment test - To perform Vehicles impairment test\" (Impairment valuation test)",
            "Fixed Assets Inventory Taking & Disposal Management": "\"To coordinate Fixed assets inventory taking - To analyse inventory diferencies - To approve fixed assets disposals... transference\" (Fixed assets inventory management)",
            "Inflation Adjustment of Non-Monetary Assets": "\"To adjust by inflation non monetary assets in AR$\" (Inflation accouting in AR$, excl. TASA)",
            "Finished Goods Inventory Taking & Booking": "\"To perfom Finished good (vehicules, spare parts, materials) inventory taking - To analyse inventory diferencies and book them if necessary\"",
            "Non-Operating Results Determination & Budget Follow-up": "\"To determine Non Operating results (actual & budget/fcst/MTBP planning) - To control Actual Non Operating results\"",
            "USD Position Forecast & Follow-up": "\"To determine USD position forecast - To control Actual Balance sheet USD position\"",
            "TPA Units Accounting & Intercompany Control": "\"Units, valuation and expousure of Units Liabilities - Penalties and contingencies control - Intercompany control\" (TPA consortium, excl. TASA)",
            "Dividend / IOE Payment Calculation": "\"To calculate dividend and IOE (excl.TDB) payment\"",
            "Invoicing Dashboard Control & Credit Notes": "\"Follow up and controlling of Invoicing Dashboard - Invoice Monthly Closing and Reporting - Analysis, control and making of Credit Notes\" (Invoicing, excl. TASA)",
            "Inventory in Transit / Importation Tracking": "\"Importation in progress (TDB)\" (Finished good inventories, TDB)",
            "Monthly Tax Credit Reversal": "\"Reversal of the Tax credit of the month\" (Finished good inventories, TDB)",
            "Government Bloco K Inventory Reporting (Brazil)": "\"Information for the inventory moviment to Goverment Bloco K (TDB)\"",
        },
        "solo_bottom_up": {},  # ningún proceso bottom-up quedó sin mención del gerente
        "solo_top_down": {
            "Rota 2030 Government Benefit Approval Reporting (Brazil)": {
                "evidence": "\"Information to goverment related to benefit approval - Rota 2030 (TDB)\" (Finished good inventories, TDB)",
                "reconciled_wording": (
                    "Preparar y presentar la información requerida por el gobierno brasileño para la "
                    "aprobación de beneficios del programa Rota 2030 (TDB). El gerente lo espera dentro del "
                    "alcance de Accounting/Stock TDB, pero ninguna descripción de puesto relevada lo declara "
                    "explícitamente hoy — a validar si ya lo cubre alguno de los analistas de Stock TDB (PFZ/SOR "
                    "I/SOR II/reporting) o si falta asignarlo formalmente."
                ),
            },
        },
    },
    "AP & AR": {
        "source_doc": "data/vision-gerentes/AP, AR & Kinto.pdf",
        "note": (
            "El organigrama de este documento muestra headcount (AP TDB(4), AR TDB(5), Kinto Adm TASA(6), "
            "Con TDB(2), etc.) mayor al de los 13 PDFs de posición disponibles. Varias brechas 'solo top-down' "
            "reflejan probablemente posiciones aún no recolectadas (ej. Coordinadores de AP/AR, roles adicionales "
            "de Kinto/Connected) y no necesariamente procesos huérfanos."
        ),
        "aligned": {
            "AP Invoice/Document Analysis & Posting (Dealers, Suppliers, Auto Parts, Foreign)": "\"Local supplier's invoice processing\", \"Dealers invoice process\", \"Foreign payments\", \"Main suppliers local payments\", \"Non-regular supplier's invoices control\" (AP org chart / JOB DESCRIPTION DETAIL)",
            "Payment Proposal Preparation & Review": "\"Outsystem payment approval follow up\" (AP org chart)",
            "TPA / Lexus / Insurance Collections Follow-up": "\"Others sales: scrap / consortium / insurance\", \"TCFA receips\" (AR org chart) — cobertura parcial/aproximada",
            "Aging Report Preparation & Collections Forecast": "\"Monthly closing process / Aging report\" (AP y AR), \"Overdue report / Aging report\" (Senior AP, JOB DESCRIPTION DETAIL)",
            "Customer/Dealer Portfolio Management & Due-Date Follow-up": "\"Collection management & control: Dealers\", \"Overdue follow up\", \"Dealers accounts\" (AR org chart / JOB DESCRIPTION DETAIL)",
            "Receipt/Invoice & Collections Reconciliation": "\"Accounts reconciliation\" (Plain, JOB DESCRIPTION DETAIL - Account Receivables)",
            "Credit & Business Risk Assessment": "\"Nosis análisis – credit approval\", \"Spare parts credit analysis & approval\", \"Verification SERASA/AFIP\" (AR/AP org chart)",
            "Additional Services Control & Billing": "\"Additional services invoicing\" (Kinto, JOB DESCRIPTION DETAIL)",
            "Kinto Fine Management & Commission Settlement": "\"Traffic tickets controls, payment and collection\", \"Dealers commissions\" (Kinto, JOB DESCRIPTION DETAIL)",
            "Overdue Kinto Share Accounts Monitoring": "\"Kinto collection management\" (AR org chart) — cobertura aproximada",
            "Kinto One Billing, Control & Revenue/Expense Analysis": "\"Invoicing process\", \"Prebilling revision\" (Kinto org chart)",
            "Kinto One Customer Support": "\"Call center claims revision\" (Kinto, JOB DESCRIPTION DETAIL)",
            "Kinto Investment, Pricing & Residual Value Management": "\"Sales price controller\", \"Investment controller\" (Kinto org chart)",
            "Kinto Business Performance Analysis": "\"P&L analysis & reporting\", \"Business KPI\" (Kinto org chart)",
            "Connected Services Billing (Local & Regional)": "\"Invoicing process\", \"Prebilling revision\" (Connected org chart)",
            "Connected Controller": "\"Controller: Connected Kinto op. / Banco Toyota / TFCA / Insurance (Mitsui/La Caja)\" (Connected org chart)",
        },
        "solo_bottom_up": {
            "Supplier & Internal User Support (AP queries)": (
                "El gerente no nombra soporte a proveedores/usuarios internos como proceso propio del área AP; "
                "aparece únicamente en el puesto Jr Analyst Accounts Payable. Redacción propuesta para incorporar "
                "en la visión de sector: 'Atención y soporte de consultas a proveedores y usuarios internos sobre "
                "el estado de sus documentos/pagos, como parte del flujo operativo de AP Junior.'"
            ),
            "Internal / External Audit Support": (
                "Ningún bullet del documento del gerente menciona soporte a auditorías; sólo lo declara Sr Analyst "
                "Accounts Payable. Redacción propuesta: 'Dar soporte a auditorías internas y externas sobre el "
                "proceso de Cuentas a Pagar (documentación, conciliaciones y propuestas de pago), a cargo del "
                "Senior Analyst de AP.'"
            ),
            "Receipts & Tax Certificate Upload": (
                "No está en la visión de sector; sólo lo declara Jr Analyst Accounts Receivable. Redacción "
                "propuesta: 'Carga de comprobantes de cobro y certificados de retención impositiva en el sistema, "
                "como tarea de base del analista Junior de AR.'"
            ),
            "Accounting/Account Integrity Assurance": (
                "No aparece como proceso nombrado por el gerente (aunque puede estar implícito en el control "
                "general de cobranzas). Redacción propuesta: 'Asegurar la integridad de la información contable "
                "de cobranzas y de Connected, formalizando esta responsabilidad en la definición de sector de "
                "AR Web Business y Connected.'"
            ),
            "Kinto Dealer Invoice Approval & Share Operations Management": (
                "El área de Kinto en la visión del gerente se describe en términos de pricing/inversión/facturación, "
                "sin mencionar aprobación de facturas de concesionarios ni gestión de operaciones de Kinto Share. "
                "Redacción propuesta: 'Aprobación de facturas de concesionarios y gestión operativa de Kinto Share, "
                "a cargo del analista Junior de Kinto Administration 1 — a confirmar con el gerente si debe "
                "explicitarse en la visión de sector.'"
            ),
            "Connected Systems Development & Testing": (
                "La visión de sector de Connected está enfocada en la introducción comercial del área nueva, sin "
                "mencionar desarrollo/testing de sistemas de gestión. Redacción propuesta: 'Desarrollo y testing de "
                "sistemas de gestión para Connected, en soporte a la implementación de la nueva área descripta por "
                "el gerente.'"
            ),
        },
        "solo_top_down": {
            "AP/AR Contract Revision & New Project Implementation": {
                "evidence": "\"Contract conditions revision\", \"New project implementations\" (AP y AR org chart)",
                "reconciled_wording": (
                    "Revisión de condiciones contractuales con proveedores/clientes y participación en la "
                    "implementación de nuevos proyectos del área de AP/AR. El gerente lo espera a nivel Senior en "
                    "ambos sectores, pero ninguna de las 13 posiciones relevadas lo declara — podría corresponder "
                    "a un Coordinador de AP/AR aún sin PDF."
                ),
            },
            "SVD/ARIBA Supplier System Management": {
                "evidence": "\"SVD/ARIBA management\" (AP org chart, Plain)",
                "reconciled_wording": (
                    "Administración de las plataformas SVD/ARIBA para gestión de proveedores. No está en ninguna "
                    "descripción de puesto disponible; a validar si corresponde al Pl Analyst Account Payable."
                ),
            },
            "Price Difference Control (TDB Imports)": {
                "evidence": "\"Price difference (TDB)\" (AP org chart, Plain)",
                "reconciled_wording": (
                    "Control de diferencias de precio en importaciones de TDB. No declarado en las posiciones "
                    "disponibles; podría corresponder al Pl Analyst Account Payable de TDB (sin PDF propio "
                    "todavía, ya que el actual es genérico TASA/TDB combinado)."
                ),
            },
            "Concur Expense Management (Employee Advances)": {
                "evidence": "\"Concur mgt\", \"Employees advance payments\" (AP org chart)",
                "reconciled_wording": (
                    "Gestión de adelantos y rendiciones de gastos de empleados vía Concur. Esperado por el "
                    "gerente a nivel Senior de AP, sin cobertura en las posiciones relevadas."
                ),
            },
            "AR Cash Flow Reporting": {
                "evidence": "\"Cash Flow report\" (AR org chart, Plain)",
                "reconciled_wording": (
                    "Elaboración de reportes de flujo de caja de cobranzas. No aparece en ninguna posición de AR "
                    "relevada; a confirmar si lo cubre el Pl Analyst Account Receivable - Web business o falta "
                    "asignarlo."
                ),
            },
            "Vehicles Certificates Management (AR)": {
                "evidence": "\"Vehicles certificates\" (AR org chart, Plain)",
                "reconciled_wording": (
                    "Gestión de certificados de vehículos vinculados a la cobranza. No declarado por ninguna "
                    "posición relevada de AR."
                ),
            },
            "Kinto GTS Management": {
                "evidence": "\"GTS management\" (Kinto org chart, Senior)",
                "reconciled_wording": (
                    "Gestión del sistema/proceso GTS de Kinto (sigla sin aclarar en el documento). No cubierto por "
                    "ninguna posición de Kinto relevada — a validar alcance con el gerente antes de redactar "
                    "definitivamente."
                ),
            },
            "Kinto Systems & New Project Implementation": {
                "evidence": "\"System implementations\", \"New projects implementation\" (Kinto org chart, Senior)",
                "reconciled_wording": (
                    "Participación en implementaciones de sistemas y nuevos proyectos de Kinto Administration. "
                    "Esperado a nivel Senior por el gerente; no declarado en el Sr Analyst Kinto Administration "
                    "actual — posible brecha real o falta de detalle en su PDF."
                ),
            },
            "Kinto Maintenance & Spare Parts Control": {
                "evidence": "\"Maintenance & spare parts controller\" (Kinto org chart, Plain)",
                "reconciled_wording": (
                    "Control de mantenimiento y repuestos de la flota Kinto. No aparece en el Pl Analyst Kinto "
                    "Administration relevado."
                ),
            },
            "Kinto CUP Follow-up": {
                "evidence": "\"CUP follow up\" (Kinto org chart, Plain)",
                "reconciled_wording": (
                    "Seguimiento del proceso CUP de Kinto (sigla sin aclarar en el documento). No declarado por "
                    "ninguna posición relevada."
                ),
            },
            "Kinto New Client Registration": {
                "evidence": "\"Input new clients\", \"Clients registration\" (Kinto org chart)",
                "reconciled_wording": (
                    "Alta y registro de nuevos clientes de Kinto. No aparece en las posiciones de Kinto "
                    "relevadas."
                ),
            },
        },
    },
    "Profit Planning": {
        "source_doc": "data/vision-gerentes/Profit planning.pdf",
        "note": (
            "Este documento incluye una sección 'Second Wheel Business Manager' que es una gerencia distinta "
            "dentro de Finance Planning (sin PDFs de posición propios todavía) — se excluyó de este cruce, que se "
            "limita a la visión del Profit Planning Manager."
        ),
        "aligned": {
            "Financial Analysis of Profit Margins": "\"Financial analysis: Deeply analysis of financial statements to identify key factors that affect profit margins\" (JOB DESCRIPTION DETAIL, Company Profit planning consolidation)",
            "Financial Forecasting": "\"Forecasting: ...accurate financial forecasts, considering market trends, economic indicators...\" + Manager main activity #3 'Forecasting and Financial Modeling'",
            "Scenario Planning": "\"Scenario Planning: Evaluate potential scenarios and their impact on profitability...\" + Manager main activity #5 'Scenario and Sensitivity Analysis'",
            "Management Reporting & Dashboards": "\"Reporting: Generate regular reports and dashboards...\" + Manager main activity #6 'Performance Monitoring and Reporting'",
            "Monthly Financial Closing Process Oversight": "\"Closing Process Oversight: Monthly financial closing process, ensuring met deadlines with high report accuracy\"",
            "Financial Statement Preparation & P&L Analysis by Business Unit": "\"Financial Statement Preparation: Income statement and profit and lost by business unit analysis\"",
            "Budget vs. Actual / Profitability Variance Analysis": "\"Variance Analysis: Budget versus actual & actual vs actual performance analysis...\"",
            "Continuous Process Improvement": "Manager main activity #7 'Process Improvement and Systems Development: Continuously improve planning tools, processes, and systems...'",
            "Cross-functional Collaboration for Monthly Close": "Implícito en Manager main activity #7 (\"reinforcing...cross-functional collaboration\") y en el propósito general del rol",
            "Budgeting & Alignment with Profit Goals": "Manager main activity #4 'Budget Oversight and Alignment: Coordinate the budgeting process across departments...'",
            "Financial Risk Management (Profit Planning)": "\"Risk Management: Evaluate financial risks associated with profit planning activities...\"",
            "Profitability Analysis (Revenue/Cost/Margin)": "\"Profitability Analysis: Detailed analyses of revenue streams, cost structures, and profit margins...\" (OEM/Distrib. Profitability control)",
            "KPI Development & Monitoring (Profitability)": "\"Key Performance Indicators (KPIs): Develop, monitor, and report on key profitability indicators...\"",
            "Product/Service Profitability Assessment": "\"Product/Service Profitability: Assess and compare the profitability of different products or services...\"",
        },
        "solo_bottom_up": {},  # los 14 procesos bottom-up están cubiertos por la visión del gerente
        "solo_top_down": {
            "Team Management & Coordination of Profit Planning Analysts": {
                "evidence": "Manager main activity #2: \"Team Management and Coordination: Manage a team of analysts responsible for profit modeling, financial projections, and variance analysis...\"",
                "reconciled_wording": (
                    "Gestión y coordinación del equipo de analistas de Profit Planning. Es una responsabilidad "
                    "propia del rol de Manager (no se espera que aparezca en las descripciones de puesto de "
                    "analistas) — se deja registrada como 'solo top-down' por completitud, no como brecha a "
                    "cerrar en el staff."
                ),
            },
            "Overall Company Profit Plan Cycle (STPP/MTPP, Consolidation, Variance Segregation, Report Construction)": {
                "evidence": "Task distribution map: \"MID & SHORT TERM: GPM/TOSHO/SHUSEI/QUARTERLY\", \"Consolidation: Profit planning P&L construction\", \"Comparative variance analyisis: Segregate impacts\", \"Conclusion: Remarks main variations\", \"Report construction: F&A/RBOD\"",
                "reconciled_wording": (
                    "Ciclo completo de plan de utilidades de la compañía (corto y mediano plazo: TOSHO/SHUSEI/"
                    "trimestral y MTPP a 5 años), con consolidación, segregación de variaciones y armado de "
                    "reporte F&A/RBOD. No está en el nivel de detalle de ninguna descripción de puesto relevada "
                    "(los 6 puestos disponibles describen el rol en términos generales, no este ciclo operativo "
                    "específico) — candidato a incorporarse en el próximo relevamiento de Profit Planning Analyst/"
                    "Monthly close analyst."
                ),
            },
            "Monthly Process Deep-Dive (SAP Control, Volume, Revenue, Variable Cost, Trade Balance, Value Chain, IFEM, Main KPI ROS/BEP, FAFM)": {
                "evidence": "Task distribution map, sección 'MONTHLY PROCESS': \"MONTHLY CLOSE: SAP Control...\", \"Volume: Production and sales...\", \"Revenue: Invoicing/Freight/Commision/CCL/Fleet support/Export price\", \"Variable cost: Impot CBU/Parts/Labor/Taxes\", \"Trade balance...\", \"IFEM SUBMISSION: TMC Accounting screen\", \"MAIN KPI: ROS/BEP\", \"FAFM: Variation detailed explanation/Non OP result\"",
                "reconciled_wording": (
                    "Detalle operativo del cierre mensual: control en SAP, análisis de volumen, revenue, costo "
                    "variable, balanza comercial, submission a IFEM y KPIs ROS/BEP/FAFM. Es una desagregación "
                    "mucho más granular de lo que hoy cubren 'Monthly Financial Closing Process Oversight' y "
                    "'Budget vs. Actual Variance Analysis' bottom-up — se sugiere, en la próxima ronda de "
                    "descripciones de puesto, detallar estos sub-procesos explícitamente."
                ),
            },
            "Regional Profit Consolidation & TMC Reporting (CCPV, TOM, Matsushita Report, Marginal Profit)": {
                "evidence": "Task distribution map, sección 'RECONCILIATION': \"REGIONAL PROFIT CONSOLIDATION: CCPV\", \"TOM: Top management meeting (Ar)\", \"TMC REPORT (Matsushita): Profit consolidation\", \"MARGINAL PROFIT: Actual vs actual/Actual vs theorical\"",
                "reconciled_wording": (
                    "Consolidación regional de resultados (CCPV), reporte a TMC (Matsushita) y análisis de "
                    "utilidad marginal, con reuniones de Top Management (TOM). Marcado únicamente en la columna "
                    "de mayor seniority del task map — no aparece en ninguna descripción de puesto relevada; "
                    "podría ser una responsabilidad concentrada en un Senior Analyst específico (TASA) a "
                    "confirmar."
                ),
            },
            "Value Chain & TLAC Business Profitability / Pricing Analysis (incl. FOB Intercompany, Price List, Kinto Ar Performance)": {
                "evidence": "Task distribution map, sección 'Profitability for control': \"VALUE CHAIN: Detailed analysis by business\", \"TLAC Business: SP/Acc/PPO/Conv./UC\", \"Kinto Ar: Performance analysis\", \"PRICE (Dom. MKT.): Discussion with commercial (Veh/SP/Kinto)\", \"FOB Intercompany revision\", \"Price list: Overall control of F&A input in SAP\"",
                "reconciled_wording": (
                    "Análisis detallado de rentabilidad por línea de negocio de TLAC (Spare Parts, Accesorios, "
                    "PPO, Conversión, Usados) y de Kinto Argentina, más discusión de precios con el área "
                    "comercial, revisión de FOB intercompañía y control de lista de precios en SAP. No está "
                    "cubierto por 'Profitability Analysis' ni 'Product/Service Profitability Assessment' "
                    "bottom-up en este nivel de detalle — se sugiere evaluar si corresponde a una posición "
                    "separada (Value Chain, que ya tiene su propia gerencia en la jerarquía) antes de asignarlo "
                    "a Profit Planning."
                ),
            },
            "Intercompany FOB Setting & GI Follow-up (Vehicles/Spare Parts/Accessories)": {
                "evidence": "Org chart: \"Intercompany FOB Setting (Vehicles)\", \"GI Follow up (Veh / SP / Accessories)\"",
                "reconciled_wording": (
                    "Definición del FOB intercompañía y seguimiento de GI (Gross Income) para vehículos, "
                    "repuestos y accesorios. No aparece en ninguna descripción de puesto relevada de Profit "
                    "Planning."
                ),
            },
        },
    },
}


def build():
    canonical = load_canonical()
    out = {}
    for gerencia, spec in RECONCILIATION.items():
        g_canonical = canonical[gerencia]

        aligned = []
        for process, evidence in spec["aligned"].items():
            aligned.append({
                "process": process,
                "bottom_up_positions": positions_for(g_canonical, process),
                "top_down_evidence": evidence,
            })

        solo_bottom_up = []
        for process, wording in spec["solo_bottom_up"].items():
            solo_bottom_up.append({
                "process": process,
                "bottom_up_positions": positions_for(g_canonical, process),
                "reconciled_wording": wording.strip(),
            })

        solo_top_down = []
        for process, info in spec["solo_top_down"].items():
            solo_top_down.append({
                "process": process,
                "top_down_evidence": info["evidence"],
                "reconciled_wording": info["reconciled_wording"].strip(),
            })

        out[gerencia] = {
            "source_doc": spec["source_doc"],
            "note": spec.get("note"),
            "summary": {
                "aligned": len(aligned),
                "solo_bottom_up": len(solo_bottom_up),
                "solo_top_down": len(solo_top_down),
            },
            "aligned": aligned,
            "solo_bottom_up": solo_bottom_up,
            "solo_top_down": solo_top_down,
        }
    return out


def main():
    result = build()
    out_path = Path("processed/reconciliacion.json")
    out_path.write_text(json.dumps({"by_gerencia": result}, indent=2, ensure_ascii=False), encoding="utf-8")

    for gerencia, data in result.items():
        s = data["summary"]
        print(f"\n=== {gerencia} — alineados: {s['aligned']} | solo bottom-up: {s['solo_bottom_up']} | solo top-down: {s['solo_top_down']} ===")

    print(f"\nGuardado en {out_path}")


if __name__ == "__main__":
    main()
