# Introducción

Este repositorio está asociado al artículo de investigación sobre la evaluación de la **fortaleza de red (Grid Strength)** en sistemas eléctricos de transmisión con alta penetración de **generación basada en inversores (Inverter-Based Resources, IBR)**.

El repositorio contiene los **códigos, archivos de entrada, datos de configuración y estructura de directorios** necesarios para implementar y reproducir la metodología propuesta en el artículo. La metodología integra **DIgSILENT PowerFactory** y **Python** para el modelado del sistema eléctrico, el procesamiento de los datos y el cálculo de diferentes indicadores de fortaleza de red.

La metodología se aplica y valida utilizando los sistemas de prueba **IEEE de 9 y 39 nodos**, considerando diferentes escenarios de operación y condiciones de penetración de generación basada en inversores.

# Estructura del repositorio

El repositorio se organiza en multiples directorios de acuerdo con la función que desempeñan dentro de la metodología. Esta estructura permite separar los **archivos de entrada**, los **códigos de procesamiento**, los **modelos de DIgSILENT PowerFactory** y los **resultados generados**, facilitando la ejecución y reproducción de los resultados.

La estructura principal del repositorio es la siguiente:

```text
Grid-strength-assessment/
│
├── data/
│   ├── example/
│   │   ├── IEEE9/
│   │   └── IEEE39/
│   │
│   ├── scenarios/
│   │   ├── IEEE9/
│   │   │   ├── CAP/
│   │   │   └── IND/
│   │   └── IEEE39/
│   │       ├── CAP/
│   │       └── IND/
│   │
│   └── results/
│       ├── IEEE9/
│       └── IEEE39/
│
├── powerfactory/
│
├── python/
│   ├── preprocessing/
│   ├── analysis/
│   ├── indicators/
│   └── visualization/
│
├── results/
│   ├── IEEE9/
│   │   ├── CAP/
│   │   └── IND/
│   └── IEEE39/
│       ├── CAP/
│       └── IND/
│
└── README.md
```

## Descripción de los directorios

### `data/`

Contiene los datos utilizados durante las diferentes etapas de la metodología, incluyendo los archivos de entrada, la definición de escenarios y los resultados intermedios generados durante los cálculos.

#### `data/example/`

Contiene los archivos de entrada asociados a los sistemas de prueba **IEEE de 9 y 39 nodos**. Estos archivos constituyen la información de partida necesaria para ejecutar los diferentes procesos de análisis.

```text
data/example/
├── IEEE9/
└── IEEE39/
```

#### `data/scenarios/`

Contiene la definición de los escenarios utilizados para evaluar la fortaleza de red. Los escenarios se organizan según el sistema de prueba y el tipo de factor de potencia considerado:

* `CAP/`: escenarios con comportamiento **capacitivo**.
* `IND/`: escenarios con comportamiento **inductivo**.

Cada uno de estos directorios contiene los escenarios de prueba correspondientes (`Escenario_1` a `Escenario_6`).

```text
data/scenarios/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

#### `data/results/`

Contiene los **resultados intermedios y datos generados durante el primer procesamiento** de los escenarios. Estos archivos incluyen, entre otros, información utilizada para el cálculo de los diferentes indicadores de fortaleza de red, exportaciones de impedancias y resultados asociados a los análisis realizados en Python.

Los resultados se organizan por sistema de prueba, resultados de barrido de potencia por tipo de generación y el resultado de la extracción de información basica para los indicadores por escenario planteado.

```text
data/results/
├── IEEE9/
│   ├── CAP/
│   ├── IND/
│   ├── IEEE9C/
│   └── IEEE9I/
└── IEEE39/
    ├── CAP/
    ├── IND/
    ├── IEEE39C/
    └── IEEE39I/
```

Dentro de los directorios de cada escenario se encuentran subdirectorios específicos para los distintos tipos de información generada, tales como:

* `Datos GSIM/`: datos utilizados para el cálculo del **Grid Strength Impedance Metric (GSIM)**.
* `ExportZ_Python/`: archivos asociados a la informacion de cargas e impedancias de los generadores.
* `Informacion SCR/`: información utilizada para el cálculo de indicadores basados en **Short Circuit Ratio (SCR)**.
* `Positive/`: resultados correspondientes a la informacion base de la red (generadores, nodos, transformadores, corrientes de cortocircuito, Ybus, etc.).
* `SDSCR INFO/`: información utilizada en el cálculo del **SDSCR**.

### `powerfactory/`

Contiene los archivos asociados a **DIgSILENT PowerFactory** utilizados en el desarrollo de la metodología. En este directorio se incluyen los scripts y archivos necesarios para realizar la ejecucion de análisis de la red y exportar la información requerida por los scripts de Python.

### `python/`

Contiene los scripts desarrollados en **Python**. Los códigos se encuentran organizados de acuerdo con la etapa del procesamiento en la que son utilizados:

| Directorio       | Función                                                                                       |
| ---------------- | --------------------------------------------------------------------------------------------- |
| `preprocessing/` | Preparación, organización y procesamiento inicial de los datos de entrada.                    |
| `indicators/`    | Cálculo de los indicadores utilizados para evaluar la fortaleza de red.                       |
| `visualization/` | Generación de gráficos y representaciones utilizadas para analizar y comparar los resultados. |

Esta separación permite mantener independientes las diferentes etapas del flujo de procesamiento y facilita la reutilización de los scripts.

### `results/`

Contiene los **resultados finales y figuras generadas para el análisis de los sistemas de prueba**. A diferencia de `data/results/`, este directorio está orientado principalmente a los resultados finales utilizados para la presentación, comparación y análisis de los indicadores.

Los resultados se organizan por sistema de prueba y tipo de escenario:

```text
results/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

