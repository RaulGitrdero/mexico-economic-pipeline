# Roles y Responsabilidades del Equipo

**Proyecto:** Mexico Economic Pipeline  
**Materia:** Procesamiento de Grandes Bases de Datos  
**Institución:** CUCEA · Universidad de Guadalajara  
**Período:** Agosto–Diciembre 2026

---

## Integrantes y roles

| Integrante | Rol principal | Rol secundario |
|------------|--------------|---------------|
| Cordero Villalobos, Raúl | Developer | Documentation Lead |
| [Nombre 2] | Technical Reviewer | Developer |
| [Nombre 3] | Documentation Lead | Technical Reviewer |

> Actualizar nombres según confirmación del equipo.

---

## Descripción de roles

### 🧑‍💻 Developer

Responsable de escribir, probar y entregar el código funcional del pipeline.

**Responsabilidades:**
- Implementar los notebooks de ingesta, transformación e integración
- Escribir las funciones reutilizables en `src/`
- Asegurarse de que el código corre sin errores en el ambiente del equipo
- Crear Pull Requests con el código desarrollado
- Documentar con docstrings las funciones del módulo `src/`

**Entregables:**
- Notebooks `01_ingesta_*.ipynb` a `07_integracion.ipynb`
- Módulos `src/ingesta/*.py` y `src/transformacion/*.py`

---

### 🔍 Technical Reviewer

Responsable de revisar la calidad técnica del código y los datos antes de que se integren a `main`.

**Responsabilidades:**
- Revisar todos los Pull Requests antes de aprobarlos (mínimo 1 reviewer por PR)
- Verificar que los outputs del pipeline son correctos (conteos, rangos de valores, nulos)
- Correr los notebooks del reviewer en su propia máquina para validar reproducibilidad
- Detectar y reportar Issues de calidad de datos o de código
- Proponer mejoras de rendimiento en las transformaciones Spark

**Entregables:**
- Revisiones y comentarios en PRs (con aprobación o solicitud de cambios)
- Notebook `05_validacion.ipynb`
- Issues documentados en GitHub con etiqueta `bug` o `data-quality`

---

### 📝 Documentation Lead

Responsable de que el repositorio esté bien documentado y sea comprensible para cualquier lector externo.

**Responsabilidades:**
- Mantener actualizado el `README.md`
- Redactar y actualizar `docs/fuentes.md`, `docs/arquitectura.md` y `docs/roles.md`
- Revisar que los notebooks tengan celdas Markdown explicativas entre el código
- Crear y mantener el diagrama `docs/arquitectura.png`
- Coordinar que los commits tengan mensajes descriptivos (ver `CONTRIBUTING.md`)

**Entregables:**
- `docs/fuentes.md` completo con todas las fuentes
- `docs/arquitectura.png` y `docs/arquitectura.md`
- Revisión final de README antes de entrega

---

## Flujo de trabajo del equipo

```
feature branch  →  Pull Request  →  Code Review  →  merge a main
   (Developer)       (Developer)    (Tech Reviewer)   (tras aprobación)
```

1. Cada funcionalidad se desarrolla en una **rama dedicada** (nunca directo en `main`)
2. Al terminar, se abre un **Pull Request** con descripción de los cambios
3. El **Technical Reviewer** revisa el PR; puede pedir cambios antes de aprobar
4. Solo tras aprobación se hace merge a `main`
5. El **Documentation Lead** actualiza los docs si el cambio lo requiere

Ver `CONTRIBUTING.md` para las convenciones de ramas y commits.

---

## Distribución de fuentes por integrante

| Fuente | Responsable de ingesta | Responsable de revisión |
|--------|----------------------|------------------------|
| ENOE | Cordero Villalobos, Raúl | [Nombre 2] |
| IGAE | [Nombre 2] | [Nombre 3] |
| INPC | [Nombre 3] | Cordero Villalobos, Raúl |
| SHCP Deuda | Cordero Villalobos, Raúl | [Nombre 2] |
| Integración | Equipo completo | Todos |

> Ajustar distribución según acuerdo del equipo.
