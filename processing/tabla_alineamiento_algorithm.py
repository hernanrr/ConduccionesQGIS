"""Algoritmo de Processing para generar la tabla de alineamiento."""

from __future__ import annotations

from qgis.core import (
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterString,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant

from ConduccionesQGIS.core.alineamiento import (
    construir_tabla_alineamiento,
    parsear_catalogo_codos,
)
from ConduccionesQGIS.core.exportacion import (
    FORMATO_CSV,
    FORMATO_XLSX,
    exportar_tablas,
    serializar_tablas_alineamiento,
)
from ConduccionesQGIS.core.models import Punto2D


class TablaAlineamientoAlgorithm(QgsProcessingAlgorithm):
    """Genera la tabla de alineamiento a partir de una polilinea simple."""

    INPUT = "INPUT"
    BEND_CATALOG = "BEND_CATALOG"
    EXPORT_ENABLED = "EXPORT_ENABLED"
    EXPORT_DIRECTORY = "EXPORT_DIRECTORY"
    EXPORT_BASE_NAME = "EXPORT_BASE_NAME"
    EXPORT_FORMATS = "EXPORT_FORMATS"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config=None) -> None:
        """Define parametros de entrada y salida."""
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                "Alineamiento",
                [QgsProcessing.TypeVectorLine],
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.BEND_CATALOG,
                "Catálogo de codos (separado por comas)",
                defaultValue="11.25,22.5,45,90",
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                "Tabla de alineamiento",
                QgsProcessing.TypeVectorPoint,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.EXPORT_ENABLED,
                "Exportar resultados a archivos",
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.EXPORT_DIRECTORY,
                "Directorio de exportación",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.EXPORT_BASE_NAME,
                "Nombre base de exportación",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.EXPORT_FORMATS,
                "Formatos de exportación",
                options=["CSV", "XLSX"],
                allowMultiple=True,
                optional=True,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Ejecuta el algoritmo."""
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException("No se pudo leer la capa de alineamiento.")

        features = list(source.getFeatures())
        if len(features) != 1:
            raise QgsProcessingException(
                "La capa debe contener exactamente una polilinea de alineamiento."
            )

        feature = features[0]
        if feature is None or feature.geometry().isNull():
            raise QgsProcessingException("La geometria de entrada es invalida.")

        geometry = feature.geometry()
        if geometry.isMultipart():
            raise QgsProcessingException(
                "La geometria de entrada no puede ser multipart."
            )

        if QgsWkbTypes.geometryType(geometry.wkbType()) != QgsWkbTypes.LineGeometry:
            raise QgsProcessingException(
                "La geometria de entrada debe ser una polilinea."
            )

        polyline = geometry.asPolyline()
        if not polyline:
            raise QgsProcessingException(
                "No se pudo convertir la geometria a una polilinea simple."
            )

        catalogo_texto = self.parameterAsString(parameters, self.BEND_CATALOG, context)
        catalogo = parsear_catalogo_codos(catalogo_texto.split(","))
        vertices = [Punto2D(x=vertice.x(), y=vertice.y()) for vertice in polyline]
        puntos, tramos = construir_tabla_alineamiento(vertices, catalogo)

        fields = _crear_campos()
        sink, destination_id = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Point,
            source.sourceCrs(),
        )
        if sink is None:
            raise QgsProcessingException("No se pudo crear la salida de resultados.")

        total = len(puntos)
        for indice, punto in enumerate(puntos):
            if feedback.isCanceled():
                break

            feature_out = QgsFeature(fields)
            feature_out.setGeometry(
                QgsGeometry.fromPointXY(QgsPointXY(punto.punto.x, punto.punto.y))
            )
            feature_out["PI"] = punto.numero
            feature_out["Progresiva"] = punto.progresiva
            feature_out["X"] = punto.punto.x
            feature_out["Y"] = punto.punto.y
            feature_out["Longitud_tramo"] = punto.longitud_tramo
            feature_out["Azimut"] = punto.azimut
            feature_out["Deflexión"] = punto.deflexion
            feature_out["Giro"] = punto.giro.value
            feature_out["Codo_recomendado"] = punto.codo_recomendado
            sink.addFeature(feature_out)
            feedback.setProgress(int(((indice + 1) / total) * 100))

        export_enabled = self.parameterAsBool(parameters, self.EXPORT_ENABLED, context)
        if export_enabled:
            directorio = self.parameterAsString(
                parameters, self.EXPORT_DIRECTORY, context
            )
            nombre_base = self.parameterAsString(
                parameters, self.EXPORT_BASE_NAME, context
            )
            formatos = self._resolver_formatos_exportacion(parameters, context)
            if not directorio.strip():
                raise QgsProcessingException(
                    "Debe indicar un directorio de exportación."
                )
            if not nombre_base.strip():
                raise QgsProcessingException(
                    "Debe indicar un nombre base de exportación."
                )

            tablas = serializar_tablas_alineamiento(puntos, tramos)
            resultado = exportar_tablas(tablas, directorio, nombre_base, formatos)
            for nombre_tabla, ruta in resultado.csv.items():
                feedback.pushInfo(f"CSV exportado ({nombre_tabla}): {ruta}")
            if resultado.xlsx is not None:
                feedback.pushInfo(f"XLSX exportado: {resultado.xlsx}")

        return {self.OUTPUT: destination_id}

    def name(self) -> str:
        """Devuelve el nombre interno del algoritmo."""
        return "tabla_alineamiento"

    def displayName(self) -> str:
        """Devuelve el nombre visible del algoritmo."""
        return "Tabla de alineamiento"

    def group(self) -> str:
        """Devuelve el grupo visible del algoritmo."""
        return "Ingeniería Hidráulica"

    def groupId(self) -> str:
        """Devuelve el identificador interno del grupo."""
        return "ingenieria_hidraulica"

    def shortHelpString(self) -> str:
        """Devuelve la ayuda corta del algoritmo."""
        return (
            "Genera una tabla de puntos de interseccion con progresiva, azimut, "
            "deflexión, giro y codo recomendado."
        )

    def createInstance(self):
        """Crea una nueva instancia del algoritmo."""
        return TablaAlineamientoAlgorithm()

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


def _crear_campos() -> QgsFields:
    """Crea la definicion de campos de salida."""
    fields = QgsFields()
    fields.append(QgsField("PI", QVariant.Int))
    fields.append(QgsField("Progresiva", QVariant.Double))
    fields.append(QgsField("X", QVariant.Double))
    fields.append(QgsField("Y", QVariant.Double))
    fields.append(QgsField("Longitud_tramo", QVariant.Double))
    fields.append(QgsField("Azimut", QVariant.Double))
    fields.append(QgsField("Deflexión", QVariant.Double))
    fields.append(QgsField("Giro", QVariant.String))
    fields.append(QgsField("Codo_recomendado", QVariant.Double))
    return fields