Dentro de cada directorio por tipo de generación se almacenan las gráficas y resultados finales correspondientes. Adicionalmente, se incluyen directorios destinados a diferentes tipos de visualización, como:

* `Graficas_SCR/`: gráficos relacionados con la evaluación de los indicadores por escenario.
* `Matriz_Graficas_Derecha/`: matriz de gráficos correspondientes a los resultados comparativos para los indicadores basados en tensión.
* `Matriz_Graficas_Izquierda/`: matrices de gráficos correspondientes a los resultados comparativos para los indicadores basados en corrientes de cortocircuito.
* `Normalized graphs/`: gráficos comparativos de indicadores normalizados.

Finalmente, `README.md` contiene la documentación general del repositorio, incluyendo la descripción de la metodología, los requisitos, la estructura de archivos y las instrucciones necesarias para reproducir los análisis.

# Requisitos

Para ejecutar la metodología y reproducir los análisis presentados en el artículo, se requiere disponer de **DIgSILENT PowerFactory** y un entorno de **Python** con las librerías utilizadas por los scripts del repositorio.

## Software

* **DIgSILENT PowerFactory 2024 SP1** o una versión compatible con los archivos y scripts incluidos en el repositorio.
* **Python 3.9 o superior**.
* Un entorno de desarrollo para Python, como **Visual Studio Code**, Jupyter Notebook u otro entorno compatible.

## Librerías de Python

Los scripts utilizan principalmente las siguientes librerías:

* `numpy`: operaciones numéricas y manipulación de matrices.
* `pandas`: lectura, procesamiento y organización de datos tabulares.
* `scipy`: operaciones y métodos utilizados en el procesamiento matemático y análisis de los resultados.
* `matplotlib`: generación de gráficos y visualización de resultados.

Las dependencias pueden instalarse mediante `pip`:

```bash
pip install numpy pandas scipy matplotlib
```

## DIgSILENT PowerFactory

Parte de la metodología se ejecuta directamente en **DIgSILENT PowerFactory**, donde se realizan los estudios eléctricos y se generan los archivos de datos utilizados posteriormente por los scripts de Python.

Los archivos asociados a PowerFactory se encuentran en el directorio:

```text
powerfactory/
```

El flujo general de ejecución consiste en:

```text
DIgSILENT PowerFactory
        │
        │ Estudios eléctricos
        ▼
Exportación de datos
        │
        ▼
Python
        │
        ├── Preprocesamiento
        ├── Cálculo de indicadores
        ├── Análisis
        └── Visualización
        │
        ▼
Resultados
```


# Instalación y configuración

## 1. Clonar el repositorio

El repositorio puede clonarse utilizando Git:

```bash
git clone <URL_DEL_REPOSITORIO>
cd Grid-strength-assessment
```

## 2. Crear un entorno virtual

Se recomienda utilizar un entorno virtual de Python para mantener aisladas las dependencias del proyecto:

```bash
python -m venv .venv
```

Para activar el entorno virtual en Windows:

```powershell
.venv\Scripts\activate
```

## 3. Instalar las dependencias

Una vez activado el entorno virtual, instalar las librerías requeridas:

```bash
pip install numpy pandas scipy matplotlib
```

## 4. Configuración de las rutas

Los scripts del repositorio están organizados para trabajar utilizando rutas relativas a la estructura principal del proyecto. Esto permite ejecutar el código sin depender de rutas absolutas específicas del equipo donde se realiza el análisis.

La estructura base utilizada es:

```text
Grid-strength-assessment/
├── data/
├── powerfactory/
├── python/
└── results/
```

Los archivos de entrada se encuentran principalmente en:

```text
data/example/
data/scenarios/
```

mientras que los resultados generados por los procesos de análisis se almacenan en:

```text
data/results/
results/
```

Por lo tanto, se recomienda mantener la estructura de directorios del repositorio sin modificar los nombres de las carpetas principales.

## 5. Configuración de DIgSILENT PowerFactory

Los estudios que requieren DIgSILENT PowerFactory deben ejecutarse utilizando los modelos y scripts incluidos en:

