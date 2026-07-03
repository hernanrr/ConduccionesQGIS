"""Utilidades reutilizables para exportacion tabular."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TablaExportable:
    """Representa una tabla lista para persistirse a disco."""

    nombre: str
    columnas: tuple[str, ...]
    filas: tuple[tuple[object | None, ...], ...]

    def __post_init__(self) -> None:
        """Valida coherencia basica de la tabla exportable."""
        if not self.nombre.strip():
            raise ValueError("El nombre de la tabla exportable es obligatorio.")
        if not self.columnas:
            raise ValueError("La tabla exportable debe tener al menos una columna.")
        for fila in self.filas:
            if len(fila) != len(self.columnas):
                raise ValueError(
                    "Todas las filas de una tabla exportable deben coincidir con "
                    "la cantidad de columnas."
                )


def crear_tabla_exportable(
    nombre: str,
    columnas: Sequence[str],
    filas: Iterable[Sequence[object | None]],
) -> TablaExportable:
    """Crea una tabla exportable a partir de secuencias genericas."""
    return TablaExportable(
        nombre=nombre,
        columnas=tuple(columnas),
        filas=tuple(tuple(fila) for fila in filas),
    )


def validar_nombre_base(nombre_base: str) -> str:
    """Valida el nombre base obligatorio para exportaciones a archivo."""
    limpio = nombre_base.strip()
    if not limpio:
        raise ValueError("El nombre base de exportacion es obligatorio.")
    caracteres_invalidos = set('\\/:*?"<>|')
    if any(caracter in caracteres_invalidos for caracter in limpio):
        raise ValueError("El nombre base contiene caracteres no permitidos.")
    return limpio


def construir_ruta_exportacion(
    directorio: str | Path,
    nombre_base: str,
    nombre_tabla: str,
    extension: str,
) -> Path:
    """Construye la ruta completa de una exportacion tabular."""
    directorio_path = Path(directorio)
    directorio_path.mkdir(parents=True, exist_ok=True)
    base = validar_nombre_base(nombre_base)
    return directorio_path / f"{base}_{nombre_tabla}.{extension.lstrip('.')}"


def exportar_tabla_csv(
    tabla: TablaExportable,
    directorio: str | Path,
    nombre_base: str,
) -> Path:
    """Exporta una tabla individual a CSV."""
    ruta = construir_ruta_exportacion(directorio, nombre_base, tabla.nombre, "csv")
    with ruta.open("w", encoding="utf-8-sig", newline="") as descriptor:
        escritor = csv.writer(descriptor)
        escritor.writerow(tabla.columnas)
        escritor.writerows(tabla.filas)
    return ruta


def exportar_tablas_csv(
    tablas: Sequence[TablaExportable],
    directorio: str | Path,
    nombre_base: str,
) -> dict[str, Path]:
    """Exporta una coleccion de tablas a archivos CSV independientes."""
    return {
        tabla.nombre: exportar_tabla_csv(tabla, directorio, nombre_base)
        for tabla in tablas
    }
