"""Algoritmo de Processing para exportar resultados existentes del plugin."""

from __future__ import annotations

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterString,
)

from ConduccionesQGIS.core.exportacion import (
    COLUMNAS_PUNTOS_INTERSECCION,
    FORMATO_CSV,
    FORMATO_XLSX,
    NOMBRE_TABLA_PUNTOS_INTERSECCION,
    crear_tabla_exportable,
    exportar_tablas,
)


class ExportarResultadosAlgorithm(QgsProcessingAlgorithm):
    """Exporta a archivo una capa de resultados ya generada por el plugin."""

    INPUT = "INPUT"
    EXPORT_DIRECTORY = "EXPORT_DIRECTORY"
    EXPORT_BASE_NAME = "EXPORT_BASE_NAME"
    EXPORT_FORMATS = "EXPORT_FORMATS"

    def initAlgorithm(self, config=None) -> None:
        """Define parametros de entrada y salida de la exportacion."""
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                "Capa de resultados",
                [QgsProcessing.TypeVectorPoint],
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.EXPORT_DIRECTORY,
                "Directorio de exportación",
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.EXPORT_BASE_NAME,
                "Nombre base de exportación",
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.EXPORT_FORMATS,
                "Formatos de exportación",
                options=["CSV", "XLSX"],
                allowMultiple=True,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Valida la capa de entrada y exporta los resultados a archivo."""
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException("No se pudo leer la capa de resultados.")

        campos = [field.name() for field in source.fields()]
        faltantes = [
            campo for campo in COLUMNAS_PUNTOS_INTERSECCION if campo not in campos
        ]
        if faltantes:
            raise QgsProcessingException(
                "La capa no tiene el esquema esperado de Tabla de alineamiento. "
                f"Faltan campos: {faltantes}."
            )

        nombre_base = self.parameterAsString(parameters, self.EXPORT_BASE_NAME, context)
        directorio = self.parameterAsString(parameters, self.EXPORT_DIRECTORY, context)
        formatos = self._resolver_formatos_exportacion(parameters, context)

        filas = []
        for feature in source.getFeatures():
            filas.append(
                tuple(feature[campo] for campo in COLUMNAS_PUNTOS_INTERSECCION)
            )

        tabla = crear_tabla_exportable(
            NOMBRE_TABLA_PUNTOS_INTERSECCION,
            COLUMNAS_PUNTOS_INTERSECCION,
            filas,
        )
        resultado = exportar_tablas([tabla], directorio, nombre_base, formatos)

        for nombre_tabla, ruta in resultado.csv.items():
            feedback.pushInfo(f"CSV exportado ({nombre_tabla}): {ruta}")
        if resultado.xlsx is not None:
            feedback.pushInfo(f"XLSX exportado: {resultado.xlsx}")

        return {
            "csv": {nombre: str(ruta) for nombre, ruta in resultado.csv.items()},
            "xlsx": str(resultado.xlsx) if resultado.xlsx is not None else "",
        }

    def name(self) -> str:
        """Devuelve el nombre interno del algoritmo."""
        return "exportar_resultados"

    def displayName(self) -> str:
        """Devuelve el nombre visible del algoritmo."""
        return "Exportar resultados"

    def group(self) -> str:
        """Devuelve el grupo visible del algoritmo."""
        return "Ingeniería Hidráulica"

    def groupId(self) -> str:
        """Devuelve el identificador interno del grupo."""
        return "ingenieria_hidraulica"

    def shortHelpString(self) -> str:
        """Devuelve la ayuda corta del algoritmo."""
        return (
            "Exporta la capa de resultados generada por Tabla de alineamiento a "
            "CSV, XLSX o ambos formatos."
        )

    def createInstance(self):
        """Crea una nueva instancia del algoritmo."""
        return ExportarResultadosAlgorithm()

    def _resolver_formatos_exportacion(self, parameters, context) -> list[str]:
        """Convierte la seleccion de formatos a valores internos estables."""
        indices = self.parameterAsEnums(parameters, self.EXPORT_FORMATS, context)
        formatos: list[str] = []
        for indice in indices:
            if indice == 0:
                formatos.append(FORMATO_CSV)
            elif indice == 1:
                formatos.append(FORMATO_XLSX)

        if not formatos:
            raise QgsProcessingException(
                "Debe seleccionar al menos un formato de exportación."
            )

        return formatos