```text
powerfactory/
```

Antes de ejecutar estos estudios, se debe verificar que:

1. DIgSILENT PowerFactory se encuentre correctamente instalado.
2. La versión utilizada sea compatible con los archivos del repositorio.
3. Los modelos de los sistemas de prueba estén disponibles.
4. Las rutas de entrada y salida utilizadas por los scripts correspondan a la estructura del repositorio.

Los datos exportados desde PowerFactory son posteriormente utilizados por los scripts de Python para realizar el procesamiento, cálculo de indicadores y generación de resultados.

# Descripción de la metodología

La metodología desarrollada tiene como objetivo evaluar la **fortaleza de red (Grid Strength)** en sistemas eléctricos de transmisión con alta penetración de generación basada en inversores (**IBR**). El procedimiento combina estudios realizados en **DIgSILENT PowerFactory** con herramientas de procesamiento y análisis desarrolladas en **Python**.

El flujo metodológico general se divide en las siguientes etapas:

```text
Selección del sistema de prueba
            │
            ▼
Modelamiento del sistema en PowerFactory
            │
            ▼
Exportación de la matriz Ybus
            │
            ▼
Cálculo de la matriz Zbus
            │
            ▼
Identificación de nodos eléctricamente cercanos
            │
            ▼
Modelamiento de generadores basados en inversores (IBR)
            │
            ▼
Análisis de barrido de potencia
            │
            ▼
Definición de escenarios de operación
            │
            ▼
Cálculo de indicadores de fortaleza de red
            │
            ▼
Normalización y análisis comparativo
            │
            ▼
Generación de resultados y visualizaciones
```

## 1. Selección de los sistemas de prueba

La metodología se implementa utilizando los sistemas de prueba **IEEE de 9 y 39 nodos**, sin embargo es aplicable a cualquier otro sistema de pueba que pueda aportar la informacion basica para la evaluación.

Los archivos correspondientes a los sistemas de prueba se encuentran en:

```text
data/example/
├── IEEE9/
└── IEEE39/
```

## 2. Modelamiento del sistema eléctrico

Los sistemas de prueba son implementados en **DIgSILENT PowerFactory**, donde se realizan los estudios eléctricos necesarios para obtener la información utilizada posteriormente por los scripts de Python.

Para representar la generación basada en inversores se utilizan modelos de plantas fotovoltaicas basados en el modelo **WECC PVsys**. Los estudios consideran diferentes condiciones de operación y factores de potencia, incluyendo escenarios **inductivos (IND)** y **capacitivos (CAP)**.

## 3. Obtención de la matriz de impedancias

A partir del modelo de red se obtiene la matriz de admitancias nodales **Ybus**. Esta información se exporta desde PowerFactory y posteriormente se procesa mediante Python para obtener la matriz de impedancias nodales **Zbus**.

La matriz `Zbus` se utiliza como base para caracterizar las relaciones eléctricas entre los nodos del sistema.

El script relacionado con esta etapa se encuentran en:

```text
python/preprocessing/calculate_zbus.py
```

## 4. Identificación de nodos eléctricamente cercanos

Utilizando la información obtenida de `Zbus`, se determina la proximidad eléctrica entre todos los nodos de la red. De este listado se deben seleccionar los nodos electricamente cercanos en donde se modelarán manualmente las fuentes de generación basada en inversores.

Esta etapa permite identificar los nodos que presentan una mayor interacción eléctrica y que, por lo tanto, deben considerarse conjuntamente en la evaluación de la fortaleza de red.

Los resultados de este procesamiento se utilizan posteriormente para definir los grupos de generadores considerados en el cálculo de los indicadores.

El script relacionado con esta etapa se encuentran en:

```text
python/preprocessing/find_electrically_close_nodes.py
```

## 5. Determinación de los límites de operación

Se realiza un **barrido de potencia** para analizar la respuesta del sistema ante diferentes niveles de inyección de potencia activa de las fuentes IBR.

Durante este procedimiento se monitorean las variables eléctricas del sistema y se identifican los puntos asociados con los límites de operación establecidos para el estudio.

Los resultados del barrido permiten definir diferentes condiciones de operación que posteriormente son utilizadas para construir los escenarios de análisis.

Los scripts relacionados con esta etapa se encuentran en:

```text
poerfactory/python/analysis/Power Sweep IND.py
poerfactory/python/analysis/Power Sweep CAP.py
```

## 6. Definición de escenarios

Los escenarios se construyen a partir de las condiciones de operación identificadas durante el análisis de los sistemas de prueba.

Para cada sistema se consideran diferentes niveles de penetración de generación basada en inversores y condiciones de factor de potencia. Los escenarios se organizan de acuerdo con el sistema, el tipo de factor de potencia y el nivel de operación considerado.

La información correspondiente a los escenarios se encuentra en:

