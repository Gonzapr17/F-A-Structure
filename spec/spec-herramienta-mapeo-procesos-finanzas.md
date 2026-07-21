# Spec funcional: Herramienta de Mapeo y Validación de Procesos — Finanzas

## 1. Objetivo

Construir una herramienta que, a partir de las descripciones de posición ya recolectadas por gerencia, permita:

1. **Inferir y consolidar los procesos** que atraviesan cada gerencia (bottom-up), a partir de lo que cada puesto declara.
2. **Contrastar ese mapa** contra la definición que cada gerente tiene de su propio sector (top-down), identificando coincidencias y brechas, y proponiendo redacciones reconciliadas cuando no coinciden.
3. **Generar un dashboard interactivo** con dos vistas complementarias:
   - Validación bottom-up vs. top-down por gerencia.
   - Reporte/presentación enfocado en un nodo organizacional seleccionable (Jefatura, Gerencia, Gerencia General, Dirección).
4. **Soportar carga incremental**, dado que no todas las descripciones de posición están disponibles todavía.

La estructura jerárquica de Finanzas ya está definida y no es objeto de esta herramienta — se usa como dato de entrada, no como algo a modelar desde cero.

---

## 2. Fuentes de datos (inputs)

| Fuente | Formato | Contenido | Estado |
|---|---|---|---|
| Descripciones de posición | PDF, plantilla 100% uniforme | Objetivo del puesto, procesos declarados, responsabilidades, **seniority** y **nómina** del puesto | Parcialmente disponible — se sigue recibiendo |
| Visión del gerente sobre su sector | Documento separado (formato menos estructurado) | Definición que el gerente hace de su propio sector: procesos, responsabilidades esperadas | Disponible por gerencia |
| Estructura jerárquica (pertenencia a Jefatura y niveles superiores) | Excel + HTML | Relación de dependencia completa: puesto → Jefatura → Gerencia → Gerencia General → Dirección | Disponible |

**Nota de diseño:** la estructura jerárquica derivable directamente de las descripciones de posición (quién reporta a quién dentro del puesto) **no incluye la pertenencia a Jefatura**. Ese dato viene exclusivamente del archivo Excel/HTML separado y debe usarse como fuente de verdad para el armado del organigrama y la agregación por nodo.

---

## 3. Pipeline de procesamiento

### Etapa 1 — Ingesta y parsing
- Parsear los PDF de posiciones (plantilla uniforme → extracción determinística de campos, sin necesidad de IA para la estructura).
- Parsear el Excel/HTML de jerarquía → construir el árbol organizacional completo (Jefatura → Gerencia → Gerencia General → Dirección).
- Parsear los documentos de visión del gerente (menos estructurados → acá sí se apoya en IA para extraer procesos/responsabilidades declaradas).
- Cruzar posiciones con nodos jerárquicos usando el archivo de jerarquía como fuente de verdad.

### Etapa 2 — Inferencia bottom-up de procesos (por gerencia)
- IA agrupa semánticamente las menciones de procesos de todos los puestos de una gerencia en una lista canónica.
- Cada proceso canónico queda trazado a los puestos que lo originan (para trazabilidad y auditoría).
- No existe today un catálogo de procesos predefinido — la taxonomía emerge de este paso y debe quedar persistida (no recalculada desde cero en cada corrida) para mantener consistencia entre actualizaciones incrementales.

### Etapa 3 — Reconciliación bottom-up vs. top-down
- Matching semántico entre la lista canónica bottom-up y la lista extraída del documento del gerente.
- Clasificación de cada proceso en tres estados:
  - **Alineado**: aparece en ambos.
  - **Solo bottom-up**: las posiciones lo ejecutan pero el gerente no lo menciona en su definición del sector.
  - **Solo top-down**: el gerente lo espera pero ninguna posición lo cubre explícitamente.
- Para los casos no alineados, la IA propone una **redacción reconciliada** (texto sugerido que integra ambas perspectivas), sin sobrescribir automáticamente ninguna fuente original.

### Etapa 4 — Agregación organizacional (para la vista de reporte)
Para cada nodo del organigrama (Jefatura, Gerencia, Gerencia General, Dirección), calcular por agregación de sus dependientes:
- Áreas/procesos dependientes (rollup de los procesos canónicos de los nodos hijos).
- Complejidad (a definir un criterio simple, ej. cantidad de procesos distintos + dispersión de seniority).
- Principales responsabilidades (síntesis de las de los nodos hijos).
- Dimensiones que se destacan (ej. concentración de determinado tipo de proceso).
- Nómina dependiente total (suma de personas de todos los puestos bajo ese nodo).
- Distribución de seniority del staff dependiente.
- Estructura del organigrama local (para el gráfico simple).

### Etapa 5 — Manifest de estado (carga incremental)
- Archivo de control que registra, por puesto y por gerencia: recibido / pendiente / procesado / fecha de última actualización.
- Permite correr el pipeline solo sobre lo nuevo o modificado, sin reprocesar todo desde cero, y sin perder la taxonomía de procesos ya consolidada.

---

## 4. Dashboard (salida)

### Vista A — Validación de procesos por gerencia
- Selector de gerencia.
- Estado de completitud de carga (puestos recibidos vs. pendientes).
- Mapa de procesos consolidado con trazabilidad a los puestos de origen.
- Semáforo de alineación (alineado / solo bottom-up / solo top-down) por proceso.
- Redacciones reconciliadas propuestas, editables.

### Vista B — Reporte por nodo organizacional
- Selector de nodo, adaptable según el nivel elegido (Jefatura / Gerencia / Gerencia General / Dirección).
- Contenido del reporte:
  - Áreas / procesos dependientes.
  - Complejidad del nodo.
  - Principales responsabilidades.
  - Dimensiones que se destacan.
  - Nómina dependiente.
  - Seniority del staff.
  - Organigrama simple del nodo y su descendencia.
- Pensada como vista "presentable" (formato apto para mostrar en una reunión, no solo para uso analítico interno).

---

## 5. Consideraciones técnicas sugeridas (para que Claude Code decida el detalle)

- Persistir los resultados intermedios (taxonomía de procesos, árbol jerárquico, resultados de reconciliación) en archivos estructurados (ej. JSON) para que el dashboard no dependa de recalcular todo en cada carga y para sostener las actualizaciones incrementales.
- Separar claramente: (a) capa de parsing/extracción, (b) capa de inferencia con IA, (c) capa de agregación/reconciliación, (d) capa de presentación (dashboard HTML). Esto facilita reprocesar solo la etapa que corresponda cuando lleguen nuevas descripciones.
- El dashboard debe poder regenerarse o actualizarse de forma incremental a medida que se completan más descripciones, sin perder el trabajo de reconciliación ya validado manualmente por Gonzalo.

---

## 6. Fuera de alcance (explícito)

- Modificar o cuestionar la estructura jerárquica existente.
- Generar automáticamente las visiones de sector de los gerentes (ya existen como input).
- Sobrescribir automáticamente las descripciones originales con las redacciones reconciliadas (quedan como propuesta a revisión).
