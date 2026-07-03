"""Logica de negocio para el perfil longitudinal."""

from __future__ import annotations

import math
from collections.abc import Sequence

from .models import PerfilPunto, PerfilTramo, PuntoInterseccion, Tramo


def construir_perfil_longitudinal(
    puntos_interseccion: Sequence[PuntoInterseccion],
    tramos: Sequence[Tramo],
    cotas_terreno: Sequence[float],
) -> tuple[list[PerfilPunto], list[PerfilTramo]]:
    """Construye el perfil longitudinal a partir de cotas de terreno por PI."""
    if len(puntos_interseccion) != len(cotas_terreno):
        raise ValueError(
            "La cantidad de cotas de terreno debe coincidir con la cantidad de PI."
        )
    if len(tramos) != max(0, len(puntos_interseccion) - 1):
        raise ValueError(
            "La cantidad de tramos debe coincidir con la geometria del alineamiento."
        )

    perfil_puntos = [
        PerfilPunto(
            numero_pi=punto.numero,
            progresiva=punto.progresiva,
            cota_terreno=cota,
        )
        for punto, cota in zip(puntos_interseccion, cotas_terreno, strict=True)
    ]

    perfil_tramos: list[PerfilTramo] = []
    for tramo in tramos:
        cota_inicial = cotas_terreno[tramo.pi_inicial - 1]
        cota_final = cotas_terreno[tramo.pi_final - 1]
        delta_z = cota_final - cota_inicial
        longitud_horizontal = tramo.longitud_horizontal
        longitud_inclinada = math.hypot(longitud_horizontal, delta_z)
        pendiente_porcentaje = calcular_pendiente_porcentaje(
            delta_z, longitud_horizontal
        )
        perfil_tramos.append(
            PerfilTramo(
                numero_tramo=tramo.numero,
                pi_inicial=tramo.pi_inicial,
                pi_final=tramo.pi_final,
                longitud_horizontal=longitud_horizontal,
                delta_z=delta_z,
                longitud_inclinada=longitud_inclinada,
                pendiente_porcentaje=pendiente_porcentaje,
            )
        )

    return perfil_puntos, perfil_tramos


def calcular_pendiente_porcentaje(delta_z: float, longitud_horizontal: float) -> float:
    """Calcula la pendiente del tramo expresada en porcentaje."""
    if math.isclose(longitud_horizontal, 0.0, abs_tol=1e-9):
        raise ValueError("La longitud horizontal del tramo no puede ser cero.")
    return (delta_z / longitud_horizontal) * 100.0