```text
data/scenarios/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

Cada condición contiene seis escenarios de operación, denominados `Escenario_1` a `Escenario_6`.

## 7. Cálculo de indicadores de fortaleza de red

Para cada escenario se calculan diferentes indicadores empleados en la evaluación de la fortaleza de red. La metodología propuesta para el cálculo de estos indicadores puede aplicarse a cualquier indicador que cuente con una formulación matemática sólida y cuyas ecuaciones se encuentren plenamente identificadas y definidas para su implementación.

Entre los indicadores considerados se encuentran:

* **SCR** — Short Circuit Ratio.
* **WSCR** — Weighted Short Circuit Ratio.
* **CSCR** — Composite Short Circuit Ratio.
* **GSIM** — Grid Strength Impedance Metric.
* **NRSCR** — Network Reduction Short Circuit Ratio.
* **SDSCR** — Site Depend Short Circuit Ratio.
* **λSCR** — Critical Short-Circuit Ratio.
* **K_vtg** — Voltage Support Capability Indication.

Los códigos asociados al cálculo de estos indicadores se encuentran en:

```text
python/indicators/
```

El uso de diferentes indicadores permite comparar sus respuestas ante cambios en las condiciones de operación y en la penetración de IBR.

## 8. Normalización y análisis de resultados

Los valores obtenidos para los diferentes indicadores se procesan para facilitar su comparación. Cada indicador es normalizado en funcion con su valor critico.

Posteriormente se realizan análisis comparativos y estadísticos para evaluar la relación entre los indicadores y las condiciones de operación del sistema.

Los procesos correspondientes se encuentran principalmente en:

```text
python/visualization/Indicador Comparative.py
```

## 9. Visualización de resultados

Finalmente, los resultados procesados se utilizan para generar las figuras y gráficos empleados en el análisis de la metodología.

Las herramientas de visualización se encuentran en:

```text
python/visualization/
```

Los resultados finales se almacenan en:

```text
results/
```

y se organizan de acuerdo con el sistema de prueba, la condición de operación y el tipo de escenario.

De esta manera, el repositorio permite seguir el flujo completo desde la **obtención de la información basica de la red en DIgSILENT PowerFactory**, pasando por el **procesamiento y cálculo de indicadores en Python**, hasta la **generación de los resultados y visualizaciones utilizados en el análisis**.

# Ejecución

La metodología se ejecuta mediante una secuencia de pasos que combina **DIgSILENT PowerFactory** y **Python**. El usuario debe seguir el orden establecido, ya que los resultados generados en cada etapa constituyen los archivos de entrada de las etapas posteriores.

El flujo completo de ejecución es:

```text
Modelamiento del sistema en PowerFactory
                │
                ▼
     export_network_data.py
                │
                ▼
             Ybus
                │
                ▼
         calculate_zbus.py
                │
                ▼
             Zbus
                │
                ▼
 find_electrically_close_nodes.py
                │
                ▼
     pares_nodos_cercanos.csv
                │
                ▼
 Selección de nodos para los IBR
                │
                ▼
 Modelamiento de los IBR + WECC
                │
                ▼
   Power Sweep IND.py / CAP.py
                │
                ▼
 boundary_PV1_PV2.csv
 boundary_plot_PV1_PV2.png
                │
                ▼
 Selección de puntos operativos
                │
                ▼
 Potencias_Comp_PV1_PV2.xlsx
                │
                ▼
 extract_scenario_data.py
                │
                ▼
 Información por escenario
                │
                ▼
   calculate_indicators.py
                │
                ▼
 Resultados de indicadores
                │
                ▼
 Scenario Comparative.py
                │
                ▼
 Gráficas comparativas
                │
                ▼
 Indicator Comparative.py
                │
                ▼
 Gráficas normalizadas
