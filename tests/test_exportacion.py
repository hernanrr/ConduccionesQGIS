"""Pruebas unitarias para el nucleo reusable de exportacion."""

from __future__ import annotations

import csv

import pytest
from ConduccionesQGIS.core.exportacion import (
    construir_ruta_exportacion,
    crear_tabla_exportable,
    exportar_tabla_csv,
    exportar_tablas_csv,
    validar_nombre_base,
)


def test_crear_tabla_exportable_preserva_columnas_y_filas() -> None:
    """Construye una tabla exportable estable a partir de secuencias simples."""
    tabla = crear_tabla_exportable(
        "puntos_interseccion",
        ["PI", "Progresiva"],
        [(1, 0.0), (2, 125.5)],
    )

    assert tabla.nombre == "puntos_interseccion"
    assert tabla.columnas == ("PI", "Progresiva")
    assert tabla.filas == ((1, 0.0), (2, 125.5))


def test_validar_nombre_base_rechaza_vacio() -> None:
    """Exige que el nombre base manual tenga contenido."""
    with pytest.raises(ValueError, match="obligatorio"):
        validar_nombre_base("   ")


def test_validar_nombre_base_rechaza_caracteres_invalidos() -> None:
    """Bloquea caracteres no validos para nombres de archivo en Windows."""
    with pytest.raises(ValueError, match="no permitidos"):
        validar_nombre_base("alineamiento:demo")


def test_construir_ruta_exportacion_anexa_nombre_y_extension(tmp_path) -> None:
    """Deriva la ruta final desde directorio, base, tabla y extension."""
    ruta = construir_ruta_exportacion(
        tmp_path,
        "alineamiento_demo",
        "puntos_interseccion",
        "csv",
    )

    assert ruta.name == "alineamiento_demo_puntos_interseccion.csv"
    assert ruta.parent == tmp_path


def test_exportar_tabla_csv_genera_encabezados_y_filas(tmp_path) -> None:
    """Exporta una tabla individual a CSV con encabezado y contenido."""
    tabla = crear_tabla_exportable(
        "puntos_interseccion",
        ["PI", "Progresiva", "Giro"],
        [(1, 0.0, "Inicio"), (2, 125.5, "Derecha")],
    )

    ruta = exportar_tabla_csv(tabla, tmp_path, "alineamiento_demo")

    assert ruta.exists()
    with ruta.open("r", encoding="utf-8-sig", newline="") as descriptor:
        filas = list(csv.reader(descriptor))

    assert filas == [
        ["PI", "Progresiva", "Giro"],
        ["1", "0.0", "Inicio"],
        ["2", "125.5", "Derecha"],
    ]


def test_exportar_tablas_csv_genera_un_archivo_por_tabla(tmp_path) -> None:
    """Exporta varias tablas a CSV separados por nombre logico."""
    puntos = crear_tabla_exportable("puntos_interseccion", ["PI"], [(1,), (2,)])
    tramos = crear_tabla_exportable("tramos", ["Tramo"], [(1,), (2,)])

    rutas = exportar_tablas_csv([puntos, tramos], tmp_path, "alineamiento_demo")

    assert set(rutas) == {"puntos_interseccion", "tramos"}
    assert rutas["puntos_interseccion"].name.endswith("_puntos_interseccion.csv")
    assert rutas["tramos"].name.endswith("_tramos.csv")
