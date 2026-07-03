"""Proveedor de herramientas de Processing."""

from __future__ import annotations

from qgis.core import QgsProcessingProvider

from ConduccionesQGIS.processing.exportar_resultados_algorithm import (
    ExportarResultadosAlgorithm,
)
from ConduccionesQGIS.processing.tabla_alineamiento_algorithm import (
    TablaAlineamientoAlgorithm,
)


class IngenieriaHidraulicaProvider(QgsProcessingProvider):
    """Proveedor de herramientas para Ingenieria Hidraulica."""

    def loadAlgorithms(self) -> None:
        """Registra los algoritmos disponibles."""
        self.addAlgorithm(ExportarResultadosAlgorithm())
        self.addAlgorithm(TablaAlineamientoAlgorithm())

    def id(self) -> str:
        """Devuelve el identificador interno del proveedor."""
        return "ingenieria_hidraulica"

    def name(self) -> str:
        """Devuelve el nombre visible del proveedor."""
        return "Ingeniería Hidráulica"

    def longName(self) -> str:
        """Devuelve el nombre largo del proveedor."""
        return self.name()
