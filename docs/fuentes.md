# Fuentes de Datos

Este documento describe cada fuente de datos utilizada en el proyecto, su justificación, variables clave seleccionadas y el mapeo de cruce con las demás fuentes.

---

## 1. ENOE — Encuesta Nacional de Ocupación y Empleo

**Institución:** Instituto Nacional de Estadística y Geografía (INEGI)  
**URL de descarga:** https://inegi.org.mx/programas/enoe/15ymas/#datos_abiertos  
**Frecuencia:** Trimestral  
**Cobertura:** 2005-T1 a 2026-T2 (85 períodos, ~3.25 GB comprimidos)

### Descripción

La ENOE es la encuesta de mayor cobertura sobre el mercado laboral en México. Se levanta en viviendas particulares a nivel nacional con representatividad a nivel de entidad federativa. Es la fuente oficial para indicadores como la Tasa de Desocupación (TD) y la Tasa de Informalidad Laboral (TIL).

### Tablas utilizadas

| Tabla | Registros/trimestre | Uso |
|-------|-------------------|-----|
| SDEM (Sociodemográfico) | ~390,000–425,000 | Variables de persona: sexo, edad, escolaridad, ingreso, formalidad |
| COE1 (Cuestionario de Ocupación parte 1) | ~306,000–345,000 | Variables de ocupación: sector, horas, tipo de empresa |

### Variables clave seleccionadas

| Variable | Descripción |
|----------|-------------|
| `clase1` | Condición de actividad (1=Ocupado, 2=Desocupado, 3=PNEA) |
| `ingocup` | Ingreso mensual de la ocupación (pesos corrientes) |
| `hrsocup` | Horas trabajadas en semana de referencia |
| `seg_soc` | Acceso a seguridad social (1=Sí, 2=No) |
| `pos_ocu` | Posición en la ocupación (asalariado, cuenta propia, etc.) |
| `rama` / `scian` | Sector económico de actividad |
| `ent` | Entidad federativa (1–32) |
| `fac` / `fac_tri` | Factor de expansión trimestral — **obligatorio para estimaciones poblacionales** |
| `sub_o` | Subocupación (horas insuficientes) |
| `tip_con` | Tipo de contratación (escrito/verbal/sin contrato) |
| `p4b` | Pago de impuestos del negocio (formalidad fiscal) |

### Cruces con otras fuentes

| Fuente | Variable ENOE | Variable destino | Análisis |
|--------|--------------|-----------------|---------|
| IGAE | `rama` / `scian` | Sector IGAE | Empleo por unidad de producto por sector |
| IGAE | `hrsocup` | Índice de volumen físico | Productividad laboral por hora |
| INPC | `ingocup` | INPC general | Ingreso real (poder adquisitivo) |
| INPC | `salario` | INPC por subíndice | Salario mínimo real trimestral |
| SHCP | `seg_soc` | Gasto en seguridad social | Cobertura efectiva vs gasto público |
| SHCP | `p4b` | Recaudación ISR/IVA | Informalidad fiscal y recaudación |
| SHCP | `ent` | Transferencias por entidad | Distribución territorial del gasto y empleo |

### Consideraciones técnicas

- **Encoding:** `latin1` (UTF-8-SIG con BOM en trimestres de 2017)
- **Columna de entidad:** `ent` (2005–2022) → `cve_ent` (2023+) — normalizar a `ent` en ETL
- **Factor de expansión:** `fac` (hasta 2022) → `fac_tri` (2023+)
- **2020-T2 no disponible** por pandemia
- **Join COE1 ↔ SDEM:** 13 columnas de llave compuesta (`r_def`, `cd_a`, `ent`, `con`, `upm`, `d_sem`, `n_pro_viv`, `v_sel`, `n_hog`, `h_mud`, `n_ent`, `per`, `n_ren`)

---

## 2. IGAE — Indicador Global de la Actividad Económica

**Institución:** INEGI  
**URL de descarga:** https://www.inegi.org.mx/temas/igae/  
**Frecuencia:** Mensual  
**Cobertura:** 2003 en adelante

### Descripción

El IGAE mide mensualmente el comportamiento de la economía mexicana a través de un índice de volumen físico (base 2018=100). Es el indicador de mayor frecuencia del ciclo económico en México, equivalente a un PIB mensual aproximado. Se desagrega en cuatro series: actividades primarias, secundarias, terciarias y total.

### Variables clave seleccionadas

| Variable | Descripción |
|----------|-------------|
| `PERIODO` | Fecha en formato YYYY/MM |
| `ACTIVIDAD` | Sector (Primarias, Secundarias, Terciarias, Total) |
| `INDICE` | Valor del índice de volumen físico (base 2018=100) |

### Cruces con otras fuentes

