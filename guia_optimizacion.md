# Guía práctica de buenas prácticas y optimización en PySpark

**Proyecto:** Mexico Economic Pipeline
**Actividad 10 · Procesamiento de Grandes Bases de Datos · MCD, CUCEA**

## Propósito y alcance

Esta guía orienta las decisiones de implementación del pipeline de ENOE, IGAE, INPC y SHCP. Las recomendaciones se adaptan al diseño del proyecto; no representan optimizaciones ejecutadas ni mejoras de rendimiento comprobadas.

La referencia técnica es Spark 3.5.3, versión declarada actualmente en `requirements.txt`. Si el equipo acuerda otra versión, deberá actualizar las dependencias y revisar esta guía. Las rutas se interpretan desde la raíz del repositorio.

## 1. Ciclo de optimización

| Etapa | Pregunta | Aplicación al proyecto | Evidencia que se registrará |
| --- | --- | --- | --- |
| Definir objetivo | ¿Qué queremos mejorar y qué resultado esperamos? | Delimitar una operación, por ejemplo la unión de COE1 y SDEM de un trimestre. Establecer qué tiempo o consumo se busca reducir. | Operación, datos utilizados, resultado esperado y criterio de aceptación. |
| Medir | ¿Cuál es la situación inicial? | Ejecutar una línea base con una acción que materialice el resultado que interesa medir. | Tiempo, plan, métricas de Spark UI, configuración y controles de calidad. |
| Identificar | ¿Dónde está el problema? | Distinguir lectura lenta, redistribución de datos, tareas desbalanceadas o presión de memoria. | Stage, operador o tarea asociado al problema observado. |
| Ajustar | ¿Qué cambio podría ayudar? | Modificar una decisión a la vez, como columnas seleccionadas o estrategia de unión. | Cambio específico y motivo técnico. |
| Validar | ¿Mejoró y conserva resultados correctos? | Repetir la operación en condiciones comparables y contrastar calidad y rendimiento. | Comparación, diferencias detectadas y decisión de conservar o revertir. |

**Regla de medición:** definir transformaciones no mide su procesamiento, porque Spark difiere su ejecución hasta una acción. Un `count()` sirve para medir un conteo, pero no necesariamente evalúa todas las columnas que produciría una escritura. Para comparar una salida del pipeline, medir la misma escritura en rutas separadas, con la misma entrada y configuración. Registrar si la caché estaba fría o materializada; realizar varias ejecuciones comparables cuando se evalúe rendimiento y reportar su variabilidad.

## 2. Calidad y coherencia antes del rendimiento

Estas son decisiones del proyecto que deben acordarse con los diccionarios y metadatos de cada fuente.

| Recomendación | Qué hacer | Cuándo conviene | Cómo verificar |
| --- | --- | --- | --- |
| Esquemas y lectura controlada | Definir tipos y opciones de CSV; preservar ceros iniciales de identificadores. Homologar cambios de nombre entre períodos antes de unirlos. | Al incorporar archivos de distintas etapas de ENOE o nuevos formatos. | Comparar `printSchema()` con el diccionario; revisar encabezados, codificación y nulos nuevos después de conversiones. Véase [R2]. |
| Validar llaves y duplicados | Definir la unidad de observación y la llave por tabla y período. Investigar duplicados antes de eliminarlos. | Antes de unir COE1 con SDEM o combinar períodos. | Agrupar por la llave y buscar conteos mayores que uno; comprobar llaves nulas y registros sin correspondencia. |
| Controlar reglas de negocio | Distinguir datos faltantes, códigos especiales y valores válidos. Conservar factores de expansión de ENOE para los indicadores que los requieran. | Al calcular empleo, ingreso y otras medidas laborales. | Registrar nulos y códigos especiales por período; contrastar indicadores de una muestra con un cálculo independiente según su definición. |
| Homologar tiempo y unidades | Documentar regla mensual–trimestral, moneda, unidad y base de índices. Exigir cobertura temporal suficiente para cada agregación. | Antes de integrar IGAE, INPC y SHCP. | Revisar meses disponibles por trimestre y ejemplos manuales. No interpretar un trimestre incompleto como completo. |
| Preservar granularidad | Agregar cada fuente a la unidad acordada antes de unir. Los indicadores nacionales conservan ese alcance al asociarse a entidades. | Al construir el panel trimestral. | Comprobar unicidad de la tabla derecha por llave temporal y filas antes/después del join. Evitar sumar indicadores nacionales repetidos por entidad. |

