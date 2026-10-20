"""Ejecuta cada consulta de consultas.sql y muestra el resultado como tabla.

Uso:
    python sql/ejecutar_consultas.py                 # sobre los datos originales (BD en memoria)
    python sql/ejecutar_consultas.py api/data/suministros.db
"""

import re
import sqlite3
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent


def consultas(texto: str) -> list[tuple[str, str]]:
    """Separa el archivo en (título, sql) usando los encabezados '-- N. ...'."""
    bloques = re.split(r"\n(?=-- -+\n-- \d\.)", texto)
    salida = []
    for bloque in bloques:
        titulo = re.search(r"-- (\d\..*)", bloque)
        sql = "\n".join(l for l in bloque.splitlines() if not l.lstrip().startswith("--")).strip()
        if titulo and sql:
            salida.append((titulo.group(1).strip(), sql.split("-- ====")[0]))
    return salida


def tabla(cursor: sqlite3.Cursor) -> str:
    columnas = [d[0] for d in cursor.description]
    filas = [["" if v is None else str(v) for v in f] for f in cursor.fetchall()]
    anchos = [max(len(c), *(len(f[i]) for f in filas)) if filas else len(c) for i, c in enumerate(columnas)]
    linea = lambda valores: "| " + " | ".join(v.ljust(a) for v, a in zip(valores, anchos)) + " |"
    return "\n".join([linea(columnas), "|" + "|".join("-" * (a + 2) for a in anchos) + "|", *map(linea, filas),
                      f"({len(filas)} filas)"])


def main() -> None:
    if len(sys.argv) > 1:
        conn = sqlite3.connect(sys.argv[1])
    else:
        conn = sqlite3.connect(":memory:")
        conn.executescript((CARPETA / "datos_prueba.sql").read_text(encoding="utf-8"))
    for titulo, sql in consultas((CARPETA / "consultas.sql").read_text(encoding="utf-8")):
        print(f"\n### {titulo}\n")
        print(tabla(conn.execute(sql)))


if __name__ == "__main__":
    main()
