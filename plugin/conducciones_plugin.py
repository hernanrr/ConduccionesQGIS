"""Clase principal del plugin de QGIS."""

from __future__ import annotations

from ConduccionesQGIS.processing.provider import IngenieriaHidraulicaProvider


class ConduccionesQGISPlugin:
    """Registra el proveedor de Processing del plugin."""

    def __init__(self, iface) -> None:
        """Inicializa el plugin."""
        self.iface = iface
        self.provider: IngenieriaHidraulicaProvider | None = None

    def initGui(self) -> None:
        """Registra el proveedor al iniciar la interfaz."""
        self.provider = IngenieriaHidraulicaProvider()
        from qgis.core import QgsApplication

        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self) -> None:
        """Retira el proveedor al descargar el plugin."""
        if self.provider is None:
            return

        from qgis.core import QgsApplication

        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.provider = None
