# Motores principales SONARA-PHYSICS-1 y SONARA-ISO12354-RAIN-1

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

Los 674 revestimientos `FloorCover` están conectados al cálculo de impacto
mediante sus espectros medidos de mejora `ΔL(f)` entre 20 Hz y 10 kHz. SONARA
interpola esos datos a las bandas del cálculo, los resta al nivel de la losa
base y obtiene `Ln,w`, `L'nT,w`, `CI` y `ΔLw`; no sustituye el espectro por un
único valor promedio.

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

## Serie ISO/EN 12354 conectada al motor principal

- ISO 12354-1: transmisión aérea directa `Dd` y caminos `Df`, `Fd` y `Ff`
  para cada unión, con suma energética, `R'` y `DnT`.
- ISO 12354-2 / ISO 717-2: impacto, con selección de revestimiento medido o
  modelo genérico/físico, cielo y caminos estructurales flanqueantes.
- ISO 12354-3 / ISO 717-1: fachadas compuestas por combinación energética de
  elementos grandes, elementos pequeños `Dn,e` y juntas `Rs`.
- ISO 12354-4: potencia sonora radiada desde recintos hacia el exterior,
  desglosada por elemento de envolvente.
- EN 12354-5: instalaciones por vías aérea en el mismo recinto, aérea entre
  recintos, salida de conducto y transmisión estructural mediante función de
  transferencia instalada.
- EN 12354-6: absorción equivalente y reverberación mediante Sabine y Eyring.
- ISO 717-1 e ISO 717-2: descriptores únicos y términos de adaptación.

Cada módulo devuelve el espectro total y las contribuciones individuales. La
interfaz no oculta los caminos detrás de un único ajuste global.

## Ruido de lluvia

El trazado implementado reproduce la arquitectura física identificada:

1. `TRainCalcParameters`: intensidad, tipo y área de lluvia.
2. `TDrop/DropIteration`: diámetro, masa, velocidad terminal y frecuencia de
   impactos.
3. `TRain`: potencia cinética normal incidente.
4. `TRoof.calculateRain`: masa superficial, rigidez a flexión,
   amortiguamiento, apoyos y frecuencia crítica.
5. `NearFieldDropsRadiation`: radiación espectral de la hoja.
6. `TRoofDoublePanel.InitRoof` y `calcISPLTwoPort`: transferencia de cubierta
   doble y corrección de la resonancia masa-aire-masa.
7. Conversión a presión sonora en el recinto mediante área de cubierta y
   absorción equivalente.

La cubierta triple no está habilitada como resultado validado: el propio
programa analizado declara esa rama no operativa. La salida de lluvia de
SONARA se identifica como predicción física y nunca como dato de laboratorio.

SONARA entrega los valores acústicos. La clasificación ISO/TS 19488 continúa
siendo realizada por el alumno.

## Validación pendiente

Los motores están activos como fuente principal, pero su versión se mantiene
visible. La implementación no equivale por sí sola a una certificación de
conformidad del software. Las comparaciones deben registrar, por banda:

- frecuencia;
- resultado de referencia;
- resultado SONARA;
- diferencia firmada y absoluta;
- sesgo, MAE, RMSE, error máximo y diferencia de Rw.

Las discrepancias deben corregirse en los auxiliares físicos identificados, no
mediante ajustes ocultos por material.
