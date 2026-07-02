# Arquitectura v0.1

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

## Reglas clave

- Deflexion con convencion `0° = linea recta`
- Solo polilinea simple
- Catalogo de codos configurable
- Interfaz en espanol
