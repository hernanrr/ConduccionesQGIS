# Arquitectura v0.2

## Enfoque

El proyecto sigue una arquitectura **library-first**:

- `core/` contiene logica pura y reusable
- `processing/` expone algoritmos de QGIS
- `plugin/` registra el proveedor en QGIS

## Modulo implementado

`Tabla de alineamiento` genera una capa de puntos en cada PI con:

- `PI`
- `Progresiva`
- `X`
- `Y`
- `Longitud_tramo`
- `Azimut`
- `Deflexion`
- `Giro`
- `Codo_recomendado`

## Exportacion v0.2

La exportacion sigue una base reusable en `core/exportacion.py`:

- `puntos_interseccion` se exporta a CSV y/o XLSX
- `tramos` se exporta a CSV y/o XLSX
- `Tabla de alineamiento` puede exportar al finalizar
- `Exportar resultados` permite exportar una capa ya generada

El `XLSX` agrupa las tablas en hojas separadas y depende de `openpyxl`.

## Reglas clave

- Deflexion con convencion `0° = linea recta`
- Solo polilinea simple
- Catalogo de codos configurable
- Interfaz en espanol
