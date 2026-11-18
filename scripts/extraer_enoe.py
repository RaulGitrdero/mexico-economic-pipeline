#!/usr/bin/env python3
"""
extraer_enoe.py
Extrae de los ZIP de la ENOE (descarga masiva de INEGI) solo los CSV que usa el ETL:
el conjunto de datos principal de COE1 y SDEM (y opcionalmente sus catálogos).

Conserva la estructura interna del ZIP dentro de una carpeta por periodo:
    <salida>/<AAAA>_<T>/conjunto_de_datos_sdem_enoe_<AAAA>_<T>t/conjunto_de_datos/....csv

Uso:
    python extraer_enoe.py <carpeta_con_zips> <carpeta_salida>
    python extraer_enoe.py DescargaMasiva_16112026_184443 data\\enoe\\raw
    python extraer_enoe.py zips data\\enoe\\raw --tablas coe1 sdem --catalogos
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

PATRONES = [
    re.compile(r"(?<!\d)(\d{4})_(\d)t_csv", re.I),  # ..._enoe_2005_1t_csv, ..._enoe2018_2t_csv, enoen
    re.compile(r"_(\d{4})_trim(\d)_", re.I),       # 2017-T1..T4 y 2018-T1: NN_2017_trim1_enoe_csv
]


def periodo(nombre: str):
    for p in PATRONES:
        if m := p.search(nombre):
            return int(m.group(1)), int(m.group(2))
    return None


def es_principal(miembro: str) -> bool:
    """CSV principal: está en /conjunto_de_datos/ y su nombre empieza con 'conjunto_de_datos_'.
    Excluye archivos auxiliares como '<tabla>_enoe_2017_1t_bitacora_de_cambios.csv'."""
    n = miembro.replace("\\", "/").lower()
    return "/conjunto_de_datos/" in n and n.rsplit("/", 1)[-1].startswith("conjunto_de_datos_")


def elegir(miembro: str, tablas: list[str], catalogos: bool, bitacoras: bool) -> bool:
    n = miembro.replace("\\", "/").lower()
    if not n.endswith(".csv"):
        return False
    if not any(f"_{t}_" in n for t in tablas):
        return False
    if es_principal(n):
        return True
    if bitacoras and "/conjunto_de_datos/" in n and "bitacora" in n:
        return True
    return catalogos and "/catalogos/" in n


def main() -> int:
    # Salida en UTF-8 aunque se redirija a un archivo (en Windows el default es cp1252)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Extrae COE1/SDEM de los ZIP de la ENOE.")
    ap.add_argument("zips", help="Carpeta con los ZIP descargados de INEGI")
    ap.add_argument("salida", help="Carpeta destino (ej. data/enoe/raw)")
    ap.add_argument("--tablas", nargs="+", default=["coe1", "sdem"],
                    help="Tablas a extraer (default: coe1 sdem)")
    ap.add_argument("--catalogos", action="store_true", help="Extraer también los catálogos")
    ap.add_argument("--bitacoras", action="store_true",
                    help="Extraer también las bitácoras de cambios (no son datos)")
    args = ap.parse_args()

    origen, salida = Path(args.zips), Path(args.salida)
    zips = sorted(origen.glob("*.zip"), key=lambda z: periodo(z.name) or (9999, 9))
    if not zips:
        print(f"No se encontraron ZIP en {origen}")
        return 1

    ok, errores, periodos = 0, 0, []
    for z in zips:
        per = periodo(z.name)
        if per is None:
            print(f"[OMITIDO] {z.name}: no se reconoce año/trimestre en el nombre")
            continue
        destino = salida / f"{per[0]}_{per[1]}"
        try:
            with zipfile.ZipFile(z) as zf:
                miembros = [m for m in zf.namelist() if elegir(m, args.tablas, args.catalogos, args.bitacoras)]
                encontradas = {t for t in args.tablas
                               if any(f"_{t}_" in m.lower() and es_principal(m) for m in miembros)}
                for m in miembros:
                    zf.extract(m, destino)
            faltan = set(args.tablas) - encontradas
            estado = f"  [AVISO] no se encontró: {', '.join(sorted(faltan))}" if faltan else ""
            print(f"[OK]  {per[0]}-T{per[1]}  {len(miembros):>3} archivo(s)  <- {z.name}{estado}")
            ok += 1
            periodos.append(per)
        except (zipfile.BadZipFile, OSError) as e:
            print(f"[ERROR] {z.name}: {e}", file=sys.stderr)
            errores += 1

    # Detectar trimestres faltantes en la serie (ej. 2020-T2)
    if periodos:
        a0, a1 = min(periodos)[0], max(periodos)[0]
        esperados = {(a, t) for a in range(a0, a1 + 1) for t in range(1, 5)}
        esperados = {p for p in esperados if min(periodos) <= p <= max(periodos)}
        faltantes = sorted(esperados - set(periodos))
        if faltantes:
            print("\nTrimestres faltantes en la serie: " + ", ".join(f"{a}-T{t}" for a, t in faltantes))

    print(f"\nResumen: {ok} ZIP extraídos, {errores} errores. Salida: {salida.resolve()}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
