"""Parser determinístico de PDFs de descripción de posición (carpeta data/posiciones/).

Plantilla uniforme: extrae POSITION, TASKS AND PROCESSES, las 8 dimensiones de
DIMENSION ASSESSMENT AND PROFILE y el nivel de seniority (columna lateral).
"""
import glob
import json
import re
from pathlib import Path

import pdfplumber

DIM_ORDER = [
    "Operational autonomy",
    "Process complexity",
    "Decision-making",
    "Technical knowledge",
    "Stakeholder management",
    "Reporting level",
    "Error impact",
    "Tools and technology",
]

TITLE_PREFIX_RE = re.compile(r"^(Profile|Profit Planning|Profit planning)\s*—\s*", re.IGNORECASE)


def get_sidebar_box(page):
    """Localiza el recuadro lateral de seniority via la línea vertical divisoria."""
    divs = [r for r in page.rects if (r["x1"] - r["x0"]) < 6 and (r["bottom"] - r["top"]) > 40]
    if not divs:
        return None
    d = divs[0]
    return d["x0"], d["top"], d["bottom"]


def dedup_consecutive_lines(text):
    lines = text.split("\n")
    out = []
    for line in lines:
        if out and out[-1].strip() == line.strip() and line.strip():
            continue
        out.append(line)
    return "\n".join(out)


def extract_body_and_level(page):
    W, H = page.width, page.height
    box = get_sidebar_box(page)
    if box is None:
        return page.extract_text() or "", None
    bx0, btop, bbot = box
    level_top = btop - 22.5
    band_a = page.crop((0, 0, W, max(level_top - 2, 0))).extract_text() or ""
    band_b = page.crop((0, max(level_top - 2, 0), bx0, bbot)).extract_text() or ""
    band_c = page.crop((0, bbot, W, H)).extract_text() or ""
    body = dedup_consecutive_lines("\n".join([band_a, band_b, band_c]))

    words = page.extract_words()
    level = " ".join(
        w["text"] for w in words
        if w["x0"] >= bx0 - 10 and (level_top - 3) <= w["top"] <= (level_top + 3)
    )
    return body, level or None


def parse_position_block(body):
    m = re.search(
        r"Role\s*/\s*Function\s+(.*?)\s+Department\s+(.*?)\n",
        body,
    )
    role_function = m.group(1).strip() if m else None
    department = m.group(2).strip() if m else None

    m2 = re.search(r"Organization\s+(.*?)\n", body)
    organization = m2.group(1).strip() if m2 else None

    return role_function, department, organization


def parse_tasks(body):
    m = re.search(
        r"TASKS AND PROCESSES\s*\n(.*?)\n\s*DIMENSION ASSESSMENT AND PROFILE",
        body,
        re.DOTALL,
    )
    if not m:
        return []
    raw = m.group(1)
    lines = [line.strip() for line in raw.split("\n") if line.strip()]

    # Algunas plantillas envuelven una tarea en varias líneas sin insertar el
    # salto como nueva viñeta; una línea de continuación empieza en minúscula.
    tasks = []
    for line in lines:
        if tasks and line[:1].islower():
            tasks[-1] = f"{tasks[-1]} {line}"
        else:
            tasks.append(line)
    return tasks


def parse_dimensions(body):
    m = re.search(r"DIMENSION ASSESSMENT AND PROFILE\s*\nDimension assessed\s*\n(.*)", body, re.DOTALL)
    if not m:
        return {}
    tail = m.group(1)

    pattern = "(" + "|".join(re.escape(h) for h in DIM_ORDER) + ")\\n"
    parts = re.split(pattern, tail)
    # parts alternates: [pre-text(discard), header, text, header, text, ...]
    result = {}
    it = iter(parts[1:])
    for header in it:
        text = next(it, "")
        clean = " ".join(line.strip() for line in text.split("\n") if line.strip())
        result[header] = clean
    return result


def position_id_from_filename(path):
    stem = Path(path).stem
    stem = TITLE_PREFIX_RE.sub("", stem)
    return stem.strip()


def parse_pdf(path):
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]
        body, level = extract_body_and_level(page)

    role_function, department, organization = parse_position_block(body)
    tasks = parse_tasks(body)
    dimensions = parse_dimensions(body)

    org_company = None
    org_area = None
    if organization:
        om = re.match(r"(TASA|TDB)\s+General Management\s+(.*)", organization)
        if om:
            org_company, org_area = om.group(1), om.group(2).strip()

    return {
        "position_id": position_id_from_filename(path),
        "source_file": Path(path).name,
        "role_function": role_function,
        "department": department,
        "organization": organization,
        "organization_company": org_company,
        "organization_area": org_area,
        "seniority_level": level,
        "tasks_and_processes": tasks,
        "dimensions": dimensions,
    }


def main():
    files = sorted(glob.glob("data/posiciones/*.pdf"))
    positions = [parse_pdf(f) for f in files]

    out_path = Path("processed/posiciones.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"positions": positions}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Parsed {len(positions)} positions -> {out_path}")


if __name__ == "__main__":
    main()
