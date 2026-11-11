# Mexico Economic Pipeline

**Proyecto Integrador · Procesamiento de Grandes Bases de Datos**
**Maestría en Ciencia de los Datos · CUCEA · Universidad de Guadalajara**
**Semestre: 2026-B**

Este proyecto busca reunir y preparar datos públicos de México sobre empleo, actividad económica, precios y deuda pública para facilitar su análisis conjunto. Se propone desarrollar un pipeline con PySpark: una secuencia de pasos para leer, validar, transformar e integrar información de distintas fuentes.

## Problema y relevancia

La información económica y laboral se publica en archivos con diferentes formatos, variables y frecuencias. Por ejemplo, los datos de empleo utilizados en el proyecto son trimestrales, mientras que las series de actividad económica y precios son mensuales. Estas diferencias dificultan compararlos directamente.

Organizar su procesamiento permitirá realizar comparaciones sobre una base común y documentar las decisiones de limpieza e integración. El conjunto resultante servirá para explorar cómo evolucionan el empleo, el poder adquisitivo, la actividad económica y el endeudamiento público. Las relaciones observadas no implicarán, por sí mismas, causalidad.

## Objetivo

Desarrollar un pipeline reproducible con PySpark para integrar datos de ENOE, IGAE, INPC y deuda pública de la SHCP en un conjunto analítico trimestral, mediante validaciones de calidad, homologación de variables y documentación del procesamiento.

## Fuentes de datos

| Fuente | Institución | Información de interés | Frecuencia de trabajo prevista |
| --- | --- | --- | --- |
| ENOE — Encuesta Nacional de Ocupación y Empleo | INEGI | Empleo, ingresos y características de la población ocupada | Trimestral |
| IGAE — Indicador Global de la Actividad Económica | INEGI | Actividad económica total y por grandes actividades | Mensual |
| INPC — Índice Nacional de Precios al Consumidor | INEGI | Evolución de precios y referencia para calcular ingresos reales | Mensual |
| Deuda pública | SHCP | Saldos y composición de la deuda pública | Mensual |

Los enlaces de consulta, variables y consideraciones de integración están en [Fuentes de datos](docs/fuentes.md).

La cobertura propuesta es 2005–2026; el período final se ajustará a la disponibilidad y comparabilidad de las cuatro fuentes. La integración deberá considerar períodos faltantes y diferencias de cobertura geográfica: los indicadores nacionales conservarán ese alcance aunque se relacionen con información laboral por entidad.

## Resultados esperados

- Datos preparados por fuente, con nombres de columnas, tipos y períodos homologados.
- Un conjunto analítico trimestral en formato Parquet para estudiar conjuntamente las variables seleccionadas.
- Validaciones documentadas de esquemas, valores nulos, duplicados y llaves de integración.
- Tablas y visualizaciones exploratorias sobre empleo, ingreso real, actividad económica, inflación y deuda pública.
- Un procedimiento reproducible y un historial de cambios mediante commits y Pull Requests.

Estos resultados corresponden al desarrollo previsto; todavía no se presenta una ejecución completa del pipeline en esta rama.

## Etapas del procesamiento

La arquitectura propuesta organiza los datos en tres capas: **bronce** para la ingesta, **plata** para la limpieza y **oro** para la integración analítica.

| Etapa | Trabajo previsto | Ubicación prevista |
| --- | --- | --- |
| Obtención e ingesta | Descargar los archivos, conservar los originales y preparar su lectura | `data/raw/` y `src/ingesta/` |
| Validación y transformación | Revisar calidad, homologar nombres y tipos, y preparar variables temporales | `src/transformacion/` y `data/clean/` |
| Integración | Agregar series a frecuencia trimestral y unirlas con llaves previamente validadas | `src/integracion/` y `output/` |
| Análisis | Elaborar indicadores, tablas y visualizaciones del conjunto integrado | `src/analisis/` |

El diseño inicial propone promediar el IGAE mensual por trimestre y utilizar valores de cierre para INPC y deuda. Estas decisiones deberán validarse según la definición de cada indicador antes de implementar las uniones.