```

## Paso 1. Modelamiento del sistema de prueba

Inicialmente se debe disponer del modelo del sistema de prueba en **DIgSILENT PowerFactory**.

La metodología puede aplicarse a los sistemas de prueba considerados en el repositorio:

* IEEE 9 nodos.
* IEEE 39 nodos.

El modelo debe contener la información necesaria de la red eléctrica, incluyendo líneas, transformadores, generadores, cargas y demás elementos requeridos para realizar los estudios.

Los archivos de entrada asociados a cada sistema se encuentran en:

```text
data/example/
├── IEEE9/
└── IEEE39/
```

En esta etapa también se prepara el modelo de acuerdo con las condiciones de estudio requeridas.

## Paso 2. Exportación de los datos de red desde PowerFactory

Una vez preparado el modelo, se debe ejecutar internamente en **DIgSILENT PowerFactory** el script:

```text
export_network_data.py
```

El script se encuentra en:

```text
powerfactory/
```

Este script permite extraer del modelo de PowerFactory la información base de la red necesaria para las etapas posteriores, incluyendo la información utilizada para construir la matriz de admitancias nodales **Ybus**.

El script está diseñado para utilizar la estructura de directorios del repositorio. El usuario **no debe modificar el código**, excepto el nombre del ejemplo que se está procesando.

El lugar específico donde debe modificarse el nombre del ejemplo se encuentra **claramente indicado mediante comentarios dentro del propio script**.

Al finalizar la ejecución, los archivos exportados se almacenan en el directorio correspondiente dentro de:

```text
data/example/
```

Entre los archivos generados se encuentra la matriz **Ybus**, que será utilizada en el siguiente paso.

## Paso 3. Cálculo de la matriz Zbus

Con los datos exportados desde PowerFactory, se ejecuta desde Python el script:

```text
calculate_zbus.py
```

ubicado en:

```text
python/preprocessing/
```

El script utiliza la matriz **Ybus** generada en el paso anterior para calcular la matriz de impedancias nodales **Zbus**.

La matriz `Zbus` generada se almacena en la misma ruta del ejemplo dentro de:

```text
data/example/
```

Esta matriz constituye la información de entrada necesaria para identificar los nodos eléctricamente cercanos.

## Paso 4. Identificación de nodos eléctricamente cercanos

A continuación, se ejecuta desde Python:

```text
find_electrically_close_nodes.py
```

ubicado en:

```text
python/preprocessing/
```

El script utiliza la matriz **Zbus** calculada en el paso anterior para determinar las relaciones de proximidad eléctrica entre los nodos del sistema.

Como resultado, se genera el archivo:

```text
pares_nodos_cercanos.csv
```

Este archivo se almacena en la misma ruta del ejemplo:

```text
data/example/
```

El archivo contiene las parejas de nodos ordenadas de acuerdo con el criterio de proximidad eléctrica utilizado por la metodología.

## Paso 5. Selección de los nodos para los IBR

La selección de los nodos donde se instalarán las fuentes de generación basada en inversores (**IBR**) se realiza manualmente.

El usuario debe revisar:

```text
pares_nodos_cercanos.csv
```

y seleccionar dos nodos eléctricamente cercanos que serán utilizados posteriormente para ubicar los generadores IBR.

Esta selección es necesaria debido a que la metodología busca evaluar la interacción entre fuentes IBR conectadas en nodos con una relación eléctrica significativa.

## Paso 6. Modelamiento de los IBR

Una vez seleccionados los nodos, se deben incorporar los generadores basados en inversores al modelo de PowerFactory en los nodos seleccionados.

Los IBR deben utilizar un **modelo de control basado en WECC** compatible con el estudio.

En esta etapa se deben configurar los parámetros necesarios del modelo de los generadores y verificar que el sistema pueda ejecutar correctamente los estudios de flujo de potencia.

## Paso 7. Barrido de potencia

Una vez incorporados los IBR, se realizan los barridos de potencia para determinar los límites de operación del sistema.

Los scripts utilizados son:

```text
Power Sweep IND.py
Power Sweep CAP.py
```

Estos scripts se ejecutan internamente en **DIgSILENT PowerFactory**.

Los scripts corresponden a las dos condiciones de factor de potencia consideradas:

* `IND`: condición inductiva.
* `CAP`: condición capacitiva.

Para cada ejecución se debe verificar y modificar manualmente el tipo de factor de potencia de los IBR de acuerdo con el escenario que se desea analizar.

El barrido permite evaluar diferentes combinaciones de potencia de los dos IBR y determinar la región de operación admisible del sistema.

Como resultado se generan:

```text
boundary_plot_PV1_PV2.png
boundary_PV1_PV2.csv
```

Estos archivos se almacenan en la ruta correspondiente dentro de:

```text
results/
```

El archivo `boundary_plot_PV1_PV2.png` permite visualizar gráficamente la frontera de operación obtenida, mientras que `boundary_PV1_PV2.csv` contiene los datos asociados a dicha frontera.

## Paso 8. Selección de los puntos operativos

A partir de la curva:

```text
boundary_plot_PV1_PV2.png
```

el usuario debe identificar y seleccionar manualmente los puntos de operación que serán utilizados para construir los escenarios de estudio.

La selección debe considerar diferentes posiciones respecto de la frontera de operación, de acuerdo con los criterios establecidos en la metodología.

Los puntos seleccionados representan las combinaciones de potencia activa de los dos IBR que serán analizadas posteriormente.

## Paso 9. Definición de los escenarios

Los puntos operativos seleccionados deben registrarse manualmente en el archivo:

```text
Potencias_Comp_PV1_PV2.xlsx
```

ubicado en:

```text
data/scenarios/
```

Los escenarios deben definirse de manera independiente para cada condición de factor de potencia:

```text
data/scenarios/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

## Paso 10. Extracción de información para cada escenario

Una vez diligenciado el archivo `Potencias_Comp_PV1_PV2.xlsx`, se ejecuta internamente en **DIgSILENT PowerFactory** el script:

