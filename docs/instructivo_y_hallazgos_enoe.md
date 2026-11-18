# ENOE · Preparación local de datos y hallazgos de encoding

**Proyecto Integrador · Procesamiento de Grandes Bases de Datos · Repositorio `mexico-economic-pipeline`**

> Los datos de la ENOE **no se suben al repositorio**, por privacidad y por tamaño. Cada integrante los descarga y prepara en su propia computadora con los scripts del repo.

---

## Parte 1 · Instructivo para correr los scripts localmente

### 1.1 Requisitos

| Requisito | Detalle |
|---|---|
| Python | **3.10 o superior** (`python --version`). Sin dependencias externas. |
| Espacio libre | **~25 GB**: ~3.7 GB de ZIP + ~20 GB de CSV extraídos (COE1 + SDEM). |
| Repositorio | Clonado y actualizado: `git switch dev` y `git pull`. |

### 1.2 Estructura de carpetas

Todo se trabaja **dentro del repo**, en la carpeta `data/`, que está en `.gitignore`:

```
mexico-economic-pipeline/          <- desde aquí se corren todos los comandos
├── scripts/
│   ├── extraer_enoe.py
│   └── normalizar_utf8.py
├── data/                          <- NO se sube a GitHub
│   └── enoe/
│       ├── zips/                  <- (1) aquí van los 85 ZIP descargados de INEGI
│       └── raw/                   <- (2) aquí los genera extraer_enoe.py
│           ├── 2005_1/
│           ├── 2005_2/
│           └── ...
├── logs/                          <- salida de los scripts (evidencia)
└── docs/
```

Antes de copiar datos, verifica que Git ignore la carpeta. Debe responder con la regla del `.gitignore`:
```
git check-ignore -v data/enoe/zips/prueba.zip
```

### 1.3 Descargar los datos

1. Descarga la ENOE con la **Descarga masiva** de INEGI (`DescargaMasivaApp.exe`), en formato CSV.
2. Copia los **85 archivos `.zip`** a `data\enoe\zips\`. Van de `1_conjunto_de_datos_enoe_2005_1t_csv.zip` a `85_conjunto_de_datos_enoe_2026_2t_csv.zip`.

### 1.4 Comandos, en orden

Abre una terminal **en la raíz del repo** (`mexico-economic-pipeline`):

```
:: 0. Preparar carpetas y consola en UTF-8
mkdir data\enoe\zips data\enoe\raw logs
chcp 65001

:: 1. Extraer COE1 y SDEM de los 85 ZIP
python scripts\extraer_enoe.py data\enoe\zips data\enoe\raw > logs\extraccion.txt 2>&1

:: 2. Normalizar todos los CSV a UTF-8 sin BOM
python scripts\normalizar_utf8.py data\enoe\raw --no-backup > logs\normalizacion.txt 2>&1

