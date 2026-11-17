# Normalización de archivos CSV a UTF-8

**Proyecto Integrador · Procesamiento de Grandes Bases de Datos · ETL ENOE**
Justificación técnica y manual de uso de `scripts/normalizar_utf8.py`

---

## 1. Contexto

El análisis inicial de la ENOE revisó tres periodos y encontró encodings distintos en los CSV principales:

| Periodo | Encoding detectado | Observación |
|---|---|---|
| 2005-T1 | ASCII | Sin BOM |
| 2017-T1 | UTF-8 con BOM | La primera columna llega como `\ufeffr_def` |
| 2026-T2 | ASCII | Sin BOM |

Además, el pipeline integra fuentes de distintos productores (INEGI y SHCP), y los catálogos de la ENOE contienen etiquetas con acentos y ñ. Antes de la lectura con Spark se necesita un criterio único de codificación para los 85 trimestres.

---

## 2. Por qué UTF-8

1. **Es el estándar universal.** Es la codificación por defecto de Python 3, Spark, Parquet, JSON, Git y la web.
2. **Es compatible con ASCII.** Todo archivo ASCII ya es UTF-8 válido, byte por byte. Los tres periodos analizados ya cumplen con UTF-8.
3. **Representa cualquier carácter.** Acentos, ñ, símbolos y cualquier idioma, sin tablas regionales.
4. **Un solo encoding en todo el pipeline.** Bronce (CSV) y Plata (Parquet, que almacena texto en UTF-8 por especificación) quedan en la misma codificación.
5. **Detecta errores en lugar de ocultarlos.** Una secuencia de bytes inválida produce un error visible, no texto corrupto silencioso.

---

## 3. Por qué no leer con `latin1`

La estrategia inicial proponía leer todos los CSV con `encoding="latin1"`. Tiene dos problemas:

**a) El BOM de 2017 deja de detectarse.** Leídos como latin1, los bytes del BOM (`EF BB BF`) se convierten en los caracteres `ï»¿`, no en `\ufeff`:

| Lectura | Primera columna (2017) | ¿El fix de BOM la detecta? |
|---|---|---|
| UTF-8 | `\ufeffr_def` | Sí |
| latin1 | `ï»¿r_def` | No |

Consecuencia: la llave `r_def` "no existe", `safe_select` la rellena con `NULL` y el *inner join* de 13 llaves descarta todos los registros. **Los 4 trimestres de 2017 quedarían vacíos sin ningún error.**

**b) latin1 nunca falla.** Cualquier byte es un carácter válido en latin1, así que un texto UTF-8 con acentos se convertiría en `Ã±`, `Ã³`, etc. sin aviso.

---

## 4. Estrategia adoptada

1. **Normalizar a UTF-8 sin BOM** después de descomprimir y antes de leer con Spark.
2. **Los ZIP originales son el respaldo inmutable.** Los CSV extraídos pueden regenerarse en cualquier momento.
3. **Validar los 85 trimestres**, no solo una muestra: el script reporta archivo por archivo el encoding de origen.
4. **Leer en Spark siempre con `encoding = "UTF-8"`.**
5. **Conservar un fix defensivo del BOM** que cubra `\ufeff` y `ï»¿`.
6. **Validar conteos por trimestre** (SDEM, COE1 y join) antes de escribir la capa Plata.

### Excepciones consideradas

| Caso | Criterio |
|---|---|
| Archivos para abrir en Excel | Exportar como `utf-8-sig` (con BOM) solo para esos entregables. |
| Columnas de códigos (`ent`, `sex`, `eda`, …) | Son ASCII; la normalización no cambia sus valores. |
| Comparación de textos de distintas fuentes | Normalizar a forma Unicode NFC antes de comparar o unir. |

---

## 5. Manual de uso del script

### 5.1 Requisitos

- **Python 3.10 o superior.** Verificar con `python --version`.
- **Sin dependencias externas:** solo usa la biblioteca estándar.
- Ubicación en el repositorio: `scripts/normalizar_utf8.py`.

### 5.2 Qué hace

1. Detecta el encoding de cada archivo: UTF-8, UTF-8 con BOM, cp1252 o latin-1.
2. Si ya es UTF-8 sin BOM, no lo modifica.
3. Si no, lo convierte a **UTF-8 sin BOM**, procesando por bloques de 1 MB (soporta archivos de varios GB).
4. Escribe primero a un archivo temporal y **verifica que la salida sea UTF-8 válido** antes de reemplazar el original.
5. Avisa si detecta texto ya dañado de origen (por ejemplo `Ã±`).

