"""Utilidades geometricas puras para el alineamiento."""

from __future__ import annotations

import math
from collections.abc import Sequence

from .models import Giro, Punto2D

TOLERANCIA_ANGULAR = 1e-9


def distancia_horizontal(p1: Punto2D, p2: Punto2D) -> float:
    """Calcula la distancia horizontal entre dos puntos."""
    return math.hypot(p2.x - p1.x, p2.y - p1.y)


def azimut_grados(p1: Punto2D, p2: Punto2D) -> float:
    """Calcula el azimut en grados, medido desde el norte y en sentido horario."""
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    if math.isclose(dx, 0.0, abs_tol=TOLERANCIA_ANGULAR) and math.isclose(
        dy, 0.0, abs_tol=TOLERANCIA_ANGULAR
    ):
        raise ValueError("No se puede calcular el azimut de un tramo de longitud cero.")

    azimut = math.degrees(math.atan2(dx, dy))
    return azimut % 360.0


def delta_angular_firmado(azimut_1: float, azimut_2: float) -> float:
    """Calcula el cambio angular firmado entre dos azimuts consecutivos."""
    delta = (azimut_2 - azimut_1 + 180.0) % 360.0 - 180.0
    if math.isclose(delta, -180.0, abs_tol=TOLERANCIA_ANGULAR):
        return 180.0
    return delta


def deflexion_grados(azimut_1: float, azimut_2: float) -> float:
    """Calcula la deflexion con convención 0° = recta."""
    return abs(delta_angular_firmado(azimut_1, azimut_2))


def determinar_giro(azimut_1: float, azimut_2: float, tolerancia: float = 1e-3) -> Giro:
    """Determina el sentido del giro entre dos azimuts."""
    delta = delta_angular_firmado(azimut_1, azimut_2)
    if math.isclose(delta, 0.0, abs_tol=tolerancia):
        return Giro.RECTO
    if delta > 0.0:
        return Giro.DERECHA
    return Giro.IZQUIERDA


def validar_vertices(vertices: Sequence[Punto2D]) -> None:
    """Valida que el alineamiento tenga al menos dos tramos utiles."""
    if len(vertices) < 3:
        raise ValueError(
            "El alineamiento debe tener al menos tres vertices para formar dos tramos."
        )

    for indice in range(len(vertices) - 1):
        if math.isclose(
            distancia_horizontal(vertices[indice], vertices[indice + 1]),
            0.0,
            abs_tol=TOLERANCIA_ANGULAR,
        ):
            raise ValueError(
                "El alineamiento no puede contener tramos de longitud cero."
            )
