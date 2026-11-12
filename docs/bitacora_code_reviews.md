# Bitácora de Code Reviews

**Proyecto Integrador · Procesamiento de Grandes Bases de Datos · Maestría en Ciencia de Datos, CUCEA**

| Campo | Valor |
|---|---|
| **Proyecto** | ETL de la ENOE con PySpark y cruces con IGAE, INPC y SHCP |
| **Repositorio** | [RaulGitrdero/mexico-economic-pipeline](https://github.com/RaulGitrdero/mexico-economic-pipeline) |
| **Rama principal** | `main` |
| **Rama de desarrollo** | `dev` |
| **Integrante 1** | Raúl Cordero Villalobos |
| **Integrante 2** | Sergio Delgadillo Domínguez |
| **Integrante 3** | Juan Manuel Seimandi Gollaz |
| **Periodo** | Noviembre 2026 |

---

## Convenciones

### Severidad de la observación

| Nivel | Significado |
|---|---|
| 🔴 **Crítica** | Rompe el ETL, corrompe datos o da resultados incorrectos. |
| 🟠 **Mayor** | Error de lógica, rendimiento o mantenibilidad relevante. |
| 🟡 **Menor** | Estilo, nombres, comentarios o documentación. |
| 🟢 **Sugerencia** | Mejora opcional; no bloquea la aprobación. |

### Estado de la observación

| Estado | Significado |
|---|---|
| ⏳ **Abierta** | Registrada, pendiente de atender. |
| ✅ **Corregida** | Se aplicó el cambio y el revisor lo verificó. |
| ❌ **Rechazada** | No se aplica; se justifica en "Acción tomada". |
| ⏸️ **Pospuesta** | Se atenderá después; referenciar issue. |

### Cómo usar esta bitácora

- **Una fila por review** en la Tabla 1 (ID consecutivo `CR-001`, `CR-002`…). Normalmente corresponde a un Pull Request.
- **Resultado del review:** Aprobado · Aprobado con cambios · Cambios requeridos (requiere un nuevo review).
- **Una fila por observación** en la Tabla 2. Su ID combina el review y un consecutivo: `CR-001-01`, `CR-001-02`…
- **Al corregir,** el autor anota la acción y el hash del commit; el revisor confirma, cambia el estado a Corregida y firma con sus iniciales y fecha.
- **El review se cierra** cuando todas sus observaciones Críticas y Mayores están Corregidas o justificadas. La fila de ejemplo (en cursiva) puede borrarse.

---

## Tabla 1. Registro de reviews

| ID | Fecha | PR / Rama | Autor | Revisor | Archivos modificados | Resumen del cambio | Resultado |
|---|---|---|---|---|---|---|---|
| *CR-001* | *12/11/2026* | *PR #4 · `feat/ingesta-enoe`* | *Integrante 1* | *Integrante 2* | *`etl/ingesta_enoe.py`, `etl/schemas.py`, `README.md`* | *Lectura de COE1 y SDEM a capa Plata (Parquet por año)* | *Aprobado con cambios* |
| | | | | | | | |

---

## Tabla 2. Registro de observaciones y seguimiento

| ID obs. | Review | Archivo / línea | Observación | Severidad | Acción tomada | Estado | Commit | Verificó / fecha |
|---|---|---|---|---|---|---|---|---|
| *CR-001-01* | *CR-001* | *`etl/schemas.py:42`* | *La columna `ent` se lee como string; debe ser entero para el cruce por entidad.* | *🟠 Mayor* | *Se definió `IntegerType` en el esquema de SDEM.* | *✅ Corregida* | *`a3f9c21`* | *I2 · 13/11* |
| | | | | | | | | |

---

## Resumen de seguimiento por review

*Se actualiza al cerrar cada review. Permite ver de un vistazo cuántas observaciones se encontraron y cuántas se corrigieron.*

| Review | Total obs. | Críticas | Mayores | Menores / Sug. | Corregidas | Pendientes | Fecha de cierre | Comentarios |
|---|---|---|---|---|---|---|---|---|
| *CR-001* | *1* | *0* | *1* | *0* | *1* | *0* | *13/11/2026* | *Cerrado* |
| | | | | | | | | |