```text
extract_scenario_data.py
```

ubicado en:

```text
powerfactory/
```

Antes de ejecutar el script, se debe verificar nuevamente el tipo de factor de potencia de los generadores IBR correspondiente al conjunto de escenarios que se desea procesar.

El script lee las combinaciones de potencia definidas en:

```text
Potencias_Comp_PV1_PV2.xlsx
```

y ejecuta el procesamiento necesario para obtener la información eléctrica requerida para el cálculo posterior de los indicadores.

Para cada escenario se genera la información correspondiente al punto de operación seleccionado.

Los resultados se almacenan en:

```text
data/results/
```

organizados de acuerdo con:

```text
Sistema de prueba
    └── Tipo de factor de potencia
            └── Escenario
```

Para cada escenario se generan las diferentes carpetas de información utilizadas por los indicadores.

## Paso 11. Cálculo de los indicadores

Con la información obtenida para cada escenario, se ejecuta desde Python:

```text
calculate_indicators.py
```

ubicado en:

```text
python/indicators/
```

El script utiliza los resultados generados por el paso anterior y calcula los indicadores de fortaleza de red considerados en el estudio.

El procesamiento se realiza de manera independiente para cada escenario.

Los resultados de cada indicador se almacenan en las carpetas correspondientes a cada escenario dentro de:

```text
data/results/
```

De esta manera, los resultados quedan organizados según el sistema de prueba, el tipo de factor de potencia y el escenario analizado.

## Paso 12. Generación de gráficos comparativos por escenario

Una vez calculados los indicadores, se ejecuta desde Python el script:

```text
Scenario Comparative.py
```

ubicado en:

```text
python/visualization/
```

El script utiliza los resultados calculados para cada escenario y genera gráficos comparativos que permiten analizar simultáneamente el comportamiento de los diferentes indicadores de fortaleza de red.

Los resultados se almacenan en:

```text
results/
```

dentro del directorio correspondiente al sistema y al tipo de factor de potencia.

El script crea automáticamente la carpeta:

```text
Graficas_SCR/
```

donde se almacenan las gráficas comparativas generadas.

## Paso 13. Normalización y comparación de indicadores

Finalmente, se ejecuta desde Python el script:

```text
Indicator Comparative.py
```

ubicado en:

```text
python/visualization/
```

Este script utiliza los mismos resultados de los indicadores obtenidos para cada escenario.

Inicialmente, los valores de los indicadores son procesados y **normalizados respecto a sus valores críticos**, permitiendo comparar indicadores que presentan diferentes escalas y rangos numéricos.

Posteriormente, el script genera las representaciones gráficas utilizadas para analizar la evolución y distribución de los indicadores normalizados, incluyendo gráficos de bigotes y curvas.

Los resultados se almacenan en:

```text
results/
```

dentro del directorio correspondiente al sistema y tipo de factor de potencia.

El script crea automáticamente la carpeta:

```text
Normalized graphs/
```

donde se almacenan las figuras generadas.

# Sistemas de prueba

La metodología se implementa utilizando dos sistemas de prueba estandarizados de la literatura: el **IEEE 9-bus system** y el **IEEE 39-bus system**. Estos sistemas permiten evaluar el comportamiento de los indicadores de fortaleza de red bajo diferentes condiciones de operación y niveles de integración de generación basada en inversores (IBR).

Los archivos asociados a los sistemas de prueba se encuentran en:

```text
data/example/
├── IEEE9/
└── IEEE39/
```

## IEEE 9-bus system

El sistema IEEE de 9 nodos se utiliza como un sistema de prueba de menor tamaño para verificar el funcionamiento de la metodología y analizar la interacción entre fuentes IBR eléctricamente cercanas.

Sobre este sistema se consideran dos fuentes de generación basada en inversores, denominadas **PV1** y **PV2**, ubicadas en los nodos seleccionados mediante el procedimiento de cercania eléctrica basado en la matriz `Zbus`.

Los estudios consideran dos condiciones de factor de potencia:

* `CAP`: operación con factor de potencia capacitivo.
* `IND`: operación con factor de potencia inductivo.

Para cada condición se analizan seis escenarios de operación:

```text
IEEE9/
├── CAP/
│   ├── Escenario_1
│   ├── Escenario_2
│   ├── Escenario_3
│   ├── Escenario_4
│   ├── Escenario_5
│   └── Escenario_6
│
└── IND/
    ├── Escenario_1
    ├── Escenario_2
    ├── Escenario_3
    ├── Escenario_4
    ├── Escenario_5
    └── Escenario_6
```

## IEEE 39-bus system

El sistema IEEE de 39 nodos se utiliza como un sistema de prueba de mayor tamaño para evaluar la metodología en una red con una estructura eléctrica más compleja.

Al igual que para el sistema IEEE de 9 nodos, se incorporan dos fuentes IBR, **PV1** y **PV2**, en nodos seleccionados a partir del análisis de cercania eléctrica mediante `Zbus`.

