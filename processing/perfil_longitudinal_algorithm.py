"""Algoritmo de Processing para el perfil longitudinal desde MDT."""

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
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
    QgsRaster,
    QgsRasterLayer,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant

from ConduccionesQGIS.core.alineamiento import construir_tabla_alineamiento
from ConduccionesQGIS.core.exportacion import (
    FORMATO_CSV,
    FORMATO_XLSX,
    exportar_tablas,
    serializar_tablas_perfil,
)
from ConduccionesQGIS.core.models import Punto2D
from ConduccionesQGIS.core.perfil import construir_perfil_longitudinal


class PerfilLongitudinalAlgorithm(QgsProcessingAlgorithm):
    """Calcula el perfil longitudinal del alineamiento a partir de un MDT."""

    INPUT = "INPUT"
    DEM = "DEM"
    BAND = "BAND"
    EXPORT_ENABLED = "EXPORT_ENABLED"
    EXPORT_DIRECTORY = "EXPORT_DIRECTORY"
    EXPORT_BASE_NAME = "EXPORT_BASE_NAME"
    EXPORT_FORMATS = "EXPORT_FORMATS"
    OUTPUT_POINTS = "OUTPUT_POINTS"
    OUTPUT_SEGMENTS = "OUTPUT_SEGMENTS"

    def initAlgorithm(self, config=None) -> None:
        """Define los parametros de entrada y salida."""
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                "Alineamiento",
                [QgsProcessing.TypeVectorLine],
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM,
                "MDT",
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.BAND,
                "Banda del MDT",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1,
                minValue=1,
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
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_POINTS,
                "Perfil longitudinal - PI",
                QgsProcessing.TypeVectorPoint,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_SEGMENTS,
                "Perfil longitudinal - tramos",
                QgsProcessing.TypeVector,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Ejecuta el calculo de perfil longitudinal con muestreo de MDT."""
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException("No se pudo leer la capa de alineamiento.")

        dem = self.parameterAsRasterLayer(parameters, self.DEM, context)
        if dem is None:
            raise QgsProcessingException("No se pudo leer el MDT.")

        features = list(source.getFeatures())
        if len(features) != 1:
            raise QgsProcessingException(
                "La capa debe contener exactamente una polilinea de alineamiento."
            )

        feature = features[0]
        geometry = feature.geometry()
        if feature is None or geometry.isNull():
            raise QgsProcessingException("La geometria de entrada es invalida.")
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

        vertices = [Punto2D(x=vertice.x(), y=vertice.y()) for vertice in polyline]
        puntos, tramos = construir_tabla_alineamiento(vertices)
        banda = self.parameterAsInt(parameters, self.BAND, context)
        cotas = [
            self._muestrear_cota(dem, punto.punto.x, punto.punto.y, banda)
            for punto in puntos
        ]
        perfil_puntos, perfil_tramos = construir_perfil_longitudinal(
            puntos,
            tramos,
            cotas,
        )

        points_fields = _crear_campos_perfil_puntos()
        points_sink, points_destination_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_POINTS,
            context,
            points_fields,
            QgsWkbTypes.Point,
            source.sourceCrs(),
        )
        if points_sink is None:
            raise QgsProcessingException("No se pudo crear la salida de PI.")

        segments_fields = _crear_campos_perfil_tramos()
        segments_sink, segments_destination_id = self.parameterAsSink(
            parameters,
            self.OUTPUT_SEGMENTS,
            context,
            segments_fields,
            QgsWkbTypes.NoGeometry,
            source.sourceCrs(),
        )
        if segments_sink is None:
            raise QgsProcessingException("No se pudo crear la salida de tramos.")

        total = len(perfil_puntos) + len(perfil_tramos)
        procesados = 0

        for punto_origen, perfil_punto in zip(puntos, perfil_puntos, strict=True):
            feature_out = QgsFeature(points_fields)
            feature_out.setGeometry(
                QgsGeometry.fromPointXY(
                    QgsPointXY(punto_origen.punto.x, punto_origen.punto.y)
                )
            )
            feature_out["PI"] = perfil_punto.numero_pi
            feature_out["Progresiva"] = perfil_punto.progresiva
            feature_out["Cota_terreno"] = perfil_punto.cota_terreno
            points_sink.addFeature(feature_out)
            procesados += 1
            feedback.setProgress(int((procesados / total) * 100))

        for perfil_tramo in perfil_tramos:
            feature_out = QgsFeature(segments_fields)
            feature_out["Tramo"] = perfil_tramo.numero_tramo
            feature_out["PI_inicial"] = perfil_tramo.pi_inicial
            feature_out["PI_final"] = perfil_tramo.pi_final
            feature_out["Longitud_horizontal"] = perfil_tramo.longitud_horizontal
            feature_out["Delta_Z"] = perfil_tramo.delta_z
            feature_out["Longitud_inclinada"] = perfil_tramo.longitud_inclinada
            feature_out["Pendiente"] = perfil_tramo.pendiente_porcentaje
            segments_sink.addFeature(feature_out)
            procesados += 1
            feedback.setProgress(int((procesados / total) * 100))

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

            tablas = serializar_tablas_perfil(perfil_puntos, perfil_tramos)
            resultado = exportar_tablas(tablas, directorio, nombre_base, formatos)
            for nombre_tabla, ruta in resultado.csv.items():
                feedback.pushInfo(f"CSV exportado ({nombre_tabla}): {ruta}")
            if resultado.xlsx is not None:
                feedback.pushInfo(f"XLSX exportado: {resultado.xlsx}")

        return {
            self.OUTPUT_POINTS: points_destination_id,
            self.OUTPUT_SEGMENTS: segments_destination_id,
        }

    def name(self) -> str:
        """Devuelve el nombre interno del algoritmo."""
        return "perfil_longitudinal"

    def displayName(self) -> str:
        """Devuelve el nombre visible del algoritmo."""
        return "Perfil longitudinal"

    def group(self) -> str:
        """Devuelve el grupo visible del algoritmo."""
        return "Ingeniería Hidráulica"

    def groupId(self) -> str:
        """Devuelve el identificador interno del grupo."""
        return "ingenieria_hidraulica"

    def shortHelpString(self) -> str:
        """Devuelve la ayuda corta del algoritmo."""
        return (
            "Muestrea un MDT en cada PI del alineamiento y genera tablas de "
            "cotas y calculos por tramo."
        )

    def createInstance(self):
        """Crea una nueva instancia del algoritmo."""
        return PerfilLongitudinalAlgorithm()

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

    def _muestrear_cota(
        self,
        dem: QgsRasterLayer,
        x: float,
        y: float,
        banda: int,
    ) -> float:
        """Muestrea la cota del MDT en una coordenada XY."""
        resultado = dem.dataProvider().identify(
            QgsPointXY(x, y),
            QgsRaster.IdentifyFormatValue,
        )
        if not resultado.isValid():
            raise QgsProcessingException(
                f"No se pudo muestrear el MDT en la coordenada ({x}, {y})."
            )

        valor = resultado.results().get(banda)
        if valor is None:
            raise QgsProcessingException(
                f"La banda {banda} no devolvio un valor valido en ({x}, {y})."
            )
        return float(valor)


def _crear_campos_perfil_puntos() -> QgsFields:
    """Crea los campos de la tabla de perfil por PI."""
    fields = QgsFields()
    fields.append(QgsField("PI", QVariant.Int))
    fields.append(QgsField("Progresiva", QVariant.Double))
    fields.append(QgsField("Cota_terreno", QVariant.Double))
    return fields


def _crear_campos_perfil_tramos() -> QgsFields:
    """Crea los campos de la tabla de perfil por tramo."""
    fields = QgsFields()
    fields.append(QgsField("Tramo", QVariant.Int))
    fields.append(QgsField("PI_inicial", QVariant.Int))
    fields.append(QgsField("PI_final", QVariant.Int))
    fields.append(QgsField("Longitud_horizontal", QVariant.Double))
    fields.append(QgsField("Delta_Z", QVariant.Double))
    fields.append(QgsField("Longitud_inclinada", QVariant.Double))
    fields.append(QgsField("Pendiente", QVariant.Double))
    return fields