## 3. Lectura, escritura y transformaciones

| Recomendación | Qué hacer | Cuándo conviene | Cómo verificar |
| --- | --- | --- | --- |
| Seleccionar y filtrar pronto | Conservar columnas y períodos necesarios antes de operaciones costosas, sin eliminar registros requeridos por la lógica del análisis. | En ingesta y preparación para joins. | Revisar `ReadSchema`, `PartitionFilters` y `PushedFilters` cuando correspondan al formato; contrastar resultados y volumen de entrada. |
| Preparar Parquet | Conservar originales y crear datos tipados para consultas repetidas. | Cuando una fuente ya fue interpretada y validada. | Releer la salida y comparar esquema, filas y totales de control. Parquet conserva información de esquema [R3]. |
| Separar particiones de disco y ejecución | Evaluar `partitionBy("anio")` para consultas por año; considerar tamaño real del conjunto. | Principalmente para datos ENOE voluminosos; un panel final pequeño puede no necesitarlo. | Revisar carpetas, archivos y filtros de partición del plan. Evitar fragmentar por identificadores de alta cardinalidad [R3]. |
| Hacer escrituras reproducibles | Definir rutas por fuente y etapa; repetir una carga sin duplicar información. No sobrescribir originales. | En cada ejecución o actualización de un período. | Ejecutar dos veces sobre datos de prueba y comprobar llaves, filas y períodos conservados. El modo de escritura debe documentarse. |
| Priorizar funciones de Spark | Usar expresiones nativas para tipos, fechas y cálculos; justificar UDF de Python. | En transformaciones repetidas sobre muchos registros. | Revisar el plan y probar casos de nulos, fechas y valores límite antes de comparar tiempos. |

## 4. Joins, agregaciones, shuffle y memoria

| Recomendación | Qué hacer | Cuándo conviene | Cómo verificar |
| --- | --- | --- | --- |
| Elegir estrategia de join | Evaluar broadcast solo para una tabla pequeña que quepa en memoria. | Para series agregadas de IGAE, INPC o SHCP. | Revisar operador físico, memoria y filas resultantes [R1, R4]. |
| Reducir shuffle innecesario | Evitar redistribuciones repetidas y ajustar particiones con evidencia. | En joins y agregaciones ENOE. | Relacionar `Exchange` con shuffle y tareas en UI; conservar controles de calidad [R1, R4]. |
| Agregar con criterio | Agrupar solo por dimensiones del indicador y calcular medidas compatibles. | Antes del panel trimestral. | Revisar unicidad, ponderaciones y totales; no promediar promedios sin denominadores. |
| Evaluar número de particiones | Probar `repartition` o `coalesce` según necesidad; evitar `coalesce(1)` por rutina. | Ante desbalance o archivos demasiado pequeños. | Comparar tareas y archivos, duración y distribución del trabajo [R1, R4]. |
| Usar caché selectivamente | Persistir intermediarios reutilizados y liberarlos con `unpersist()`. | Si evita trabajo repetido y existe memoria suficiente. | Revisar Storage y tiempo total, incluyendo materialización [R1, R4]. |
| Verificar AQE | Consultar `spark.sql.adaptive.enabled`; revisar su plan final. | En consultas con shuffle. | Comparar plan y ejecución; AQE no corrige llaves erróneas [R1]. |
| Proteger el driver | Evitar `collect()` o `toPandas()` de microdatos completos. Exportar resultados agregados pequeños. | Al graficar o inspeccionar ENOE. | Revisar tamaño esperado y memoria antes de transferir resultados. |

