"""Pruebas unitarias para el nucleo reusable de exportacion."""

from __future__ import annotations

import csv

import pytest
from ConduccionesQGIS.core.alineamiento import construir_tabla_alineamiento
from ConduccionesQGIS.core.exportacion import (
    COLUMNAS_PUNTOS_INTERSECCION,
    COLUMNAS_TRAMOS,
    NOMBRE_TABLA_PUNTOS_INTERSECCION,
    NOMBRE_TABLA_TRAMOS,
    construir_ruta_exportacion,
    crear_tabla_exportable,
    exportar_tabla_csv,
    exportar_tablas_csv,
    serializar_tablas_alineamiento,
    validar_nombre_base,
)
from ConduccionesQGIS.core.models import Punto2D


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


def test_serializar_tablas_alineamiento_expone_contrato_estable() -> None:
    """Serializa puntos y tramos con nombres y columnas fijos para v0.2."""
    vertices = [
        Punto2D(0.0, 0.0),
        Punto2D(0.0, 100.0),
        Punto2D(100.0, 100.0),
        Punto2D(100.0, 200.0),
    ]
    puntos, tramos = construir_tabla_alineamiento(vertices)

    tabla_puntos, tabla_tramos = serializar_tablas_alineamiento(puntos, tramos)

    assert tabla_puntos.nombre == NOMBRE_TABLA_PUNTOS_INTERSECCION
    assert tabla_puntos.columnas == COLUMNAS_PUNTOS_INTERSECCION
    assert len(tabla_puntos.filas) == len(puntos)

    assert tabla_tramos.nombre == NOMBRE_TABLA_TRAMOS
    assert tabla_tramos.columnas == COLUMNAS_TRAMOS
    assert len(tabla_tramos.filas) == len(tramos)


def test_serializar_tablas_alineamiento_mantiene_coherencia_entre_pi_y_tramos() -> None:
    """Mantiene coherencia entre progresivas, tramos y referencias de PI."""
    vertices = [
        Punto2D(0.0, 0.0),
        Punto2D(0.0, 100.0),
        Punto2D(100.0, 100.0),
        Punto2D(100.0, 200.0),
    ]
    puntos, tramos = construir_tabla_alineamiento(vertices)

    tabla_puntos, tabla_tramos = serializar_tablas_alineamiento(puntos, tramos)

    primera_fila_tramo = tabla_tramos.filas[0]
    segunda_fila_punto = tabla_puntos.filas[1]

    assert primera_fila_tramo[1] == 1
    assert primera_fila_tramo[2] == 2
    assert primera_fila_tramo[3] == pytest.approx(100.0)
    assert segunda_fila_punto[1] == pytest.approx(100.0)