| Fuente | Variable IGAE | Variable destino | Análisis |
|--------|--------------|-----------------|---------|
| ENOE | Sector | `rama` / `scian` | Empleo generado por unidad de actividad económica |
| INPC | Variación mensual | INPC mensual | Relación entre actividad económica e inflación |
| SHCP | Índice total | Gasto público | Efecto del gasto en el ciclo económico |

### Consideraciones técnicas

- Archivo fuente: `IGAE_2.xlsx` — requiere `melt()` de wide a long format
- Agregación a trimestral: promedio de los 3 meses del trimestre
- 1,612 registros totales (4 actividades × 403 períodos mensuales)

---

## 3. INPC — Índice Nacional de Precios al Consumidor

**Institución:** INEGI  
**URL de descarga:** https://www.inegi.org.mx/temas/inpc/  
**Frecuencia:** Mensual (quincenal disponible)  
**Cobertura:** 2002 en adelante

### Descripción

El INPC mide la variación de los precios de una canasta de bienes y servicios representativa del consumo de los hogares mexicanos. Es el indicador oficial de inflación. Se publica desagregado por subíndices (alimentos, vivienda, transporte, servicios, etc.) y por ciudades.

### Variables clave seleccionadas

| Variable | Descripción |
|----------|-------------|
| `fecha` | Mes de referencia |
| `inpc_general` | Índice general (base 2018=100) |
| `inpc_alimentos` | Subíndice de alimentos y bebidas |
| `inpc_vivienda` | Subíndice de vivienda |
| `inpc_transporte` | Subíndice de transporte |
| `variacion_anual` | Inflación anual (%) |

### Cruces con otras fuentes

| Fuente | Variable INPC | Variable destino | Análisis |
|--------|--------------|-----------------|---------|
| ENOE | INPC general | `ingocup` | Deflactar ingreso nominal → ingreso real |
| IGAE | Variación mensual | Variación IGAE | Brecha entre actividad e inflación |
| SHCP | INPC por subíndice | Gasto por función | Presiones inflacionarias en gasto público |

### Consideraciones técnicas

- Fecha de referencia del INPC: último día hábil de cada mes
- Para cruce trimestral con ENOE: usar el INPC del tercer mes del trimestre (mes de cierre)
- Fórmula de deflactación: `ingreso_real = ingocup / (INPC / 100)`

---

## 4. Deuda Pública — SHCP

**Institución:** Secretaría de Hacienda y Crédito Público (SHCP)  
**URL de descarga:** https://www.transparenciapresupuestaria.gob.mx/  
**Frecuencia:** Mensual  
**Cobertura:** 2000–2026

### Descripción

Datos de la deuda pública del gobierno federal mexicano, desagregados por tipo (interna/externa), instrumento y plazo. Permite analizar el perfil de endeudamiento soberano y su relación con el ciclo económico.

### Variables clave seleccionadas

| Variable | Descripción |
|----------|-------------|
| `fecha` | Mes de referencia |
| `deuda_interna` | Deuda interna en millones de pesos |
| `deuda_externa` | Deuda externa en millones de USD |
| `deuda_total_pib` | Razón deuda/PIB (%) |
| `tipo_instrumento` | CETES, Bonos, Udibonos, etc. |

### Cruces con otras fuentes

| Fuente | Variable SHCP | Variable destino | Análisis |
|--------|--------------|-----------------|---------|
| IGAE | Deuda total | Índice IGAE | Relación entre endeudamiento y actividad económica |
| INPC | Deuda real | Inflación | Efecto de la inflación en el valor real de la deuda |
| ENOE | Gasto social | `seg_soc` | Capacidad fiscal para financiar seguridad social |

### Consideraciones técnicas

- Archivo fuente: `deuda_publica.csv` y `deuda_publica_hist.csv`
- Deuda externa requiere conversión a pesos usando tipo de cambio (FIX Banxico)
- Para cruce trimestral: usar saldo al cierre del trimestre

---

## Dimensión temporal — Estrategia de cruce entre fuentes

La granularidad temporal es el punto crítico del JOIN entre fuentes:

| Fuente | Frecuencia original | Estrategia para cruce trimestral |
|--------|-------------------|----------------------------------|
| ENOE | Trimestral | Usar directamente `anio` + `trimestre` |
| IGAE | Mensual | Promedio de los 3 meses del trimestre |
| INPC | Mensual | Valor del mes de cierre del trimestre (mar, jun, sep, dic) |
| SHCP | Mensual | Saldo/valor acumulado al cierre del trimestre |

**Clave de join temporal recomendada en todas las fuentes:**

```python
# Columnas a agregar en cada DataFrame antes del join
df = df.withColumn("anio", F.lit(year))
df = df.withColumn("trimestre", F.lit(quarter))  # 1, 2, 3, 4
```