:: 3. Revisar resultados
type logs\extraccion.txt
type logs\normalizacion.txt
```

> Los comandos no muestran nada mientras corren: la salida se guarda en `logs\`. Espera a que vuelva a aparecer el prompt.
> Si el `mkdir` dice que alguna carpeta ya existe, no pasa nada.

### 1.5 Resultado esperado

| Log | Debe decir |
|---|---|
| `logs\extraccion.txt` | `Resumen: 85 ZIP extraídos, 0 errores.` y `Trimestres faltantes en la serie: 2020-T2` |
| `logs\normalizacion.txt` | `Resumen: 65 convertidos, 105 ya estaban en UTF-8, 0 errores.` |

**2020-T2 faltante es correcto:** INEGI no publicó ese trimestre por la pandemia.
Si se corre la normalización por segunda vez, dirá `0 convertidos, 170 ya estaban en UTF-8`, porque ya no queda nada por convertir.

### 1.6 Problemas comunes

| Síntoma | Solución |
|---|---|
| `can't open file ...scripts\...` | No estás en la raíz del repo. Usa `cd` hasta `mexico-economic-pipeline`. |
| `No se encontraron ZIP` | Los ZIP no están en `data\enoe\zips\`. |
| `[OMITIDO] ... no se reconoce año/trimestre` | Nombre de ZIP no previsto; reportarlo al equipo. |
| Acentos raros en la consola (`aÃ±o`, `a±o`) | Ejecuta `chcp 65001` antes de `type`, o abre el log en VS Code. |
| Error de ruta demasiado larga | Clona el repo en una ruta más corta, p. ej. `D:\repos\`. |
| Falta espacio | Los CSV de `data\enoe\raw` se pueden borrar y regenerar desde los ZIP en cualquier momento. |

### 1.7 Lectura en Spark (después de los scripts)

```python
opts = {"header": "true", "encoding": "UTF-8"}   # ya no latin1
df = spark.read.options(**opts).csv(ruta)
```

---

## Parte 2 · Resumen de hallazgos

### 2.1 Antes de los scripts

Corrida completa sobre los **85 trimestres (170 archivos: COE1 + SDEM)**:

| Encoding original | Archivos | Dónde |
|---|---|---|
| ASCII / UTF-8 | 105 | La mayoría de COE1 y parte de SDEM |
| **UTF-8 con BOM** | **34** | COE1 y SDEM de **2016-T1 a 2019-T4** y **2022-T2** (17 trimestres) |
| **cp1252** (Windows) | **31** | **Solo SDEM**: 2009, 2011-T1/T2, 2013–2015, 2021-T3 a 2023-T1 (excepto 2022-T2), 2024-T3/T4, 2025-T2 a 2026-T2 |

Además:
- Los ZIP tienen **3 formatos de nombre**, no 2: `..._enoe_2005_1t_csv.zip`, `NN_2017_trim1_enoe_csv.zip` (2017-T1 a **2018-T1**) y `..._enoe2018_2t_csv.zip` (**2018-T2**, sin guion bajo).
- Los ZIP de 2017 incluyen un archivo `*_bitacora_de_cambios.csv` junto a los datos.
- **2020-T2 no existe** en la descarga de INEGI.

### 2.2 Problemas que causaba

| Problema | Consecuencia |
|---|---|
| **BOM** (bytes `EF BB BF` al inicio) | La primera columna llega como `\ufeffr_def` (o `ï»¿r_def` si se lee con latin1) en lugar de `r_def`, que es una de las 13 llaves del join. |
| **Estrategia inicial `latin1`** | El fix del BOM buscaba `\ufeff` y no detecta `ï»¿`. `r_def` queda nula y el inner join descarta todo el trimestre: **17 de 85 trimestres (20 %) se perderían sin ningún error**. |
| **cp1252** | Leído como UTF-8, produce error o caracteres `�`. |
| Regex del reporte para nombres de ZIP | No reconocía 2018-T2: ese trimestre se habría omitido. |
| `glob(...)[0]` en 2017 | Podía leer la bitácora de cambios en lugar de los datos. |

### 2.3 Después de los scripts

| Resultado | Detalle |
|---|---|
| 85 ZIP extraídos | Solo el CSV principal de COE1 y SDEM; 0 errores. |
| **170 archivos en UTF-8 sin BOM** | 65 convertidos (34 BOM + 31 cp1252) + 105 ya correctos; **0 errores, 0 avisos**. |
| Encabezados correctos | La primera columna es `r_def` en todos los trimestres. |
| Lectura uniforme | Spark lee todo con `encoding="UTF-8"`. |

### 2.4 Qué se corrigió / cambió

- **BOM eliminado** en 34 archivos (17 trimestres).
- **31 SDEM convertidos** de cp1252 a UTF-8, conservando exactamente los mismos caracteres.
- **Estrategia de lectura:** de `latin1` a normalización previa + `UTF-8`.
- **Extracción:** reconoce los 3 formatos de nombre (incluido 2018-T2) y excluye las bitácoras de cambios.
- **Logs** escritos siempre en UTF-8, como evidencia reproducible.

### 2.5 Qué NO se cambió / NO se corrigió, y por qué

| Qué | Por qué |
|---|---|
| **Los valores de los datos** | El script solo cambia la codificación (cómo se guardan los bytes), no el contenido. Los códigos numéricos quedan idénticos. |
| **Errores de captura de INEGI** (p. ej. `SE INDEPENDIZË` en lugar de `SE INDEPENDIZÓ` en `cs_p21_des`) | Vienen así en el archivo original; no es un problema de encoding. Esas columnas de texto libre no se usan en el ETL, y corregirlas automáticamente podría alterar textos legítimos. Se documenta. Verificado en SDEM 2026-T2; no se revisó en los demás SDEM cp1252. |
| **2020-T2** | No existe en la fuente (pandemia). La serie queda con 85 trimestres. |
| **Los ZIP originales** | Se conservan intactos como respaldo inmutable; los CSV se regeneran desde ellos. |
| **Cambios de esquema** (`ent`/`cve_ent`, `fac`/`fac_tri`, nº de columnas) | No son de encoding; los resuelve el ETL (renombrado y `safe_select`). |
| **Catálogos, COE2, HOG, VIV** | No se usan en el ETL; no se extraen. Los catálogos se pueden obtener con `--catalogos`. |
| **Código del ETL en Spark y reporte inicial** | Pendiente: cambiar a `encoding="UTF-8"`, ampliar el fix del BOM, actualizar el regex de nombres de ZIP, agregar la validación de conteos por trimestre y actualizar la sección 3.1 del reporte. |
