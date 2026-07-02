"""Logica de negocio para la tabla de alineamiento."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .geometria import (
    azimut_grados,
    deflexion_grados,
    determinar_giro,
    distancia_horizontal,
    validar_vertices,
)
from .models import Giro, Punto2D, PuntoInterseccion, Tramo

CATALOGO_CODOS_POR_DEFECTO = (11.25, 22.5, 45.0, 90.0)


@dataclass(frozen=True, slots=True)
class CatalogoCodos:
    """Define un catalogo de codos comerciales."""

    angulos: tuple[float, ...] = CATALOGO_CODOS_POR_DEFECTO

    def __post_init__(self) -> None:
        """Valida los valores del catalogo despues de construir la instancia."""
        if not self.angulos:
            raise ValueError("El catalogo de codos no puede estar vacio.")
        if any(angulo <= 0.0 for angulo in self.angulos):
            raise ValueError("Todos los codos del catalogo deben ser positivos.")

    def recomendar(self, deflexion: float | None) -> float | None:
        """Devuelve el codo mas cercano a la deflexion dada."""
        if deflexion is None:
            return None
        return min(self.angulos, key=lambda angulo: (abs(angulo - deflexion), -angulo))


def construir_tabla_alineamiento(
    vertices: Sequence[Punto2D],
    catalogo: CatalogoCodos | None = None,
) -> tuple[list[PuntoInterseccion], list[Tramo]]:
    """Construye la tabla de PI y tramos a partir de los vertices."""
    validar_vertices(vertices)
    catalogo = catalogo or CatalogoCodos()

    azimuts: list[float] = []
    longitudes: list[float] = []
    tramos: list[Tramo] = []

    for indice in range(len(vertices) - 1):
        inicio = vertices[indice]
        fin = vertices[indice + 1]
        longitud = distancia_horizontal(inicio, fin)
        azimut = azimut_grados(inicio, fin)
        longitudes.append(longitud)
        azimuts.append(azimut)
        tramos.append(
            Tramo(
                numero=indice + 1,
                pi_inicial=indice + 1,
                pi_final=indice + 2,
                longitud_horizontal=longitud,
                longitud_inclinada=None,
                pendiente=None,
                azimut=azimut,
            )
        )

    puntos: list[PuntoInterseccion] = []
    progresiva = 0.0
    for indice, punto in enumerate(vertices):
        numero_pi = indice + 1
        longitud_tramo = longitudes[indice] if indice < len(longitudes) else None
        azimut = azimuts[indice] if indice < len(azimuts) else None

        if indice == 0:
            giro = Giro.INICIO
            deflexion = None
        elif indice == len(vertices) - 1:
            giro = Giro.FINAL
            deflexion = None
            azimut = None
            longitud_tramo = None
        else:
            deflexion = deflexion_grados(azimuts[indice - 1], azimuts[indice])
            giro = determinar_giro(azimuts[indice - 1], azimuts[indice])

        puntos.append(
            PuntoInterseccion(
                numero=numero_pi,
                progresiva=progresiva,
                punto=punto,
                longitud_tramo=longitud_tramo,
                azimut=azimut,
                deflexion=deflexion,
                giro=giro,
                codo_recomendado=catalogo.recomendar(deflexion),
            )
        )

        if indice < len(longitudes):
            progresiva += longitudes[indice]

    return puntos, tramos


def formatear_progresiva(
    progresiva: float,
    *,
    precision: int = 3,
    metros_por_hito: int = 1000,
) -> str:
    """Formatea una progresiva en formato hito+metros."""
    if metros_por_hito <= 0:
        raise ValueError("metros_por_hito debe ser mayor que cero.")

    hito = int(progresiva // metros_por_hito)
    metros = progresiva - (hito * metros_por_hito)
    ancho = len(str(metros_por_hito - 1))
    return f"{hito}+{metros:0{ancho + precision + 1}.{precision}f}"


def parsear_catalogo_codos(valores: Iterable[float | str]) -> CatalogoCodos:
    """Crea un catalogo a partir de una secuencia numerica o textual."""
    angulos: list[float] = []
    for valor in valores:
        if isinstance(valor, str):
            limpio = valor.strip()
            if not limpio:
                continue
            angulos.append(float(limpio))
        else:
            angulos.append(float(valor))
    return CatalogoCodos(tuple(angulos))
