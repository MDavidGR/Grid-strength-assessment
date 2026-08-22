## GRID STRENGTH ASSESSMENT
========================

Repositorio asociado al artículo de investigación sobre la evaluación de la
fortaleza de red (Grid Strength) en sistemas eléctricos de transmisión con
alta penetración de generación basada en inversores (IBR).

El repositorio contiene los códigos, archivos de entrada y estructura de
datos necesarios para reproducir la metodología desarrollada utilizando
DIgSILENT PowerFactory y Python.

La metodología se valida utilizando los sistemas de prueba IEEE de 9 y 39
nodos.

----------------------------------------------------------------------
## 1. OBJETIVO DEL REPOSITORIO
----------------------------------------------------------------------

El objetivo de este repositorio es facilitar la reproducción de los
resultados presentados en el artículo, proporcionando:

- Scripts ejecutados en DIgSILENT PowerFactory.
- Scripts de procesamiento desarrollados en Python.
- Archivos de entrada y salida utilizados durante el flujo de cálculo.
- Sistemas de prueba IEEE 9 y 39 nodos.
- Archivos correspondientes a los escenarios operativos.
- Estructura organizada para almacenar resultados y figuras.

El flujo está diseñado para que los scripts de procesamiento puedan
utilizarse sobre cualquiera de los ejemplos ubicados en:

    data/example/

siempre que la carpeta del ejemplo contenga los archivos de entrada
requeridos.


----------------------------------------------------------------------
## 2. ESTRUCTURA DEL REPOSITORIO
----------------------------------------------------------------------

La estructura general del repositorio es:

Grid-strength-assessment/
│
├── data/
│   ├── example/
│   │   ├── IEEE39/
│   │   └── IEEE9/
│   │
│   └── scenarios/
│       ├── IEEE39/
│       └── IEEE9/
│
├── docs/
│
├── figures/
│   ├── IEEE39/
│   └── IEEE9/
│
├── powerfactory/
│   ├── export_network_data.py
│   ├── extract_scenario_data.py
│   └── power_sweep.py
│
├── python/
│   ├── analysis/
│   ├── indicators/
│   ├── preprocessing/
│   │   ├── calculate_zbus.py
│   │   └── find_electrically_close_nodes.py
│   └── visualization/
│
├── results/
│   ├── IEEE39/
│   └── IEEE9/
│
├── .gitignore
├── README.txt
└── requirements.txt


----------------------------------------------------------------------
## 3. REQUISITOS
----------------------------------------------------------------------

Para reproducir el flujo completo se requiere:

SOFTWARE
--------

- DIgSILENT PowerFactory.
- Python 3.x.
- Git (opcional, únicamente para clonar y administrar el repositorio).

LIBRERÍAS DE PYTHON
-------------------

Las principales librerías utilizadas son:

- pandas
- numpy
- scipy
- matplotlib
- openpyxl

Las dependencias pueden instalarse utilizando:

    pip install -r requirements.txt


----------------------------------------------------------------------
## 4. FLUJO GENERAL DE LA METODOLOGÍA
----------------------------------------------------------------------

El flujo completo se divide en las siguientes etapas:

1. Montaje del sistema eléctrico en DIgSILENT PowerFactory.
2. Modelado manual de los generadores no síncronos.
3. Exportación de información de la red desde PowerFactory.
4. Cálculo de la matriz Zbus.
5. Identificación de nodos eléctricamente cercanos.
6. Selección manual de los nodos donde se ubicarán los generadores no
   síncronos.
7. Ejecución del algoritmo de barrido de potencia.
8. Obtención de la frontera de puntos críticos.
9. Construcción manual del archivo de escenarios.
10. Ejecución del algoritmo de extracción de información para cada escenario.
11. Cálculo de los indicadores de fortaleza de red.
12. Procesamiento y visualización de resultados.


======================================================================
## 5. ETAPA 1 - PREPARACIÓN DEL SISTEMA EN POWERFACTORY
======================================================================

Antes de ejecutar los scripts, el usuario debe disponer del sistema
eléctrico montado en DIgSILENT PowerFactory.

Los ejemplos utilizados en este trabajo corresponden a:

- IEEE 9 nodos.
- IEEE 39 nodos.

Los generadores no síncronos utilizados para el análisis deben ser
modelados manualmente en PowerFactory en los nodos seleccionados por
el usuario.


----------------------------------------------------------------------
## 6. ETAPA 2 - EXPORTACIÓN DE INFORMACIÓN DESDE POWERFACTORY
----------------------------------------------------------------------

El primer script que debe ejecutarse es:

    powerfactory/export_network_data.py

Este script se ejecuta directamente desde el entorno Python Script de
DIgSILENT PowerFactory.

El script realiza las siguientes tareas:

1. Construye la matriz Ybus a partir de los elementos de la red.
2. Ejecuta un flujo de carga.
3. Exporta las corrientes de los generadores.
4. Exporta las tensiones de los nodos.
5. Exporta las potencias activas de los generadores.
6. Ejecuta un cálculo de cortocircuito trifásico.
7. Exporta las corrientes y potencias de cortocircuito.

Como resultado se generan los siguientes archivos:

    Ybus_export.csv
    corrientes_generadores.csv
    tensiones_nodos.csv
    potencias_activas_generadores.csv
    cortocircuito_trifasico.csv


IMPORTANTE
----------

La ruta de salida debe ser configurada por el usuario dentro del script
antes de ejecutarlo.

Se recomienda utilizar como directorio de salida la carpeta correspondiente
al ejemplo analizado.

Por ejemplo:

    data/example/IEEE39/

o:

    data/example/IEEE9/

El usuario debe verificar que los archivos generados queden almacenados
en la carpeta correspondiente al sistema analizado.


======================================================================
## 7. ETAPA 3 - CÁLCULO DE LA MATRIZ ZBUS
======================================================================

Una vez generada la matriz Ybus, se ejecuta:

    python/preprocessing/calculate_zbus.py

El script toma como entrada:

    Ybus_export.csv

y calcula la matriz de impedancias de barra:

    Zbus.csv

El script está diseñado para trabajar de manera general sobre los ejemplos
ubicados dentro de:

    data/example/

Por lo tanto, no está limitado exclusivamente al sistema IEEE de 9 o
39 nodos.

Los archivos generados se almacenan en la misma carpeta del ejemplo
analizado.


----------------------------------------------------------------------
## 8. ETAPA 4 - IDENTIFICACIÓN DE NODOS ELÉCTRICAMENTE CERCANOS
----------------------------------------------------------------------

Después de obtener Zbus se ejecuta:

    python/preprocessing/find_electrically_close_nodes.py

Este script utiliza la información de Zbus para identificar pares de nodos
eléctricamente cercanos de acuerdo con el criterio utilizado en la
metodología.

La entrada principal es:

    Zbus.csv

El resultado se almacena como:

    pares_nodos_cercanos.csv

dentro de la carpeta correspondiente al ejemplo.

Por ejemplo:

    data/example/IEEE39/pares_nodos_cercanos.csv

o:

    data/example/IEEE9/pares_nodos_cercanos.csv


======================================================================
## 9. ETAPA 5 - SELECCIÓN DE NODOS Y MODELADO DE GENERADORES
======================================================================

La identificación de nodos eléctricamente cercanos no realiza
automáticamente la ubicación de los generadores no síncronos.

El usuario debe revisar el archivo:

    pares_nodos_cercanos.csv

y seleccionar manualmente la pareja de nodos que utilizará para el
análisis.

Posteriormente, los generadores no síncronos deben ser modelados
manualmente en DIgSILENT PowerFactory en los nodos seleccionados.

El procedimiento permite que el usuario defina explícitamente la ubicación
de los generadores utilizados en el análisis.


======================================================================
## 10. ETAPA 6 - BARRIDO DE POTENCIA
======================================================================

Una vez modelados los generadores no síncronos y seleccionados los nodos,
se ejecuta:

    powerfactory/power_sweep.py

Este algoritmo se ejecuta desde el entorno Python Script de
DIgSILENT PowerFactory.

El algoritmo:

1. Identifica los generadores no síncronos modelados.
2. Identifica los nodos donde están conectados.
3. Consulta el archivo de nodos eléctricamente cercanos.
4. Verifica que la pareja de generadores cumpla el criterio de cercanía
   eléctrica.
5. Si la pareja no cumple el criterio, se genera una alerta y el algoritmo
   detiene la ejecución del barrido.
6. Si la pareja cumple el criterio, se inicia el barrido de potencia.
7. Se incrementa la potencia activa de los generadores.
8. Se evalúan las tensiones de los nodos.
9. Se determina la frontera asociada al límite superior de tensión.
10. Se almacenan los puntos críticos encontrados.
11. Se genera el archivo de resultados.
12. Se genera la gráfica correspondiente.

Antes de ejecutar el script, el usuario debe revisar y configurar los
parámetros indicados explícitamente dentro del código, entre ellos:

- Ruta del archivo de nodos eléctricamente cercanos.
- Ruta de salida.
- Umbral de impedancia.
- Punto conocido.
- Punto opuesto.
- Parámetros propios del barrido.

Estos parámetros deben ser ajustados de acuerdo con el sistema que se
quiera analizar.


======================================================================
## 11. ETAPA 7 - CURVA DE PUNTOS CRÍTICOS
======================================================================

Como resultado del barrido de potencia se obtiene una curva que representa
la frontera de operación asociada al límite superior de tensión.

Para cada pareja de generadores analizada se genera:

- Un archivo CSV con los puntos críticos.
- Una gráfica de la frontera.

Los resultados deben almacenarse en la carpeta correspondiente del sistema
analizado.


======================================================================
## 12. ETAPA 8 - DEFINICIÓN DE ESCENARIOS
======================================================================

A partir de la curva de puntos críticos obtenida en la etapa anterior,
el usuario selecciona manualmente los puntos de operación que serán
utilizados para el cálculo posterior de los indicadores.

Para esto se utiliza un archivo Excel ubicado en:

    data/scenarios/IEEE39/
    data/scenarios/IEEE9/

El archivo tiene el formato:

    Potencias_Comp_PV1_PV2.xlsx


IMPORTANTE
----------

El formato del archivo Excel debe mantenerse.

El usuario debe asignar los escenarios utilizando nombres consecutivos:

    Escenario_1
    Escenario_2
    Escenario_3
    ...

Para cada escenario se deben especificar los valores de potencia
correspondientes a:

    PV1
    PV2

Estos valores corresponden a los puntos seleccionados de la curva
obtenida mediante el barrido de potencia.


======================================================================
## 13. ETAPA 9 - EXTRACCIÓN DE INFORMACIÓN DE LOS ESCENARIOS
======================================================================

Una vez construido el archivo de escenarios, se ejecuta:

    powerfactory/extract_scenario_data.py

Este script se ejecuta desde el entorno Python Script de DIgSILENT
PowerFactory.

El script utiliza el archivo Excel de escenarios para identificar los
puntos de operación que deben ser evaluados.

Para cada escenario, se extrae la información requerida desde
PowerFactory.

Los archivos de entrada y salida deben ser configurados en las rutas
indicadas dentro del script.

El objetivo de esta etapa es generar la información necesaria para el
cálculo posterior de los indicadores.


======================================================================
## 14. ETAPA 10 - CÁLCULO DE INDICADORES
======================================================================

La información obtenida durante las etapas anteriores se utiliza
posteriormente para calcular los diferentes indicadores de fortaleza de
red considerados en la metodología.

Entre los indicadores utilizados se encuentran:

- SCR
- WSCR
- CSCR
- GSIM
- NRSCR
- SDSCR
- λSCR
- K_vtg
- LSCR

Los scripts correspondientes al cálculo de indicadores se encuentran en:

    python/indicators/

Los archivos generados durante las etapas anteriores sirven como entradas
para los diferentes cálculos.


======================================================================
## 15. ETAPA 11 - ANÁLISIS Y VISUALIZACIÓN
======================================================================

Los resultados de los indicadores pueden ser procesados posteriormente
para generar las tablas y figuras utilizadas en el análisis.

Los scripts asociados al análisis se encuentran en:

    python/analysis/