No fijar ocho particiones ni una cantidad de memoria como solución universal. El ajuste depende de los datos, las operaciones y el equipo disponible.

## 5. Herramientas de verificación

Los siguientes fragmentos son ejemplos para adaptar cuando existan los DataFrames; no constituyen un pipeline ejecutable.

```python
# Plan físico de una operación propuesta.
df_resultado.explain(mode="formatted")

# Configuración y dirección efectiva de la interfaz de esta sesión.
print(spark.version)
print(spark.conf.get("spark.sql.shuffle.partitions"))
print(spark.conf.get("spark.sql.adaptive.enabled"))
print(spark.sparkContext.uiWebUrl)
```

| Herramienta | Qué observar | Para qué se usará en el proyecto |
| --- | --- | --- |
| Plan físico | Lecturas, filtros, agregaciones, joins y `Exchange` | Formular una hipótesis sobre el costo; no asumir que todo `Exchange` es un error. |
| Spark UI: Jobs y SQL | Duración y consulta asociada | Relacionar la acción medida con su ejecución. |
| Spark UI: Stages | Shuffle, spill y duración de tareas | Ubicar desbalance o presión de memoria; spill por sí solo no prueba un fallo. |
| Spark UI: Storage y Executors | Persistencia, uso de recursos y GC | Evaluar caché y restricciones de memoria. |

Las métricas se consultan según la disponibilidad de cada ejecución [R4]. El plan previo a ejecutar no siempre muestra las decisiones finales de AQE.

## 6. Validación y registro de decisiones

Antes de aceptar un cambio, comparar esquema, filas, unicidad de llaves, nulos, cobertura y totales relevantes. Para una comparación completa de dos DataFrames de prueba con columnas alineadas, considerar diferencias en ambos sentidos con `exceptAll`; para números de punto flotante, definir tolerancias por columna. La coincidencia del conteo, por sí sola, no demuestra igualdad.

Registrar cada evaluación en el PR correspondiente conforme a [CONTRIBUTING.md](../CONTRIBUTING.md):

| Campo | Contenido por completar cuando se ejecute |
| --- | --- |
| Objetivo e hipótesis | Operación, problema y mejora esperada. |
| Contexto reproducible | Commit, archivos/períodos, Spark, equipo, configuración y estado de caché. |
| Línea base y ajuste | Misma acción, métricas antes/después y cambio aplicado. |
| Calidad | Controles utilizados y diferencias encontradas. |
| Evidencia y decisión | Plan, captura o registro; conservar, revertir o investigar. |

En esta entrega no se requieren mediciones ni comparaciones ejecutadas. Los campos quedan como pauta de seguimiento; no deben completarse con resultados ficticios.

## 7. Referencias técnicas

Documentación oficial de Apache Spark 3.5.3, consultada el 11 de noviembre de 2026. Los criterios de integración y calidad específicos del proyecto deben validarse además con los metadatos de las fuentes listadas en [fuentes.md](fuentes.md).

- **[R1]** Apache Spark. [Performance Tuning](https://archive.apache.org/dist/spark/docs/3.5.3/sql-performance-tuning.html): estrategias de join, caché, particiones y AQE.
- **[R2]** Apache Spark. [CSV Files](https://archive.apache.org/dist/spark/docs/3.5.3/sql-data-sources-csv.html): esquemas y opciones de lectura.
- **[R3]** Apache Spark. [Parquet Files](https://archive.apache.org/dist/spark/docs/3.5.3/sql-data-sources-parquet.html): formato y particionamiento de archivos.
- **[R4]** Apache Spark. [Web UI](https://archive.apache.org/dist/spark/docs/3.5.3/web-ui.html): planes y métricas de ejecución.