### 5.3 Sintaxis

```
python scripts/normalizar_utf8.py <archivo.csv | carpeta> [más archivos o carpetas] [opciones]
```

| Opción | Descripción |
|---|---|
| *(sin opciones)* | Sobrescribe cada archivo con su versión UTF-8 y guarda el original como `archivo.csv.bak`. |
| `--outdir DIR` | Escribe las copias en otra carpeta, respetando subcarpetas, sin tocar los originales. |
| `--no-backup` | No crea el `.bak`. Recomendado para la ENOE: los ZIP son el respaldo. |
| `--encoding ENC` | Fuerza el encoding de origen (ej. `cp1252`, `latin-1`) si la detección no es adecuada. |
| `--lf` | Convierte los saltos de línea de Windows (`\r\n`) a `\n`. |

### 5.4 Ejemplos

**Un archivo:**
```
python scripts/normalizar_utf8.py conjunto_de_datos_sdem_enoe_2017_1t.csv
```

**Varios archivos:**
```
python scripts/normalizar_utf8.py coe1.csv sdem.csv
```

**Una carpeta completa (recursivo, todos los `.csv`):**
```
python scripts/normalizar_utf8.py data/enoe/raw/ --no-backup
```

**Sin modificar los originales:**
```
python scripts/normalizar_utf8.py data/enoe/raw/ --outdir data/enoe/raw_utf8
```

**Ruta con espacios (Windows):**
```
python scripts\normalizar_utf8.py "D:\Grandes Bases de Datos\data\enoe\raw"
```

### 5.5 Flujo recomendado en el proyecto

```
1. Descomprimir ZIPs        ->  data/enoe/raw/
2. Normalizar a UTF-8       ->  python scripts/normalizar_utf8.py data/enoe/raw/ --no-backup
3. Revisar el resumen       ->  0 errores y sin avisos de caracteres dañados
4. Leer con Spark en UTF-8  ->  ver 5.7
```

### 5.6 Cómo interpretar la salida

```
[UTF-8]  .../conjunto_de_datos_sdem_enoe_2017_1t.csv  (utf-8-sig -> utf-8)
[OK]     .../conjunto_de_datos_coe1_enoe_2005_1t.csv  ya está en UTF-8, sin cambios
         [AVISO] 3 posibles caracteres mal codificados (ej. 'Ã±'); revísalo.
[ERROR]  .../archivo.csv: <descripción>

Resumen: 1 convertidos, 1 ya estaban en UTF-8, 0 errores.
```

| Etiqueta | Significado | Acción |
|---|---|---|
| `[OK]` | Ya estaba en UTF-8 sin BOM; no se modificó. | Ninguna. |
| `[UTF-8]` | Se convirtió; entre paréntesis, el encoding de origen. | Ninguna. |
| `[AVISO]` | El texto parece dañado desde el origen. | Revisar el archivo; puede requerir corrección manual. |
| `[ERROR]` | No se pudo procesar; el original queda intacto. | Revisar el mensaje (ver 5.8). |

El script termina con código de salida `0` si no hubo errores y `1` si hubo alguno, lo que permite usarlo en scripts automatizados.

### 5.7 Lectura en Spark después de normalizar

```python
opts = {"header": "true", "encoding": "UTF-8"}
df = spark.read.options(**opts).csv(ruta)

# Fix defensivo del BOM (cubre ambos casos)
fc = df.columns[0]
limpio = fc.replace("\ufeff", "").replace("ï»¿", "")
if limpio != fc:
    df = df.withColumnRenamed(fc, limpio)
```

### 5.8 Problemas comunes

| Síntoma | Causa | Solución |
|---|---|---|
| `python` no se reconoce | Python no está en el PATH | Usar `py scripts\normalizar_utf8.py ...` |
| `SyntaxError` al ejecutar | Versión de Python menor a 3.10 | Actualizar Python |
| `PermissionError` | El CSV está abierto en Excel u otro programa | Cerrar el archivo y repetir |
| Falta espacio en disco | Los `.bak` duplican el tamaño | Usar `--no-backup` |
| Acentos raros en la consola de Windows | Es un problema de visualización de `cmd`, no del archivo | Verificar con VS Code o con el comando de 5.9 |

### 5.9 Verificación manual de un archivo

```
python -c "open(r'ruta\archivo.csv', encoding='utf-8').read(); print('UTF-8 válido')"
```

Si el archivo no es UTF-8 válido, Python muestra `UnicodeDecodeError`.