y los scripts relacionados con las figuras se encuentran en:

    python/visualization/


======================================================================
## 16. ORGANIZACIÓN DE LOS DATOS
======================================================================

Los datos asociados a cada sistema de prueba se mantienen separados.

Por ejemplo:

    data/example/IEEE39/

contiene los archivos correspondientes al sistema IEEE de 39 nodos.

Mientras que:

    data/example/IEEE9/

contiene los archivos correspondientes al sistema IEEE de 9 nodos.

De esta manera, los resultados de un sistema no interfieren con los
resultados de otro.


======================================================================
## 17. FLUJO RESUMIDO DE EJECUCIÓN
======================================================================

Para reproducir el análisis completo, seguir el siguiente orden:

    1. Montar el sistema en PowerFactory.

    2. Modelar manualmente los generadores no síncronos.

    3. Ejecutar:
           powerfactory/export_network_data.py

       Resultado:
           Ybus_export.csv
           corrientes_generadores.csv
           tensiones_nodos.csv
           potencias_activas_generadores.csv
           cortocircuito_trifasico.csv

    4. Ejecutar:
           python/preprocessing/calculate_zbus.py

       Resultado:
           Zbus.csv

    5. Ejecutar:
           python/preprocessing/find_electrically_close_nodes.py

       Resultado:
           pares_nodos_cercanos.csv

    6. Revisar manualmente:
           pares_nodos_cercanos.csv

    7. Seleccionar los nodos donde se ubicarán los generadores no síncronos.

    8. Modelar los generadores no síncronos en PowerFactory.

    9. Configurar y ejecutar:
           powerfactory/power_sweep.py

       Resultado:
           Curva de puntos críticos.
           Archivo CSV de puntos críticos.

   10. Seleccionar manualmente los puntos de operación de interés.

   11. Registrar los puntos seleccionados en:
           Potencias_Comp_PV1_PV2.xlsx

   12. Ejecutar:
           powerfactory/extract_scenario_data.py

   13. Utilizar la información extraída para calcular los indicadores.

   14. Ejecutar los scripts de análisis y visualización.


======================================================================
## 18. REPRODUCCIÓN PARA UN NUEVO SISTEMA
======================================================================

Para utilizar la metodología con un nuevo sistema de prueba, se debe crear
una nueva carpeta dentro de:

    data/example/

Por ejemplo:

    data/example/NuevoSistema/

La carpeta debe contener inicialmente el archivo:

    Ybus_export.csv

Una vez ejecutado:

    calculate_zbus.py

se generará:

    Zbus.csv

Posteriormente, al ejecutar:

    find_electrically_close_nodes.py

se generará:

    pares_nodos_cercanos.csv

Los demás archivos requeridos por los algoritmos deben ser generados
mediante el script de exportación ejecutado en PowerFactory.


======================================================================
## 19. CONSIDERACIONES IMPORTANTES
======================================================================

- Los scripts de PowerFactory deben ejecutarse desde el entorno Python
  Script de DIgSILENT PowerFactory.

- Las rutas de entrada y salida de los scripts de PowerFactory deben ser
  configuradas por el usuario antes de ejecutar cada script.

- El modelo eléctrico debe estar correctamente configurado en PowerFactory.

- Los generadores no síncronos deben ser modelados manualmente antes de
  ejecutar el barrido de potencia.

- La selección de los nodos eléctricamente cercanos y de los puntos de
  operación es una etapa manual de la metodología.

- Los valores de los parámetros del barrido deben revisarse antes de
  ejecutar el análisis sobre un nuevo sistema.

- Los nombres de los escenarios deben seguir el formato:

      Escenario_1
      Escenario_2
      Escenario_3
      ...

- La estructura del archivo Excel de escenarios debe mantenerse para
  garantizar la correcta lectura por parte del script.


======================================================================
## 20. REPOSITORIO
======================================================================

Repositorio:

Grid-strength-assessment

El repositorio contiene los códigos y archivos necesarios para documentar
y reproducir la metodología presentada en el artículo.


======================================================================
## 21. LICENCIA
======================================================================

La información relacionada con la licencia y condiciones de uso del
repositorio debe ser especificada por los autores.