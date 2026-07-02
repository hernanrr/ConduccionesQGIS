"""Pruebas unitarias para el nucleo de alineamiento."""

from __future__ import annotations

import math

import pytest
from ConduccionesQGIS.core.alineamiento import (
    CatalogoCodos,
    construir_tabla_alineamiento,
    formatear_progresiva,
)
from ConduccionesQGIS.core.models import Giro, Punto2D


def test_construir_tabla_alineamiento_simple() -> None:
    """Valida la salida base para un alineamiento sencillo de cinco vertices."""
    vertices = [
        Punto2D(0.0, 0.0),
        Punto2D(0.0, 100.0),
        Punto2D(100.0, 100.0),
        Punto2D(100.0, 200.0),
        Punto2D(200.0, 200.0),
    ]

    puntos, tramos = construir_tabla_alineamiento(vertices)

    assert len(puntos) == 5
    assert len(tramos) == 4
    assert puntos[0].giro is Giro.INICIO
    assert puntos[-1].giro is Giro.FINAL
    assert puntos[1].progresiva == pytest.approx(100.0)
    assert puntos[2].progresiva == pytest.approx(200.0)
    assert puntos[3].progresiva == pytest.approx(300.0)
    assert puntos[0].azimut == pytest.approx(0.0)
    assert puntos[1].azimut == pytest.approx(90.0)
    assert puntos[2].azimut == pytest.approx(0.0)
    assert puntos[3].azimut == pytest.approx(90.0)
    assert puntos[1].deflexion == pytest.approx(90.0)
    assert puntos[2].deflexion == pytest.approx(90.0)
    assert puntos[3].deflexion == pytest.approx(90.0)
    assert puntos[1].giro is Giro.DERECHA
    assert puntos[2].giro is Giro.IZQUIERDA
    assert puntos[3].giro is Giro.DERECHA
    assert puntos[1].codo_recomendado == pytest.approx(90.0)


def test_linea_casi_recta_devuelve_recto() -> None:
    """Clasifica como recto una deflexion muy pequena."""
    vertices = [
        Punto2D(0.0, 0.0),
        Punto2D(0.0, 100.0),
        Punto2D(0.0001, 200.0),
    ]

    puntos, _ = construir_tabla_alineamiento(vertices)

    assert puntos[1].deflexion is not None
    assert puntos[1].deflexion < 0.001
    assert puntos[1].giro is Giro.RECTO


def test_deflexion_se_mantiene_en_rango_y_no_es_angulo_interior() -> None:
    """Comprueba que la deflexion siga la convención 0° = recta."""
    vertices = [
        Punto2D(0.0, 0.0),
        Punto2D(0.0, 10.0),
        Punto2D(-5.0, 5.0),
    ]

    puntos, _ = construir_tabla_alineamiento(vertices)

    assert puntos[1].deflexion == pytest.approx(135.0)
    assert 0.0 <= puntos[1].deflexion <= 180.0
    assert not math.isclose(puntos[1].deflexion, 45.0)


def test_geometria_invalida_rechaza_menos_de_tres_vertices() -> None:
    """Rechaza alineamientos sin suficientes vertices para dos tramos."""
    with pytest.raises(ValueError, match="al menos tres vertices"):
        construir_tabla_alineamiento([Punto2D(0.0, 0.0), Punto2D(1.0, 1.0)])


def test_catalogo_configurable() -> None:
    """Recomienda el codo segun el catalogo suministrado por el usuario."""
    vertices = [
        Punto2D(0.0, 0.0),
        Punto2D(0.0, 10.0),
        Punto2D(7.0, 17.0),
    ]
    catalogo = CatalogoCodos((15.0, 30.0, 60.0))

    puntos, _ = construir_tabla_alineamiento(vertices, catalogo)

    assert puntos[1].deflexion == pytest.approx(45.0)
    assert puntos[1].codo_recomendado == pytest.approx(60.0)


def test_formatear_progresiva() -> None:
    """Formatea progresivas en notacion hito+metros."""
    assert formatear_progresiva(154.325) == "0+154.325"
    assert formatear_progresiva(1245.33) == "1+245.330"
