# Evidencia de ejecución — Actividad 11

> Documento requerido por la sección 4 de la Actividad 11:  
> *"fuentes y conteos de entrada; decisiones principales de limpieza;  
> validaciones y resultados; transformaciones; conteo, granularidad y  
> ubicación de la salida"*

---

## 1. Fuentes y conteos de entrada

| Fuente | Formato original | Registros entrada | Período |
|--------|-----------------|-------------------|---------|
| ENOE | 85 ZIPs (CSV internos) | ~5.5 M filas (bronce) | 2005-T1 – 2026-T2* |
| INPC | CSV mensual (BIE INEGI) | ~1,989 registros | feb 2021 – abr 2026 |
| IGAE | XLSX (hoja Tabulado) | ~1,612 registros | ene 1993 – reciente |
| SHCP | 2 CSV (reciente + histórico) | ~878 registros limpios | 1990 – 2026 |

> *2020-T2 no existe en la descarga masiva del INEGI por pandemia. No es un error.

---

## 2. Decisiones de limpieza (ENOE)

Notebook: `05_limpieza_enoe.ipynb`

| # | Decisión | Registros afectados | Justificación |
|---|----------|---------------------|---------------|
| 1 | Casting de tipos (`eda`, `ing7c`, `hrsocup`, etc. a int/double) | Todos | Bronce llega como string; tipos incorrectos distorsionan agregaciones |
| 2 | Eliminar duplicados por llaves compuestas + período | Variable por año | Puede haber filas repetidas en el join SDEM×COE1 de algunos ZIPs |
| 3 | Filtrar `eda < 15` | < 0.1% | ENOE 15+ delimita su universo a personas de 15 años en adelante |
| 4 | Reemplazar `-1` por `NULL` en `ingocup`, `ing7c`, `hrsocup`, `salario` | Desocupados y PEI | Código INEGI para "no aplica"; no es cero ingreso |
| 5 | Crear columna `periodo` (formato `YYYYQn`) | Todos | Facilita joins temporales con INPC e IGAE |

---

## 3. Validaciones realizadas

### Antes de limpiar (entrada)
- Conteo de nulos por columna clave (`sex`, `eda`, `clase1`, `ing7c`, `hrsocup`, `fac`)
- Duplicados en las 13 llaves de join + período
- Rango de `eda`, `ing7c`, `hrsocup`, `anio`

### Después de limpiar (salida)
- Nulos en columnas obligatorias (`eda`, `sex`, `clase1`, `anio`, `trimestre`) → esperado: 0
- `eda_min >= 15`, `menores_15 = 0`
- Distribución de `clase1` coherente (mayoritariamente ocupados + PEI)
- Validación round-trip: Parquet Plata se relee correctamente

### En integración
- Conteo pre y post join (sin fan-out: filas deben ser iguales)
- Trimestres ENOE sin INPC correspondiente (nulos en `inpc_trim`)
- `salario_real > 0` para todos los ocupados con `ingocup > 0`
- Granularidad: una fila por persona × trimestre (sin duplicados)

---

## 4. Transformaciones aplicadas

### `05_limpieza_enoe.ipynb`
1. Cast de 17 columnas enteras y 4 columnas double
2. `dropDuplicates` por 13 llaves + `anio` + `trimestre`
3. `filter(eda >= 15)`
4. `when(col < 0, None)` en columnas de ingreso y horas
5. Nueva columna `periodo = concat(anio, 'Q', trimestre)`

### `06_integracion.ipynb`
1. INPC mensual → promedio trimestral por `anio` + `trimestre`
2. IGAE mensual → promedio trimestral por `anio` + `trimestre`
3. Left join ENOE × INPC por `anio` + `trimestre`
4. Left join panel × IGAE por `anio` + `trimestre`
5. `salario_real = ingocup × (INPC_base / inpc_trim)` base T4-2018
6. `ing7c_real   = ing7c   × (INPC_base / inpc_trim)` base T4-2018

---

## 5. Resultado: conteo, granularidad y ubicación de salida

| Conjunto | Ubicación | Granularidad | Columnas aprox. | Partición |
|----------|-----------|--------------|-----------------|-----------|
| ENOE Bronce | `data/raw/enoe/parquet/` | persona × trimestre | 43 | `anio` |
| ENOE Plata | `data/silver/enoe/` | persona × trimestre | 44 (+ `periodo`) | `anio` |
| Panel Analítico | `data/silver/panel_enoe_inpc/` | persona × trimestre | 46 (+ `inpc_trim`, `igae_total`, `salario_real`, `ing7c_real`) | `anio` |

**Formato de almacenamiento:** Parquet con compresión Snappy  
**Motor:** Apache Spark 3.5.x en modo local (`local[*]`)  
**Reproducibilidad:** ejecutar los tres notebooks en orden (ver README)

---

## 6. Instrucciones de reproducción

```bash
# Prerequisitos: Python 3.10+, Java 11/17, PySpark 3.5.x
pip install -r requirements.txt

# Paso 1 — Colocar datos fuente
# data/raw/inpc/   → conjunto_de_datos_inpc_mensual.csv
# data/raw/shcp/   → ingreso_gasto_finan.csv + ingreso_gasto_finan_hist.csv
# data/raw/igae/   → IGAE_2.xlsx
# data/raw/enoe/zips/ → 85 ZIPs trimestrales ENOE

# Paso 2 — Ejecutar pipeline en orden
jupyter notebook notebooks/ingesta_general.ipynb    # ~15-30 min (ENOE)
jupyter notebook notebooks/05_limpieza_enoe.ipynb   # ~5-10 min
jupyter notebook notebooks/06_integracion.ipynb     # ~3-5 min
```

> El pipeline no requiere conexión a internet durante la ejecución.  
> Los datos en `data/raw/` y `data/silver/` no se versionan en Git por su tamaño.