Se consideran las mismas dos condiciones de factor de potencia:

* `CAP`: operación con factor de potencia capacitivo.
* `IND`: operación con factor de potencia inductivo.

Cada condición contiene seis escenarios de operación:

```text
IEEE39/
├── CAP/
│   ├── Escenario_1
│   ├── Escenario_2
│   ├── Escenario_3
│   ├── Escenario_4
│   ├── Escenario_5
│   └── Escenario_6
│
└── IND/
    ├── Escenario_1
    ├── Escenario_2
    ├── Escenario_3
    ├── Escenario_4
    ├── Escenario_5
    └── Escenario_6
```

## Organización de los casos de estudio

En conjunto, los sistemas de prueba permiten evaluar:

| Sistema       | Condición | Escenarios |
| ------------- | --------- | ---------: |
| IEEE 9 nodos  | CAP       |          6 |
| IEEE 9 nodos  | IND       |          6 |
| IEEE 39 nodos | CAP       |          6 |
| IEEE 39 nodos | IND       |          6 |

Por lo tanto, la metodología considera **24 condiciones de escenario** entre los dos sistemas de prueba y las dos condiciones de factor de potencia.

La información asociada a los escenarios se encuentra en:

```text
data/scenarios/
```

mientras que los datos intermedios y resultados generados durante el procesamiento se almacenan en:

```text
data/results/
```

y los resultados finales y figuras en:

```text
results/
```

Esta organización permite ejecutar y analizar cada sistema de prueba de manera independiente, manteniendo separados los escenarios correspondientes a las condiciones capacitivas e inductivas.

# Datos de entrada

La metodología utiliza diferentes archivos de datos durante las etapas de modelamiento, preprocesamiento, definición de escenarios y cálculo de indicadores. Algunos de estos archivos corresponden a **datos de entrada definidos previamente**, mientras que otros son **archivos intermedios generados automáticamente durante la ejecución**.

Los archivos se organizan principalmente en los directorios:

```text id="d2m1l9"
data/example/
data/scenarios/
data/results/
```

## 1. Datos de los sistemas de prueba

Los archivos de entrada correspondientes a los sistemas IEEE de 9 y 39 nodos se encuentran en:

```text id="1kq6qg"
data/example/
├── IEEE9/
└── IEEE39/
```

Estos directorios contienen la información necesaria para representar cada sistema de prueba y constituyen el punto de partida del flujo de procesamiento.

A partir del modelo implementado en DIgSILENT PowerFactory, se genera la información eléctrica que posteriormente será procesada mediante Python.

## 2. Archivos exportados desde PowerFactory

El script:

```text id="f1b5z8"
export_network_data.py
```

extrae desde DIgSILENT PowerFactory la información eléctrica requerida para el procesamiento posterior.

Entre los archivos generados se encuentran:

| Archivo                             | Descripción                                                             |
| ----------------------------------- | ----------------------------------------------------------------------- |
| `Ybus_export.csv`                   | Matriz de admitancias nodales utilizada para calcular la matriz `Zbus`. |
| `corrientes_generadores.csv`        | Información de las corrientes asociadas a los generadores.              |
| `tensiones_nodos.csv`               | Tensiones de los nodos del sistema.                                     |
| `potencias_activas_generadores.csv` | Potencias activas de los generadores.                                   |
| `cortocircuito_trifasico.csv`       | Información asociada al cálculo de cortocircuito trifásico.             |

Estos archivos son almacenados en el directorio correspondiente al sistema de prueba dentro de:

```text id="n5z8tq"
data/example/
```

El archivo `Ybus_export.csv` constituye la entrada principal para el cálculo de la matriz de impedancias nodales.

## 3. Matriz de impedancias `Zbus`

A partir de:

```text id="g0m6tz"
Ybus_export.csv
```

se ejecuta el script:

```text id="8byqf5"
calculate_zbus.py
```

El script calcula la matriz de impedancias nodales `Zbus` y exporta el resultado en el mismo directorio del sistema de prueba.

La matriz `Zbus` es posteriormente utilizada por:

```text id="m4h5jd"
find_electrically_close_nodes.py
```

para determinar la proximidad eléctrica entre los nodos de la red.

## 4. Pares de nodos eléctricamente cercanos

El script:

```text id="h0kn6s"
find_electrically_close_nodes.py
```

utiliza la matriz `Zbus` para identificar pares de nodos eléctricamente cercanos.

Como resultado se genera:

```text id="e2t4y7"
pares_nodos_cercanos.csv
```

Este archivo contiene las parejas de nodos obtenidas mediante el criterio de proximidad eléctrica empleado por la metodología.

El usuario debe revisar este archivo y seleccionar los dos nodos que serán utilizados posteriormente para conectar las fuentes IBR.

---

## 5. Archivo de definición de escenarios

