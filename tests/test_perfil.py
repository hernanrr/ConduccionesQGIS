"""Pruebas unitarias para el nucleo del perfil longitudinal."""

from __future__ import annotations

import math

import pytest
from ConduccionesQGIS.core.alineamiento import construir_tabla_alineamiento
from ConduccionesQGIS.core.models import Punto2D
from ConduccionesQGIS.core.perfil import (
    calcular_pendiente_porcentaje,
    construir_perfil_longitudinal,
)


def test_construir_perfil_longitudinal_calcula_puntos_y_tramos() -> None:
    """Construye perfil por PI y tramo a partir de cotas de terreno."""
    vertices = [
        Punto2D(0.0, 0.0),
        Punto2D(0.0, 100.0),
        Punto2D(100.0, 100.0),
    ]
    puntos, tramos = construir_tabla_alineamiento(vertices)

    perfil_puntos, perfil_tramos = construir_perfil_longitudinal(
        puntos,
        tramos,
        [10.0, 12.0, 9.0],
    )

    assert len(perfil_puntos) == 3
    assert len(perfil_tramos) == 2
    assert perfil_puntos[1].numero_pi == 2
    assert perfil_puntos[1].progresiva == pytest.approx(100.0)
    assert perfil_puntos[1].cota_terreno == pytest.approx(12.0)

    assert perfil_tramos[0].delta_z == pytest.approx(2.0)
    assert perfil_tramos[0].longitud_horizontal == pytest.approx(100.0)
    assert perfil_tramos[0].longitud_inclinada == pytest.approx(math.hypot(100.0, 2.0))
    assert perfil_tramos[0].pendiente_porcentaje == pytest.approx(2.0)

    assert perfil_tramos[1].delta_z == pytest.approx(-3.0)
    assert perfil_tramos[1].pendiente_porcentaje == pytest.approx(-3.0)


def test_construir_perfil_longitudinal_rechaza_cotas_incompletas() -> None:
    """Exige una cota de terreno por cada PI."""
    vertices = [
        Punto2D(0.0, 0.0),
        Punto2D(0.0, 100.0),
        Punto2D(100.0, 100.0),
    ]
    puntos, tramos = construir_tabla_alineamiento(vertices)

    with pytest.raises(ValueError, match="cantidad de cotas"):
        construir_perfil_longitudinal(puntos, tramos, [10.0, 12.0])


def test_calcular_pendiente_porcentaje_rechaza_longitud_cero() -> None:
    """Evita divisiones invalidas en pendientes."""
    with pytest.raises(ValueError, match="no puede ser cero"):
        calcular_pendiente_porcentaje(1.0, 0.0)
