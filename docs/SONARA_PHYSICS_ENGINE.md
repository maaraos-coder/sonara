# Motor principal SONARA-PHYSICS-1

## Alcance incorporado

SONARA usa este motor como fuente principal de las curvas de aislamiento
acústico de paneles simples, elementos multicapa adheridos, paneles dobles y
DVH. Los módulos ISO 717-1, ISO 12354-1, optimización y proyectos reciben las
curvas generadas por este núcleo.

La implementación mantiene adaptadores con los nombres históricos de las
funciones para poder abrir proyectos guardados, pero ya no ejecuta el motor
anterior.

## Catálogo

La base SQLite, distribuida como `data/acoustic_catalog.sqlite.xz.part-*` y
reconstruida automáticamente con verificación SHA-256, contiene 3.646 registros
canónicos:

| Familia | Registros |
|---|---:|
| Materials | 1.576 |
| Glazing | 81 |
| Core | 46 |
| Absorption | 528 |
| Profiles | 282 |
| Stud | 71 |
| Connections | 388 |
| FloorCover | 674 |

De los 1.657 materiales y vidrios, 1.255 registros isótropos tienen densidad,
módulo de Young, amortiguamiento, espesor y Poisson completos y entran
directamente a los selectores de cálculo. Los modelos compuestos, ortótropos,
corrugados y con núcleo permanecen consultables, pero no se fuerzan mediante
ecuaciones de placa isótropa.

## Métodos activos

Para una placa isótropa:

\[
m'=\rho h,
\qquad
B=\frac{Eh^3}{12(1-\nu^2)},
\qquad
f_c=\frac{c_0^2}{2\pi}\sqrt{\frac{m'}{B}}.
\]

La rigidez de corte de la rama isótropa se calcula como:

\[
G_s=\frac{Eh}{3{,}64}.
\]

El motor calcula un camino no resonante mediante integración angular y un
camino resonante 2022. Ambos se combinan energéticamente:

\[
R=-10\log_{10}\left(10^{-R_{nr}/10}+10^{-R_r/10}\right).
\]

El camino resonante emplea la pérdida de radiación, el área de la placa, su
densidad modal y la pérdida estructural. La eficiencia de radiación y la
densidad modal están implementadas como auxiliares físicos explícitos para que
puedan reemplazarse o calibrarse después de las comparaciones.

En sistemas con dos o más hojas, las resonancias masa-aire-masa se obtienen
armando las matrices de masa y rigidez de las cavidades y resolviendo el
problema generalizado de autovalores. Para dos hojas esto coincide con la
expresión escalar clásica.

## Métodos de proyecto conectados

- ISO 717-1: Rw, C y Ctr.
- ISO 12354-1: transmisión directa y flanqueos.
- ISO 12354-2 / ISO 717-2: impacto.
- Fachadas compuestas.
- Ruido de instalaciones por bandas de octava.
- Reverberación por Sabine y Eyring.

SONARA entrega los valores acústicos. La clasificación ISO/TS 19488 continúa
siendo realizada por el alumno.

## Validación pendiente

El motor está activo como motor principal, pero su versión se mantiene visible
en los resultados. Las próximas comparaciones deben registrar, por banda:

- frecuencia;
- resultado de referencia;
- resultado SONARA;
- diferencia firmada y absoluta;
- sesgo, MAE, RMSE, error máximo y diferencia de Rw.

Las discrepancias deben corregirse en los auxiliares físicos identificados, no
mediante ajustes ocultos por material.
