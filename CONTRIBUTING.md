# Guía de Contribución

Este documento describe el flujo de trabajo de Git y las convenciones del proyecto `mexico-economic-pipeline`.

---

## Ramas

| Rama | Propósito |
|------|-----------|
| `main` | Versión estable. **Nunca push directo.** |
| `feature/<nombre>` | Nueva funcionalidad o notebook |
| `fix/<nombre>` | Corrección de bugs |
| `docs/<nombre>` | Solo documentación |
| `data/<nombre>` | Scripts de descarga o ETL auxiliar |

**Ejemplo de nombres de rama:**
```
feature/ingesta-enoe
feature/transformacion-inpc
fix/encoding-bom-2017
docs/actualizar-fuentes
```

Crear la rama siempre desde `main` actualizado:

```bash
git checkout main
git pull origin main
git checkout -b feature/mi-funcionalidad
```

---

## Commits — Conventional Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<alcance>): <descripción corta en imperativo>
```

### Tipos permitidos

| Tipo | Cuándo usarlo |
|------|--------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de error |
| `docs` | Solo documentación |
| `style` | Formato, sin cambio lógico |
| `refactor` | Refactorización sin feat ni fix |
| `test` | Agregar o corregir tests |
| `chore` | Tareas de mantenimiento (deps, CI) |
| `data` | Cambios en scripts de datos o esquemas |

### Alcances sugeridos

`enoe`, `igae`, `inpc`, `shcp`, `integracion`, `spark`, `docs`, `ci`

### Ejemplos válidos

```
feat(enoe): agregar ingesta de períodos 2023-2026
fix(enoe): eliminar BOM en columnas 2017
docs(fuentes): actualizar URL de descarga SHCP
refactor(spark): extraer función fix_df a módulo src/ingesta
data(enoe): corregir llave compuesta en join COE1-SDEM
chore: actualizar pyspark a 3.5.3
```

---

## Pull Requests

1. **Antes de abrir el PR**, asegúrate de que:
   - El notebook corre de principio a fin sin errores
   - Los notebooks tienen celdas Markdown explicando cada bloque de código
   - Has hecho `git pull origin main` y resuelto cualquier conflicto

2. **Título del PR:** usar el mismo formato de Conventional Commits

3. **Descripción mínima del PR:**
   ```
   ## Qué hace este PR
   - Agrega ingesta de los 85 ZIPs de ENOE
   - Genera Parquet por período en data/raw/enoe/

   ## Cómo probarlo
   1. Descargar al menos 3 ZIPs en data/raw/enoe/zips/
   2. Ejecutar notebook 01_ingesta_enoe.ipynb completo
   3. Verificar que data/raw/enoe/parquet/ tiene archivos generados

   ## Checklist
   - [ ] El notebook corre sin errores
   - [ ] No se versiona data/ ni output/
   - [ ] Los outputs de las celdas están limpios (jupyter nbconvert --clear-output)
   ```

4. **Revisión:** mínimo 1 aprobación del Technical Reviewer antes de merge.

5. **Merge strategy:** usar **Squash and merge** para mantener `main` limpio.

---

## Limpiar outputs de notebooks antes de commit

Los notebooks no deben llevar resultados de ejecución versionados (evita diffs enormes):

```bash
# Limpiar un notebook específico
jupyter nbconvert --clear-output --inplace notebooks/01_ingesta_enoe.ipynb

# Limpiar todos
jupyter nbconvert --clear-output --inplace notebooks/*.ipynb
```

O instalar el hook automático:

```bash
pip install nbstripout
nbstripout --install
```

---

## Configuración inicial del entorno

```bash
# 1. Clonar el repositorio
git clone https://github.com/<org>/mexico-economic-pipeline.git
cd mexico-economic-pipeline

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar que Spark funciona
python -c "from pyspark.sql import SparkSession; print(SparkSession.builder.getOrCreate().version)"
```

---

## Issues

- Usar las etiquetas: `bug`, `enhancement`, `data-quality`, `documentation`, `question`
- Antes de abrir un issue, buscar si ya existe uno similar
- Para bugs de datos: incluir el período (año-trimestre) y el número de filas afectadas
