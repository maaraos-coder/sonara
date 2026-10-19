# Análisis estático de Insul 10.0.8 para orientar SONARA

Fecha del análisis: 19 de octubre de 2026.

## Alcance y límites

Se inspeccionó estáticamente el instalador `insul10-setup.msi` suministrado por el usuario. No se ejecutó el instalador, no se eludió ningún mecanismo de licencia y no se descompiló ni copió código fuente propietario. Los resultados se usan únicamente para identificar categorías funcionales, parámetros de entrada y oportunidades de interoperabilidad que puedan implementarse de forma independiente en SONARA.

- SHA-256 del MSI: `cb4615432862907167f5918d8424ef13376105781800e20a142f33a209e0bafa`
- Producto declarado: Insul 10.0.8
- Ejecutable principal: PE x64 nativo, construido con Delphi/FireMonkey
- Paquete: WiX Toolset 3.11.2

## Inventario funcional observado

El paquete contiene el ejecutable principal, bibliotecas numéricas y archivos XML separados para materiales, vidrios, revestimientos de piso, perfiles, montantes, conexiones y absorción. La inspección de metadatos y cadenas técnicas muestra estos grupos de variables:

| Grupo | Variables o capacidades observadas | Aplicación independiente en SONARA |
|---|---|---|
| Placas | densidad, módulo de Young, amortiguamiento, Poisson, anisotropía, frecuencia crítica | ampliar el esquema físico del material |
| Geometría | dimensiones X/Y, condiciones de borde | preparar corrección por tamaño finito |
| Multicapas | número de hojas, cavidades, gas, profundidad, resistividad al flujo | evolucionar paneles dobles hacia un solucionador multicapa |
| Uniones | rigidez y amortiguamiento del marco, perfiles, montantes y conexiones | mejorar la transmisión estructural |
| Vidrios | varias hojas, cavidades y amortiguamiento de radiación | ampliar DVH a configuraciones múltiples |
| Pisos | revestimientos, contrapisos y parámetros de impacto | reemplazar curvas genéricas por fichas espectrales trazables |
| Evaluación | ISO 717 y ASTM; medido frente a predicho | validación por bandas y diferencia de índices globales |
| Cálculo | impedancia de radiación, pérdidas por transmisión, resonancia masa–aire–masa | mostrar diagnósticos físicos y advertencias por banda |

También se observó el uso de una biblioteca LAPACK, consistente con cálculos matriciales para sistemas de varias capas. Este dato no permite reconstruir el algoritmo propietario, pero sí confirma que una evolución seria de SONARA debería separar el modelo físico, el solucionador numérico y la evaluación normativa.

## Bases de datos detectadas

Se identificaron, aproximadamente, 1.575 materiales, 669 revestimientos de piso, 387 conexiones, 281 perfiles, 80 vidrios, 69 montantes y 45 materiales de núcleo o laminados. Esos registros contienen contenido comercial y no se incorporan a SONARA. La decisión de diseño es mantener una biblioteca propia, editable y trazable, con importación CSV.

## Mejoras implementadas en esta iteración

1. Se agregó el coeficiente de Poisson a la biblioteca de materiales y a la rigidez flexional `B = E h³ / [12(1-ν²)]`.
2. Se agregó el campo de razón anisotrópica al esquema para futuras formulaciones validadas; todavía no altera el cálculo.
3. Se hicieron visibles las frecuencias de resonancia masa–aire–masa y el límite de cámara en sistemas dobles y DVH.
4. Se incorporó validación de una predicción contra un CSV de ensayo o medición: alineación de bandas, sesgo, MAE, RMSE, error máximo, Rw medido y diferencia de Rw.
5. Se incluyeron plantilla e informe CSV descargables. SONARA continúa entregando resultados acústicos; la clasificación o el cumplimiento quedan a cargo del alumno.

## Próximas etapas recomendadas

1. Incorporar dimensiones y una corrección publicada para paneles de tamaño finito, con casos de verificación reproducibles.
2. Implementar un solucionador de matriz de transferencia para hojas, cavidades y absorbentes, apoyado en referencias abiertas.
3. Añadir curvas espectrales de mejora de pisos y techos con procedencia y condiciones de ensayo.
4. Modelar caminos estructurales de instalaciones y sumarlos energéticamente al camino aéreo.
5. Crear un banco de validación con ensayos ISO 10140 anonimizados o de acceso autorizado antes de calibrar coeficientes.

## Criterio de calidad

Una función observada en otro producto no se considera validada por el solo hecho de existir. Cada nueva formulación de SONARA debe declarar su referencia, dominio de aplicación, unidades, supuestos y error contra casos conocidos. No se ajustarán resultados para imitar salidas de un software comercial sin una base técnica reproducible.
