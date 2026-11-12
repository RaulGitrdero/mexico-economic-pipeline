# Arquitectura del Pipeline

**Proyecto:** Mexico Economic Pipeline  
**Stack:** Python 3.10 · PySpark 3.5 · Parquet  
**Patrón:** Medallion Architecture (Bronce → Plata → Oro)

---

## Visión general

El pipeline procesa cuatro fuentes de datos públicas de México —ENOE, IGAE, INPC y SHCP— y las integra en una capa analítica unificada que permite responder preguntas sobre la relación entre empleo, actividad económica, inflación y finanzas públicas en el período 2005–2026.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CAPA BRONCE (raw)                             │
│   data/raw/                                                          │
│   ├── enoe/parquet/   ← CSV descomprimido → Parquet por período      │
│   ├── igae/parquet/   ← XLSX transformado → Parquet long-format      │
│   ├── inpc/parquet/   ← CSV mensual → Parquet                        │
│   └── shcp/parquet/   ← CSV deuda → Parquet                          │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │ validación + normalización
┌──────────────────────────────────▼───────────────────────────────────┐
│                        CAPA PLATA (clean)                            │
│   data/clean/                                                        │
│   ├── enoe_silver/    ← 29 columnas seleccionadas, tipos definidos   │
│   ├── igae_silver/    ← long format, columna trimestre agregada      │
│   ├── inpc_silver/    ← índices normalizados, base 2018=100          │
│   └── shcp_silver/    ← deuda consolidada en pesos                   │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │ join temporal (anio + trimestre)
┌──────────────────────────────────▼───────────────────────────────────┐
│                         CAPA ORO (gold)                              │
│   output/                                                            │
│   └── panel_economico_laboral/                                       │
│       └── part-*.parquet   ← Panel trimestral 2005–2026              │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Capas del pipeline

### Bronce — Ingesta cruda

**Propósito:** Leer los datos originales tal como los publica la fuente, convertirlos al formato Parquet binario y almacenarlos sin modificar su contenido semántico.

| Notebook | Fuente | Entrada | Salida |
|----------|--------|---------|--------|
| `01_ingesta_enoe.ipynb` | ENOE | 85 ZIPs (CSV) | Parquet por período |
| `02_ingesta_igae.ipynb` | IGAE | `IGAE_2.xlsx` | Parquet long-format |
| `03_ingesta_inpc.ipynb` | INPC | CSV mensual | Parquet mensual |
| `04_ingesta_shcp.ipynb` | SHCP | 2 CSV históricos | Parquet consolidado |

**Consideraciones de ENOE:**
- 85 períodos, 3 patrones de nombre de archivo (ver `docs/fuentes.md`)
- 2 tablas utilizadas por ZIP: `COE1` (ocupación) + `SDEM` (sociodemográfico)
- JOIN interno COE1 ↔ SDEM por 13 columnas de llave compuesta
- Encoding: `latin1` universal; BOM detectado y eliminado en 2017
- Columnas renombradas entre eras: `ent`→`cve_ent`, `fac`→`fac_tri` (2023+)

**Consideraciones de IGAE:**
- Archivo en formato wide (un período por columna) → `melt()` a long format
- Resultado: 4 actividades × N períodos mensuales

---

### Plata — Limpieza y normalización

**Propósito:** Aplicar transformaciones para garantizar calidad, consistencia de tipos y homologación entre períodos.

**Notebook principal:** `06_transformacion.ipynb`  
**Módulos reutilizables:** `src/transformacion/normalizar.py`

Transformaciones aplicadas a cada fuente:

| Transformación | ENOE | IGAE | INPC | SHCP |
|---------------|------|------|------|------|
| Cast de tipos | ✅ | ✅ | ✅ | ✅ |
| Normalizar nombres de columnas | ✅ | — | — | — |
| Eliminar duplicados | ✅ | ✅ | ✅ | ✅ |
| Agregar `anio` + `trimestre` | ✅ | ✅ | ✅ | ✅ |
| Melt wide→long | — | ✅ | — | — |
| Deflactar (ingreso real) | ✅ | — | — | — |
| Conversión moneda externa | — | — | — | ✅ |

**Función central de normalización ENOE** (en `src/ingesta/enoe.py`):

```python
def fix_df(df: DataFrame) -> DataFrame:
    """Normaliza nombres de columna entre eras (2005–2026)."""
    renames = {
        "cve_ent": "ent",
        "fac_tri": "fac",
        "cve_loc": "loc",
        "cve_mun": "mun",
        "cve_ageb": "ageb",
    }
    for old, new in renames.items():
        if old in df.columns and new not in df.columns:
            df = df.withColumnRenamed(old, new)
    return df
```

---

### Oro — Integración

**Propósito:** Construir el panel analítico unificado mediante JOINs temporales entre las cuatro fuentes.

**Notebook principal:** `07_integracion.ipynb`  
**Módulo:** `src/integracion/joins.py`

**Llave de integración temporal:**

```python
# Todas las fuentes deben tener estas dos columnas antes del JOIN
df = df.withColumn("anio", F.lit(year).cast("int"))
df = df.withColumn("trimestre", F.lit(quarter).cast("int"))  # 1, 2, 3, 4
```

**Estrategia de agregación mensual → trimestral:**

| Fuente | Meses en trimestre | Estrategia |
|--------|--------------------|------------|
| IGAE | 3 (ene-mar, abr-jun, ...) | Promedio del índice |
| INPC | 3 | Valor del último mes del trimestre |
| SHCP | 3 | Saldo al cierre del trimestre |

**Esquema del panel final (Parquet oro):**

```
anio            int       Año calendario
trimestre       int       1–4
ent             int       Entidad federativa (1–32)
n_trabajadores  long      Total ocupados (expandido por fac)
ingreso_real    double    Ingreso promedio deflactado (pesos 2018)
tasa_informal   double    % trabajadores sin seguridad social
hrsocup_prom    double    Horas trabajadas promedio semanal
igae_total      double    Índice IGAE total (base 2018=100)
igae_secundario double    Índice actividades secundarias
inpc_general    double    INPC general (base 2018=100)
inflacion_anual double    Variación anual del INPC (%)
deuda_pib_pct   double    Deuda pública / PIB (%)
```

---

## Flujo de dependencias entre notebooks

```
01_ingesta_enoe ──┐
02_ingesta_igae ──┤
03_ingesta_inpc ──┼──► 05_validacion ──► 06_transformacion ──► 07_integracion ──► 08_analisis
04_ingesta_shcp ──┘
```

Cada notebook de ingesta es **independiente** y puede ejecutarse en paralelo. La validación (`05`) requiere que al menos una fuente esté lista; la transformación (`06`) requiere las cuatro.

---

## Configuración de Spark

Parámetros recomendados para ejecución local:

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("mexico-economic-pipeline")
    .master("local[*]")
    .config("spark.driver.memory", "4g")
    .config("spark.sql.shuffle.partitions", "8")
    .config("spark.sql.parquet.compression.codec", "snappy")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")
```

> En máquinas con ≥16 GB RAM, subir `spark.driver.memory` a `8g` para procesar todos los períodos ENOE en un solo job.

---

## Particionamiento del Parquet

- **Bronce:** sin partición (un archivo por período)
- **Plata ENOE:** particionado por `anio` → lectura eficiente por año
- **Oro (panel):** particionado por `anio` → consultas por año sin scan completo

```python
df.write.partitionBy("anio").parquet("data/clean/enoe_silver/")
```