El detalle se encuentra en [Arquitectura](docs/arquitectura.md). Los notebooks, módulos y salidas descritos allí representan el diseño previsto cuando sus archivos aún no estén incorporados al repositorio.

## Organización del repositorio

| Ruta | Función |
| --- | --- |
| `data/raw/` | Archivos originales y datos de la etapa de ingesta |
| `data/clean/` | Datos limpios y normalizados |
| `src/ingesta/` | Código reutilizable para lectura y carga |
| `src/transformacion/` | Código de limpieza y transformación |
| `src/integracion/` | Código para combinar las fuentes |
| `src/analisis/` | Código de análisis e indicadores |
| `docs/` | Documentación de arquitectura, fuentes y responsabilidades |
| `output/` | Conjuntos integrados y resultados generados |
| `requirements.txt` | Dependencias de Python declaradas por el equipo |
| `.gitignore` | Reglas de exclusión de archivos locales y temporales |
| `CONTRIBUTING.md` | Convenciones de colaboración, ramas, commits y PR |

Las carpetas de datos y salidas contienen marcadores de estructura; los paquetes de `src/` contienen inicialmente archivos `__init__.py`. Su existencia no implica que el procesamiento esté implementado. Se agregarán notebooks u otras carpetas cuando exista contenido que los justifique.

## Estado actual del desarrollo

Estado de referencia: contenido revisado de `dev` el **10 de noviembre de 2026**, con esta propuesta de actualización del README para la Actividad 10.

| Componente | Estado |
| --- | --- |
| Estructura inicial de directorios y paquetes | Disponible |
| Documentos de arquitectura, fuentes y roles | Disponibles; sujetos a revisión conforme avance la implementación |
| Convenciones de colaboración y dependencias | Disponibles |
| README e índice de documentación | Actualizados en esta propuesta |
| Guía práctica de optimización | Pendiente de crear: `docs/guia_optimizacion.md` |
| Notebooks y módulos funcionales del pipeline | Pendientes de incorporar a esta rama |
| Ejecución integral, validaciones y evidencias de rendimiento | Pendientes |

La Actividad 10 se concentra en organización, documentación y trazabilidad. Las optimizaciones y comparaciones de rendimiento se incorporarán conforme se implemente el pipeline.

## Documentación

- [Arquitectura del pipeline](docs/arquitectura.md)
- [Fuentes de datos y criterios de integración](docs/fuentes.md)
- [Roles y responsabilidades del equipo](docs/roles.md)
- [Guía de contribución](CONTRIBUTING.md)
- [Dependencias del proyecto](requirements.txt)

La guía de optimización se añadirá a este índice cuando exista, para mantener funcionales los enlaces.

## Preparación del entorno y acceso a los datos

El diseño utiliza Python, PySpark y Parquet. Las versiones de las dependencias están declaradas en [requirements.txt](requirements.txt); la preparación del entorno se describe en la [Guía de contribución](CONTRIBUTING.md).

Los datos deben obtenerse de los portales oficiales indicados en [Fuentes de datos](docs/fuentes.md). Antes de ejecutar el pipeline, cada responsable deberá completar las instrucciones de descarga con la selección de archivos, el período utilizado y la ruta local esperada.

No se deben subir credenciales, información sensible, datos pesados ni salidas temporales. Antes de incorporar datos o ejecutar el procesamiento, se deben completar y comprobar las reglas de `.gitignore` para las carpetas de datos y resultados del proyecto.

## Equipo y seguimiento de cambios

| Integrante | Rol principal | Rol secundario |
| --- | --- | --- |
| Raúl Cordero Villalobos | Developer | Documentation Lead |
| Sergio Delgadillo Domínguez | Technical Reviewer | Developer |
| Juan Manuel Seimandi Gollaz | Documentation Lead | Technical Reviewer |

La distribución de fuentes y las responsabilidades se detallan en [Roles del equipo](docs/roles.md).

Las convenciones de ramas y commits, la preparación de Pull Requests y el proceso de revisión se consultan en la [Guía de contribución](CONTRIBUTING.md).
