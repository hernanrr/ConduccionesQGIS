"""Modelos de dominio del proyecto."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Giro(StrEnum):
    """Sentido del cambio de direccion en un PI."""

    INICIO = "Inicio"
    IZQUIERDA = "Izquierda"
    DERECHA = "Derecha"
    RECTO = "Recto"
    FINAL = "Final"


@dataclass(frozen=True, slots=True)
class Punto2D:
    """Representa un punto plano."""

    x: float
    y: float


@dataclass(frozen=True, slots=True)
class PuntoInterseccion:
    """Representa un punto de interseccion del alineamiento."""

    numero: int
    progresiva: float
    punto: Punto2D
    longitud_tramo: float | None
    azimut: float | None
    deflexion: float | None
    giro: Giro
    codo_recomendado: float | None


@dataclass(frozen=True, slots=True)
class Tramo:
    """Representa un tramo recto entre dos PI consecutivos."""

    numero: int
    pi_inicial: int
    pi_final: int
    longitud_horizontal: float
    longitud_inclinada: float | None
    pendiente: float | None
    azimut: float


@dataclass(frozen=True, slots=True)
class PerfilPunto:
    """Representa la informacion de terreno en un PI."""

    numero_pi: int
    progresiva: float
    cota_terreno: float


@dataclass(frozen=True, slots=True)
class PerfilTramo:
    """Representa los calculos topograficos de un tramo del perfil."""

    numero_tramo: int
    pi_inicial: int
    pi_final: int
    longitud_horizontal: float
    delta_z: float
    longitud_inclinada: float
    pendiente_porcentaje: float
