"""Utilidades reutilizables para exportacion tabular."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .models import PerfilPunto, PerfilTramo, PuntoInterseccion, Tramo

NOMBRE_TABLA_PUNTOS_INTERSECCION = "puntos_interseccion"
NOMBRE_TABLA_TRAMOS = "tramos"
NOMBRE_TABLA_PERFIL_PUNTOS = "perfil_puntos"
NOMBRE_TABLA_PERFIL_TRAMOS = "perfil_tramos"
FORMATO_CSV = "csv"
FORMATO_XLSX = "xlsx"
FORMATOS_EXPORTACION = (FORMATO_CSV, FORMATO_XLSX)

COLUMNAS_PUNTOS_INTERSECCION = (
    "PI",
    "Progresiva",
    "X",
    "Y",
    "Longitud_tramo",
    "Azimut",
    "Deflexión",
    "Giro",
    "Codo_recomendado",
)

COLUMNAS_TRAMOS = (
    "Tramo",
    "PI_inicial",
    "PI_final",
    "Longitud_horizontal",
    "Longitud_inclinada",
    "Pendiente",
    "Azimut",
)

COLUMNAS_PERFIL_PUNTOS = (
    "PI",
    "Progresiva",
    "Cota_terreno",
)

COLUMNAS_PERFIL_TRAMOS = (
    "Tramo",
    "PI_inicial",
    "PI_final",
    "Longitud_horizontal",
    "Delta_Z",
    "Longitud_inclinada",
    "Pendiente",
)


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


@dataclass(frozen=True, slots=True)
class ResultadoExportacionArchivos:
    """Representa los archivos creados durante una exportacion."""

    csv: dict[str, Path]
    xlsx: Path | None


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


def construir_ruta_xlsx(directorio: str | Path, nombre_base: str) -> Path:
    """Construye la ruta final del libro XLSX agregado."""
    directorio_path = Path(directorio)
    directorio_path.mkdir(parents=True, exist_ok=True)
    base = validar_nombre_base(nombre_base)
    return directorio_path / f"{base}.xlsx"


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


def exportar_tablas_xlsx(
    tablas: Sequence[TablaExportable],
    directorio: str | Path,
    nombre_base: str,
) -> Path:
    """Exporta varias tablas en un libro XLSX con una hoja por tabla."""
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover - depende del runtime
        raise RuntimeError(
            "No se pudo exportar a XLSX porque openpyxl no esta instalado."
        ) from exc

    ruta = construir_ruta_xlsx(directorio, nombre_base)
    libro = Workbook()
    hoja_inicial = libro.active
    libro.remove(hoja_inicial)

    for tabla in tablas:
        hoja = libro.create_sheet(title=_normalizar_nombre_hoja(tabla.nombre))
        hoja.append(list(tabla.columnas))
        for fila in tabla.filas:
            hoja.append(list(fila))

    libro.save(ruta)
    return ruta


def exportar_tablas(
    tablas: Sequence[TablaExportable],
    directorio: str | Path,
    nombre_base: str,
    formatos: Sequence[str],
) -> ResultadoExportacionArchivos:
    """Exporta tablas a los formatos solicitados."""
    formatos_normalizados = _validar_formatos_exportacion(formatos)
    csv_paths: dict[str, Path] = {}
    xlsx_path: Path | None = None

    if FORMATO_CSV in formatos_normalizados:
        csv_paths = exportar_tablas_csv(tablas, directorio, nombre_base)
    if FORMATO_XLSX in formatos_normalizados:
        xlsx_path = exportar_tablas_xlsx(tablas, directorio, nombre_base)

    return ResultadoExportacionArchivos(csv=csv_paths, xlsx=xlsx_path)


def serializar_puntos_interseccion(
    puntos: Sequence[PuntoInterseccion],
) -> TablaExportable:
    """Convierte puntos de interseccion a una tabla exportable estable."""
    return crear_tabla_exportable(
        NOMBRE_TABLA_PUNTOS_INTERSECCION,
        COLUMNAS_PUNTOS_INTERSECCION,
        [
            (
                punto.numero,
                punto.progresiva,
                punto.punto.x,
                punto.punto.y,
                punto.longitud_tramo,
                punto.azimut,
                punto.deflexion,
                punto.giro.value,
                punto.codo_recomendado,
            )
            for punto in puntos
        ],
    )


def serializar_tramos(tramos: Sequence[Tramo]) -> TablaExportable:
    """Convierte tramos a una tabla exportable estable."""
    return crear_tabla_exportable(
        NOMBRE_TABLA_TRAMOS,
        COLUMNAS_TRAMOS,
        [
            (
                tramo.numero,
                tramo.pi_inicial,
                tramo.pi_final,
                tramo.longitud_horizontal,
                tramo.longitud_inclinada,
                tramo.pendiente,
                tramo.azimut,
            )
            for tramo in tramos
        ],
    )


def serializar_tablas_alineamiento(
    puntos: Sequence[PuntoInterseccion],
    tramos: Sequence[Tramo],
) -> tuple[TablaExportable, TablaExportable]:
    """Serializa las tablas estables del modulo de alineamiento."""
    return (
        serializar_puntos_interseccion(puntos),
        serializar_tramos(tramos),
    )


def serializar_perfil_puntos(puntos: Sequence[PerfilPunto]) -> TablaExportable:
    """Convierte el perfil por PI a una tabla exportable estable."""
    return crear_tabla_exportable(
        NOMBRE_TABLA_PERFIL_PUNTOS,
        COLUMNAS_PERFIL_PUNTOS,
        [
            (
                punto.numero_pi,
                punto.progresiva,
                punto.cota_terreno,
            )
            for punto in puntos
        ],
    )


def serializar_perfil_tramos(tramos: Sequence[PerfilTramo]) -> TablaExportable:
    """Convierte el perfil por tramo a una tabla exportable estable."""
    return crear_tabla_exportable(
        NOMBRE_TABLA_PERFIL_TRAMOS,
        COLUMNAS_PERFIL_TRAMOS,
        [
            (
                tramo.numero_tramo,
                tramo.pi_inicial,
                tramo.pi_final,
                tramo.longitud_horizontal,
                tramo.delta_z,
                tramo.longitud_inclinada,
                tramo.pendiente_porcentaje,
            )
            for tramo in tramos
        ],
    )


def serializar_tablas_perfil(
    puntos: Sequence[PerfilPunto],
    tramos: Sequence[PerfilTramo],
) -> tuple[TablaExportable, TablaExportable]:
    """Serializa las tablas estables del modulo de perfil longitudinal."""
    return (
        serializar_perfil_puntos(puntos),
        serializar_perfil_tramos(tramos),
    )


def _normalizar_nombre_hoja(nombre: str) -> str:
    """Normaliza nombres de hoja de Excel a restricciones validas."""
    traduccion = str.maketrans({caracter: "_" for caracter in "[]:*?/\\"})
    nombre_limpio = nombre.translate(traduccion).strip() or "hoja"
    return nombre_limpio[:31]


def _validar_formatos_exportacion(formatos: Sequence[str]) -> tuple[str, ...]:
    """Valida y normaliza los formatos de exportacion solicitados."""
    formatos_limpios = tuple(formato.strip().lower() for formato in formatos if formato)
    if not formatos_limpios:
        raise ValueError("Debe seleccionarse al menos un formato de exportacion.")

    desconocidos = [
        formato for formato in formatos_limpios if formato not in FORMATOS_EXPORTACION
    ]
    if desconocidos:
        raise ValueError(f"Formatos de exportacion no soportados: {desconocidos!r}")

    return tuple(dict.fromkeys(formatos_limpios))
