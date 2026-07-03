# Arquitectura v0.3

## Enfoque

El proyecto sigue una arquitectura **library-first**:

- `core/` contiene logica pura y reusable
- `processing/` expone algoritmos de QGIS
- `plugin/` registra el proveedor en QGIS

## Modulos implementados

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

`Perfil longitudinal` calcula desde un MDT:

- tabla por PI con `PI`, `Progresiva`, `Cota_terreno`
- tabla por tramo con `Longitud_horizontal`, `Delta_Z`, `Longitud_inclinada`, `Pendiente`

## Exportacion v0.2

La exportacion sigue una base reusable en `core/exportacion.py`:

- `puntos_interseccion` se exporta a CSV y/o XLSX
- `tramos` se exporta a CSV y/o XLSX
- `Tabla de alineamiento` puede exportar al finalizar
- `Exportar resultados` permite exportar una capa ya generada

El `XLSX` agrupa las tablas en hojas separadas y depende de `openpyxl`.

## Limitacion actual de v0.3

El perfil longitudinal implementado en `v0.3` muestrea un `MDT` directamente.

La reutilizacion de un perfil previamente generado por SAGA no se ha activado todavia en la
capa de Processing; se reserva para `v0.4`.

## Reglas clave

- Deflexion con convencion `0° = linea recta`
- Solo polilinea simple
- Catalogo de codos configurable
- Interfaz en espanol
