# ConduccionesQGIS

Plugin de QGIS 4.x orientado a la ensenanza del diseno de conducciones a presion.

## Alcance v0.3

- Arquitectura base library-first
- Herramienta de Processing `Tabla de alineamiento`
- Exportacion opcional integrada a CSV y XLSX
- Herramienta separada `Exportar resultados`
- Herramienta de Processing `Perfil longitudinal` a partir de MDT
- Nucleo reutilizable en `core/`
- Pruebas unitarias para la logica geometrica y de alineamiento

## Dependencia runtime para XLSX

La exportacion a `XLSX` usa `openpyxl`.

En el entorno de desarrollo queda gestionada por `uv`. En el runtime real de QGIS,
si el Python de QGIS no incluye `openpyxl`, la exportacion a XLSX fallara hasta que
esa dependencia se instale tambien en ese entorno.

## Estado del perfil longitudinal

`v0.3` implementa el perfil longitudinal con entrada de `MDT`.

La integracion con un perfil ya generado por SAGA queda diferida a `v0.4`, aunque el
nucleo ya esta separado para facilitar esa incorporacion posterior.

## Estructura

```text
ConduccionesQGIS/
├── __init__.py
├── metadata.txt
├── plugin/
├── processing/
├── core/
├── tests/
├── docs/
└── ejemplos/
```