Una vez seleccionados los nodos y realizados los barridos de potencia, los puntos de operación seleccionados se registran en:

```text id="f7v2k1"
Potencias_Comp_PV1_PV2.xlsx
```

Este archivo se utiliza para definir las combinaciones de potencia de **PV1** y **PV2** correspondientes a los diferentes escenarios de estudio.

Los escenarios se organizan según:

```text id="m5r7q3"
data/scenarios/
├── IEEE9/
│   ├── CAP/
│   └── IND/
└── IEEE39/
    ├── CAP/
    └── IND/
```

Para cada condición se consideran seis escenarios:

```text id="j2v8s4"
Escenario_1
Escenario_2
Escenario_3
Escenario_4
Escenario_5
Escenario_6
```

La información contenida en este archivo es posteriormente utilizada por `extract_scenario_data.py`.

---

## 6. Datos de cada escenario

El script:

```text id="q9s6w2"
extract_scenario_data.py
```

lee las condiciones definidas en `Potencias_Comp_PV1_PV2.xlsx` y genera la información eléctrica necesaria para el cálculo de los indicadores.

Los datos generados se almacenan en:

```text id="v3c7n1"
data/results/
```

manteniendo la organización por:

```text id="x6m4p8"
Sistema de prueba
    └── Factor de potencia
            └── Escenario
```

Dentro de cada escenario se generan diferentes grupos de información utilizados por los scripts de cálculo de indicadores.

Entre ellos se encuentran directorios relacionados con:

```text id="r8k2d5"
Datos GSIM/
ExportZ_Python/
Informacion SCR/
Positive/
SDSCR INFO/
```

Estos archivos constituyen las entradas utilizadas posteriormente por `calculate_indicators.py`.

---

## 7. Datos utilizados para el cálculo de indicadores

El script:

```text id="w4p9c6"
calculate_indicators.py
```

utiliza la información generada para cada escenario y calcula los diferentes indicadores de fortaleza de red considerados en el estudio.

Los resultados correspondientes a cada escenario se almacenan en la estructura de:

```text id="u7n3x5"
data/results/
```

Estos resultados constituyen posteriormente la entrada para los scripts de análisis y visualización.

---

## 8. Archivos utilizados para la generación de resultados

Los scripts de visualización utilizan los resultados de los indicadores calculados para generar las figuras correspondientes.

En particular:

```text id="e1r5k9"
Scenario Comparative.py
```

utiliza los resultados de los indicadores para generar las gráficas comparativas por escenario.

Posteriormente:

```text id="c6m8v2"
Indicator Comparative.py
```

utiliza los mismos resultados para realizar la normalización de los indicadores y generar las gráficas comparativas normalizadas.

Los resultados finales se almacenan en:

```text id="p4q7s1"
results/
```

organizados por sistema de prueba y condición de factor de potencia.

---

## Resumen de los archivos principales

La siguiente tabla resume los principales archivos utilizados durante el flujo de ejecución:

| Archivo                       | Generado por                                | Utilizado por                      | Función                                               |
| ----------------------------- | ------------------------------------------- | ---------------------------------- | ----------------------------------------------------- |
| `Ybus_export.csv`             | `export_network_data.py`                    | `calculate_zbus.py`                | Matriz de admitancias nodales.                        |
| `Zbus`                        | `calculate_zbus.py`                         | `find_electrically_close_nodes.py` | Matriz de impedancias nodales.                        |
| `pares_nodos_cercanos.csv`    | `find_electrically_close_nodes.py`          | Usuario                            | Identificación de nodos eléctricamente cercanos.      |
| `boundary_PV1_PV2.csv`        | `Power Sweep IND.py` / `Power Sweep CAP.py` | Usuario                            | Datos de la frontera de operación.                    |
| `boundary_plot_PV1_PV2.png`   | `Power Sweep IND.py` / `Power Sweep CAP.py` | Usuario                            | Visualización de la frontera de operación.            |
| `Potencias_Comp_PV1_PV2.xlsx` | Usuario                                     | `extract_scenario_data.py`         | Definición de los puntos operativos y escenarios.     |
| Datos por escenario           | `extract_scenario_data.py`                  | `calculate_indicators.py`          | Información eléctrica para el cálculo de indicadores. |
| Resultados de indicadores     | `calculate_indicators.py`                   | Scripts de visualización           | Valores de los indicadores para cada escenario.       |
| Gráficas comparativas         | `Scenario Comparative.py`                   | Usuario / artículo                 | Comparación de indicadores por escenario.             |
| Gráficas normalizadas         | `Indicator Comparative.py`                  | Usuario / artículo                 | Comparación normalizada de los indicadores.           |

> **Nota:** Los archivos generados durante el procesamiento no deben modificarse manualmente, excepto aquellos cuya edición se indique explícitamente en el procedimiento de ejecución, como `Potencias_Comp_PV1_PV2.xlsx`.
