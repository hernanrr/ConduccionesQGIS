"""Punto de entrada del plugin ConduccionesQGIS."""


def classFactory(iface):
    """Devuelve la instancia principal del plugin para QGIS."""
    from ConduccionesQGIS.plugin.conducciones_plugin import ConduccionesQGISPlugin

    return ConduccionesQGISPlugin(iface)
