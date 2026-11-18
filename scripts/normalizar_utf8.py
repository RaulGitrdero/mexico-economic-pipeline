#!/usr/bin/env python3
"""
normalizar_utf8.py
Convierte archivos CSV a codificación UTF-8 (sin BOM).

Pensado para los CSV de INEGI / SHCP, que suelen venir en Windows-1252 (cp1252)
o Latin-1, y por eso muestran caracteres como "Ã±" o "�" en lugar de "ñ" o "é".

Uso:
    python normalizar_utf8.py archivo.csv
    python normalizar_utf8.py archivo1.csv archivo2.csv
    python normalizar_utf8.py data/bronze/enoe/            (todos los .csv de la carpeta, recursivo)
    python normalizar_utf8.py archivo.csv --outdir data/utf8
    python normalizar_utf8.py archivo.csv --no-backup --lf

Por defecto el archivo se sobrescribe con la versión UTF-8 y se guarda
una copia del original como "archivo.csv.bak".
"""

import argparse
import codecs
import os
import shutil
import sys
import tempfile
from pathlib import Path

CHUNK = 1024 * 1024  # 1 MB: permite procesar archivos de varios GB sin cargarlos en memoria
BOM = codecs.BOM_UTF8
# Patrones típicos de texto UTF-8 leído por error como cp1252 y vuelto a guardar ("doble codificación")
MOJIBAKE = ("Ã¡", "Ã©", "Ã­", "Ã³", "Ãº", "Ã±", "Ã‘", "Ã“", "Ã‰", "Ã¼", "Â°", "Â¿")


def es_utf8_valido(ruta: Path) -> bool:
    """Lee el archivo por bloques y verifica que todo sea UTF-8 válido."""
    dec = codecs.getincrementaldecoder("utf-8")(errors="strict")
    try:
        with open(ruta, "rb") as f:
            while bloque := f.read(CHUNK):
                dec.decode(bloque)
            dec.decode(b"", final=True)
        return True
    except UnicodeDecodeError:
        return False


def tiene_bom(ruta: Path) -> bool:
    with open(ruta, "rb") as f:
        return f.read(3) == BOM


def contar_mojibake(ruta: Path) -> int:
    with open(ruta, "r", encoding="utf-8-sig", newline="") as f:
        return sum(sum(b.count(p) for p in MOJIBAKE) for b in iter(lambda: f.read(CHUNK), ""))


def detectar_encoding(ruta: Path, forzado: str | None) -> str:
    """Devuelve el encoding de origen más probable."""
    if forzado:
        return forzado
    if es_utf8_valido(ruta):
        return "utf-8-sig" if tiene_bom(ruta) else "utf-8"
    # cp1252 es un superconjunto práctico de Latin-1 para texto en español,
    # pero tiene 5 bytes sin definir; si aparece alguno, usamos latin-1.
    dec = codecs.getincrementaldecoder("cp1252")(errors="strict")
    try:
        with open(ruta, "rb") as f:
            while bloque := f.read(CHUNK):
                dec.decode(bloque)
        return "cp1252"
    except UnicodeDecodeError:
        return "latin-1"


def convertir(ruta: Path, destino: Path, origen: str, lf: bool) -> dict:
    """Convierte por bloques a UTF-8 sin BOM. Escribe primero a un temporal."""
    stats = {"mojibake": 0}
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=destino.parent, prefix=".tmp_", suffix=".csv")
    os.close(fd)
    try:
        # newline="" conserva los saltos de línea originales salvo que se pida --lf
        with open(ruta, "r", encoding=origen, errors="strict", newline="") as fin, \
             open(tmp, "w", encoding="utf-8", newline="") as fout:
            cola = ""
            while texto := fin.read(CHUNK):
                if lf:
                    texto = cola + texto
                    cola = "\r" if texto.endswith("\r") else ""  # un \r\n partido entre bloques
                    if cola:
                        texto = texto[:-1]
                    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
                texto = texto.lstrip("\ufeff") if fout.tell() == 0 else texto
                stats["mojibake"] += sum(texto.count(p) for p in MOJIBAKE)
                fout.write(texto)
            if cola:
                fout.write("\n")
        os.replace(tmp, destino)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise
    return stats


def recolectar(entradas: list[str]) -> list[Path]:
    archivos = []
    for e in entradas:
        p = Path(e)
        if p.is_dir():
            archivos += sorted(x for x in p.rglob("*") if x.suffix.lower() == ".csv")
        elif p.is_file():
            archivos.append(p)
        else:
            print(f"[AVISO] No existe: {e}", file=sys.stderr)
    return archivos


def main() -> int:
    # Salida en UTF-8 aunque se redirija a un archivo (en Windows el default es cp1252)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Normaliza archivos CSV a UTF-8 (sin BOM).")
    ap.add_argument("entradas", nargs="+", help="Archivos .csv o carpetas que los contengan")
    ap.add_argument("--outdir", help="Carpeta de salida (no modifica los originales)")
    ap.add_argument("--no-backup", action="store_true", help="No crear copia .bak al sobrescribir")
    ap.add_argument("--encoding", help="Forzar encoding de origen (ej. cp1252, latin-1)")
    ap.add_argument("--lf", action="store_true", help="Convertir saltos de línea a LF (\\n)")
    args = ap.parse_args()

    archivos = recolectar(args.entradas)
    if not archivos:
        print("No se encontraron archivos .csv")
        return 1

    resumen = {"convertidos": 0, "ya_utf8": 0, "errores": 0}
    for ruta in archivos:
        try:
            origen = detectar_encoding(ruta, args.encoding)

            if args.outdir:
                base = Path(args.entradas[0]) if Path(args.entradas[0]).is_dir() else ruta.parent
                rel = ruta.relative_to(base) if ruta.is_relative_to(base) else Path(ruta.name)
                destino = Path(args.outdir) / rel
            else:
                destino = ruta

            if origen == "utf-8" and not args.lf and not args.outdir:
                print(f"[OK]     {ruta}  ya está en UTF-8, sin cambios")
                if n := contar_mojibake(ruta):
                    print(f"         [AVISO] {n} posibles caracteres mal codificados (ej. 'Ã±'); revísalo.")
                resumen["ya_utf8"] += 1
                continue

            if destino == ruta and not args.no_backup:
                shutil.copy2(ruta, ruta.with_name(ruta.name + ".bak"))

            stats = convertir(ruta, destino, origen, args.lf)

            if not es_utf8_valido(destino):
                raise RuntimeError("la salida no es UTF-8 válido")

            print(f"[UTF-8]  {ruta}  ({origen} -> utf-8)" + (f"  -> {destino}" if destino != ruta else ""))
            if stats["mojibake"]:
                print(f"         [AVISO] {stats['mojibake']} posibles caracteres mal codificados "
                      f"(ej. 'Ã±'). El archivo original quizá ya venía dañado; revísalo.")
            resumen["convertidos"] += 1

        except Exception as e:
            print(f"[ERROR]  {ruta}: {e}", file=sys.stderr)
            resumen["errores"] += 1

    print(f"\nResumen: {resumen['convertidos']} convertidos, "
          f"{resumen['ya_utf8']} ya estaban en UTF-8, {resumen['errores']} errores.")
    return 1 if resumen["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())
