# Recomendaciones de estandarización — Estructura F&A

Documento vivo con los gaps y puntos pendientes de estandarización detectados
mientras se construía la herramienta (Fases 1 a 4). El objetivo, a pedido de
Gonzalo, es que la información que sostiene la estructura de F&A sea uniforme
no solo en contenido sino también en **formato** — esto queda como propuesta
a revisar, no se modificó ningún archivo fuente original.

Se va a seguir actualizando a medida que avancen las próximas fases.

---

## 1. Descripciones de puesto (`data/posiciones/`)

- **El campo interno "Role / Function" a veces no coincide con el nombre del
  archivo** (ej. "TASA Accounting Stock & Fixed assets analyst (EV)" declara
  internamente "TASA Accounting reporting analyst", copiado de otra
  plantilla). Gonzalo ya confirmó que la próxima tanda de PDFs va a traer el
  nombre interno alineado 1:1 con el nombre del archivo — dejarlo como
  requisito explícito de la plantilla.
- **No hay campo explícito de nómina/headcount.** Hoy se asume 1 PDF = 1
  posición = 1 persona (confirmado por Gonzalo), pero es una convención
  implícita. Recomendación: agregar un campo "Headcount" explícito a la
  plantilla, por si en el futuro un PDF pasa a representar más de una persona
  bajo el mismo puesto.
- **No hay campo de Jefatura/Coordinador.** Los PDFs sólo declaran
  Department/Organization, no a qué Coordinador reporta el puesto. Esto es lo
  que impide desagregar la Fase 4 (procesos/complejidad) por debajo del nivel
  de Gerencia — ver nota `"granularity": "gerencia"` en
  `processed/agregacion-organizacional.json`. Recomendación: agregar un campo
  "Reports to" que use el mismo texto que la columna "Reports To" del Excel
  de jerarquía.
- **Los puestos de AP & AR no distinguen TASA/TDB** en el nombre (a diferencia
  de la familia Accounting/Profit Planning, que sí lo hace). Esto impide
  cruzarlos 1:1 contra las filas del Excel de jerarquía, que sí separan
  TASA/TDB. Recomendación: incluir siempre el sufijo `(TASA)`/`(TDB)`.
- **6 PDFs de la familia "Profit Planning"** (Monthly close analyst x2,
  Profitability controller x2, y posiblemente Profit Planning Analyst x2)
  tienen un defecto de generación: el texto justificado de las tareas perdió
  espacios entre palabras en algunas líneas (ej. `"ofvariousbusinessunits"`).
  Recomendación: revisar el proceso de generación/exportación de esos
  archivos puntuales.

## 2. Documentos de visión de gerentes (`data/vision-gerentes/`)

- **Formato inconsistente entre gerencias.** Accounting y Profit Planning
  usan una tabla "Task / Purpose / Job description / **Importance**"
  (High/Mid); AP & AR usa un formato de organigrama + bullets por seniority,
  sin columna de Importance y sin la estructura Task/Purpose. Esto es lo que
  impidió incorporar el impacto declarado al score de complejidad de forma
  pareja entre las 3 gerencias (quedó como indicador separado en
  `impacto_declarado`, marcado "Sin dato" para AP & AR). **Recomendación
  principal: adoptar la tabla Task/Purpose/Job description/Importance para
  todas las gerencias.**
- **Dos siglas sin aclarar** en el documento de AP & AR (`GTS`, `CUP`) —
  Gonzalo ya marcó que las tiene que validar.
- **El documento de Profit Planning mezcla dos gerencias en un mismo
  archivo** (Profit Planning Manager + Second Wheel Business Manager, que es
  una gerencia distinta sin PDFs de posición propios). Recomendación: un
  archivo por gerencia, igual que la convención de `data/posiciones/`.
- **Sin formato de nómina esperada estandarizado**: los organigramas muestran
  cantidades entre paréntesis de forma inconsistente entre documentos.
  Recomendación: una tabla de headcount esperado por gerencia, con el mismo
  formato en todos los documentos.

## 3. Jerarquía (`data/jerarquia/TLAC_FA_Structure_DB.xlsx`)

- **"Reports To" es texto libre**, a veces truncado (ej. "Regional CFO" en
  vez de "Regional CFO - Finance Director"), lo que obligó a un matching por
  prefijo en vez de una igualdad exacta al construir el árbol. Recomendación:
  usar el "Position Code" (columna ya existente) para "Reports To" en vez del
  nombre.
- **Sin columna de Importance/Impacto.** Si el punto 2 se resuelve
  (Importance uniforme en los 8 documentos de visión), esta columna podría
  volcarse también acá, cerrando el círculo entre el Excel y los PDFs.
- **Sin columna que referencie los procesos canónicos** (de
  `processed/procesos-canonicos.json`). Una vez que la taxonomía esté
  estable y validada en todas las gerencias, convendría sumar una columna
  "Procesos" al Excel para que quede como fuente de verdad conjunta.
- **Etiqueta de Department inconsistente para Kinto/Connected**: el Excel
  los agrupa bajo Department = "AP & AR"; los PDFs de posición usan "Kinto"
  como su propio Department. Recomendación: un único set de etiquetas de
  Department, usado igual en ambas fuentes (hoy se resuelve con un mapeo
  manual en el código — ver `DEPARTMENT_TO_PROCESSED_GERENCIA` en
  `tools/parser/build_aggregation.py`).

## 4. Cobertura de datos (estado actual — referencia para priorizar próximas cargas)

| Gerencia | Puestos parseados / staff real | Cobertura |
|---|---|---|
| Accounting | 19 / 19 | 100% |
| Profit Planning | 6 / 6 | 100% |
| AP & AR (incl. Kinto/Connected) | 13 / 32 | 41% |
| TAX | 0 / 46 | 0% |
| Cost | 0 / 18 | 0% |
| Treasury | 0 / 15 | 0% |
| Budget | 0 / 10 | 0% |
| Value Chain | 0 / 5 | 0% |

**Sugerencia de orden de prioridad** para la próxima tanda de PDFs: TAX
primero (es la gerencia más grande sin ningún dato — 46 personas), después
completar AP & AR (ya al 41%), y por último Cost/Treasury/Budget/Value Chain.

## 5. Misceláneo

- **"Rota 2030" y "Bloco K"** (Accounting, Brasil) son procesos regulatorios
  específicos que hoy quedan mezclados dentro de clusters de Fixed
  Assets/Inventario. Considerar una categoría temática propia
  "Regulatorio/Gobierno" en la taxonomía canónica.
- **Brechas "solo top-down" de AP & AR** (Fase 3): pendiente de validar con
  la gerencia si reflejan procesos huérfanos reales o simplemente posiciones
  sin PDF todavía (dado que el organigrama de esa gerencia tiene más
  headcount que PDFs recolectados).
