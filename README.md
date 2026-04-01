# I-V Curve Filter
Link del proyecto: https://github.com/AI-GIMEL/IV-Curve-Filter.git

## Descripción

Este proyecto está diseñado para procesar curvas I-V (Corriente-Voltaje) de paneles solares almacenadas en una base de datos MySQL. Aplica algoritmos de filtrado y ajuste al modelo de un diodo, calculando los parámetros eléctricos característicos de cada curva. El sistema está integrado con **Apache Airflow** para la automatización y orquestación del flujo de procesamiento, y se despliega mediante **Docker** para garantizar portabilidad y reproducibilidad.

El flujo general del sistema es el siguiente:
1. Los datos de curvas I-V, capturados por analizadores físicos (`AnP01`, `AnP02`, etc.) y almacenados como archivos `.parquet`, se registran en una base de datos MySQL.
2. El script principal recupera las curvas de la base de datos, aplica filtros de calidad y realiza el ajuste al modelo de un diodo utilizando los algoritmos `fmin` (scipy), `Nelder-Mead` o un enfoque híbrido.
3. Los parámetros del ajuste y los parámetros solares calculados se almacenan de nuevo en la base de datos, en sus respectivas tablas.

## Estructura del Repositorio

El repositorio está estructurado de la siguiente manera:

```
IV-Curve-Filter/
├── src/
│   ├── queries/                         # Archivos SQL para consultas y creación de tablas
│   │   ├── contar_filas.sql
│   │   ├── crear_tablas.sql
│   │   ├── curvas_restantes.sql
│   │   ├── guardar_parametros_ajuste.sql
│   │   ├── guardar_parametros_promediados.sql
│   │   ├── guardar_parametros_solares.sql
│   │   ├── obtener_analizadores.sql
│   │   ├── obtener_curvas_con_start_id.sql
│   │   ├── obtener_curvas_sin_start_id.sql
│   │   ├── obtener_id_path.sql
│   │   └── ultima_curva_procesada.sql
│   └── scripts/                         # Código fuente principal
│       ├── ajuste_curvasIV_modelo_diodo.py
│       ├── credential_handler.py
│       ├── curva_processor.py
│       ├── data.py
│       ├── database_handler.py
│       ├── main.py
│       ├── parametros_promediados.py
│       ├── parametros_solar.py
│       └── sql_handler.py
├── dags/
│   └── IV_curve_filter_dag.py           # DAG de Apache Airflow
├── notebooks/
│   ├── filtrado..ipynb                  # Notebook de análisis exploratorio
│   └── parametros_ajuste_nelder.csv     # Resultados de ajuste exportados
├── config/                              # Configuración de Airflow
├── logs/                                # Logs generados en ejecución
├── plugins/                             # Plugins de Airflow (vacío)
├── test/
│   ├── __init__.py
│   ├── main.py
│   └── test_main.py                     # Pruebas unitarias
├── .env                                 # Variables de entorno
├── Dockerfile                           # Imagen Docker personalizada (basada en Airflow)
├── docker-compose.yml                   # Orquestación de servicios con Docker Compose
├── pyproject.toml                       # Configuración de dependencias con Poetry
├── poetry.lock                          # Versiones bloqueadas de dependencias
├── gitignore                            # Archivos ignorados por Git
└── README.md                            # Este archivo
```

### Descripción de los directorios principales

- **`src/scripts/`**: Contiene el código fuente del proyecto, incluyendo el manejo de la base de datos, el procesamiento de curvas y el algoritmo de ajuste.
- **`src/queries/`**: Contiene los archivos `.sql` utilizados como plantillas para generar consultas dinámicas.
- **`dags/`**: Contiene el DAG de Apache Airflow que automatiza la ejecución del script principal.
- **`test/`**: Contiene pruebas unitarias para asegurar la calidad y funcionalidad del código.
- **`notebooks/`**: Contiene un notebook de Jupyter para análisis y exploración interactiva de los datos.
- **`.env`**: Archivo de variables de entorno requerido por Docker Compose (e.g., `AIRFLOW_UID`).
- **`Dockerfile`**: Define la imagen Docker personalizada basada en `apache/airflow:2.10.5`, con las dependencias del proyecto instaladas.
- **`docker-compose.yml`**: Orquesta todos los servicios necesarios: Airflow (webserver, scheduler, worker, triggerer), PostgreSQL y Redis.
- **`poetry.lock`**: Archivo generado por Poetry que bloquea las versiones de las dependencias.
- **`pyproject.toml`**: Archivo de configuración del proyecto que define las dependencias y otras configuraciones.

## Instalación

### Opción 1: Instalación local con Poetry

Para instalar y configurar el proyecto localmente, sigue estos pasos:

1. **Clona el repositorio**:

    ```bash
    git clone https://github.com/AI-GIMEL/IV-Curve-Filter.git
    ```

2. **Accede a la carpeta del proyecto**:

    ```bash
    cd IV-Curve-Filter
    ```

3. **Instala las dependencias**:

    El proyecto utiliza [Poetry](https://python-poetry.org/) para la gestión de dependencias. Instala las dependencias con:

    ```bash
    poetry install
    ```

4. **(Opcional) Activa el entorno virtual de Poetry**:

    ```bash
    poetry shell
    ```

### Opción 2: Despliegue con Docker y Apache Airflow

El proyecto está configurado para correr como un servicio de Apache Airflow usando Docker Compose con el executor `CeleryExecutor`.

1. **Clona el repositorio** (igual que en la opción 1).

2. **Crea el archivo `.env`** en la raíz del proyecto con el `AIRFLOW_UID` correspondiente:

    ```bash
    echo "AIRFLOW_UID=$(id -u)" > .env
    ```

3. **Configura las credenciales de la base de datos**:

    Crea un archivo `db_creds.json` en la carpeta `../.credenciales` (un nivel arriba del repositorio) con el siguiente formato:

    ```json
    {
        "host": "host.docker.internal",
        "user": "tu_usuario",
        "password": "tu_contraseña",
        "database": "db_siu",
        "port": 3306
    }
    ```

4. **Construye e inicia los contenedores**:

    ```bash
    docker-compose up --build -d
    ```

5. **Accede a la interfaz de Airflow**:

    Abre `http://localhost:8081` en tu navegador. Las credenciales por defecto son `airflow` / `airflow`.

6. **Crea la red de Docker** (si no existe):

    ```bash
    docker network create custom_bridge_network
    ```

### Dependencias del proyecto

Las dependencias principales definidas en `pyproject.toml` son:

| Paquete                  | Versión       | Uso                                               |
|--------------------------|---------------|---------------------------------------------------|
| `python`                 | `^3.12`       | Versión mínima de Python                          |
| `mysql-connector-python` | `^9.0.0`      | Conector para MySQL/MariaDB                       |
| `pymysql`                | `^1.1.1`      | Driver MySQL alternativo                          |
| `scipy`                  | `^1.14.1`     | Algoritmos de optimización (`fmin`, `fsolve`)     |
| `numpy`                  | `^2.1.1`      | Operaciones numéricas y álgebra lineal            |
| `pandas`                 | `^2.2.2`      | Lectura de archivos Parquet y manipulación de datos |
| `matplotlib`             | `^3.9.2`      | Generación de gráficas de curvas I-V             |
| `pyarrow`                | `^19.0.0`     | Backend para lectura de archivos `.parquet`       |
| `pytest`                 | `^8.3.3`      | Framework de pruebas                              |
| `pytest-mock`            | `^3.14.0`     | Extensión de mocking para pytest                  |

## Uso

### Ejecución local

Para utilizar el proyecto localmente, sigue estos pasos:

1. **Configura la base de datos MySQL**:
   - Asegúrate de que tienes una base de datos MySQL en ejecución con los datos necesarios.
   - Crea el archivo de credenciales en la ruta definida por `data.CREDENTIALES_DIR` (por defecto `/opt/airflow/credenciales/db_creds.json`).
   - Actualiza la variable `CREDENTIALES_DIR` en `src/scripts/data.py` si tu ruta es diferente.

2. **Ejecuta el script**:
   - El script principal se encuentra en `src/scripts/`. Para procesar todas las curvas I-V almacenadas en la base de datos, ejecuta el script principal (asegúrate de cambiar los parámetros correspondientes):

    ```bash
    python src/scripts/main.py
    ```

3. **Ejecuta las pruebas**:
   - Corre las pruebas para verificar la funcionalidad del código usando:

    ```bash
    pytest
    ```

### Ejecución con Apache Airflow (Docker)

1. Una vez iniciados los contenedores, accede a la UI de Airflow en `http://localhost:8081`.
2. Activa el DAG llamado `iv_curve_filter_single_run` desde la interfaz web.
3. Dispara una ejecución manual del DAG haciendo clic en el botón **Trigger DAG**.
4. El DAG ejecutará el comando `python /opt/airflow/src/scripts/main.py` dentro del contenedor worker.

### Configuración de tablas en la base de datos

Al iniciarse, el script crea automáticamente las tablas necesarias en la base de datos si no existen. Las tablas definidas en `src/queries/crear_tablas.sql` son:

| Tabla                         | Constante en `data.py`              | Descripción                                              |
|-------------------------------|-------------------------------------|----------------------------------------------------------|
| `Parametros_Metodologia1`     | `PARAMETERS_SOLAR_TABLE`            | Parámetros solares calculados por promedios (Metodología 1) |
| `Parametros_Metodologia2`     | `PARAMETERS_SOLAR_ELEKTRA_TABLE`    | Parámetros solares calculados por ajuste polinomial (Metodología 2) |
| `Resultados_Ajuste`           | `RESULTADOS_AJUSTE_TABLE`           | Parámetros del ajuste al modelo de un diodo              |
| `Curvas`                      | `CURVAS_TABLE`                      | Tabla de referencia con las rutas a los archivos de curvas (preexistente) |

## Scripts, Clases y Métodos

A continuación se describen las principales clases y métodos en el código fuente.

### Scripts

- **`src/scripts/main.py`**:
  - Script de punto de entrada del proyecto. Carga las credenciales de la base de datos, establece la conexión, inicializa las tablas y lanza el procesamiento de todas las curvas I-V mediante `CurvaProcessor`.
  - Contiene también la función auxiliar `recorrer_curvas_desde()` para procesar archivos `.parquet` directamente desde el sistema de archivos a partir de una fecha y hora específica.

- **`src/scripts/ajuste_curvasIV_modelo_diodo.py`**:
  - Contiene lo necesario para realizar el ajuste al modelo de un diodo de una curva I-V de un panel solar aplicando el algoritmo Nelder-Mead o fmin Scipy.
  - Cada método se explica detalladamente en el repositorio: https://github.com/AI-GIMEL/IV-Curve-Fitting.git

- **`src/scripts/data.py`**:
  - Módulo de constantes globales. Define los nombres de las tablas de la base de datos y la ruta al directorio de credenciales. Actúa como punto de configuración central para evitar valores hardcodeados en el código.

### Clases

#### **DatabaseHandler**

- **Descripción**: Clase para manejar la conexión a la base de datos MySQL y ejecutar consultas SQL. Es el único componente que interactúa directamente con el conector de MySQL. Configura automáticamente el sistema de logging al importarse.

##### Métodos

- **`__init__(self, host, user, password, database, port=3306)`**:
  - *Descripción*: Inicializa una instancia de `DatabaseHandler` con las credenciales de conexión.
  - *Entradas*:
    - `host` (str): La dirección del host donde se encuentra la base de datos.
    - `user` (str): El nombre de usuario para conectarse a la base de datos.
    - `password` (str): La contraseña para conectarse a la base de datos.
    - `database` (str): El nombre de la base de datos a la cual conectarse.
    - `port` (int, opcional): El puerto utilizado para la conexión a la base de datos. Por defecto es `3306`.
  - *Salida*: Ninguna.

- **`connect(self)`**:
  - *Descripción*: Establece la conexión a la base de datos MySQL.
    - *Entradas*: Ninguna.
    - *Salida*: Ninguna.

- **`disconnect(self)`**:
  - *Descripción*: Cierra la conexión a la base de datos.
    - *Entradas*: Ninguna.
    - *Salida*: Ninguna.

- **`execute_query(self, query, params=None)`**:
  - *Descripción*: Ejecuta una consulta SQL (SELECT, INSERT, UPDATE, DELETE) y retorna el resultado para consultas SELECT. Realiza `commit` automáticamente para consultas de escritura.
  - *Entradas*:
    - `query` (str): Consulta SQL para ejecutar.
    - `params` (tuple, opcional): Parámetros opcionales para la consulta parametrizada.
  - *Salida*:
    - `list`: Lista de tuplas con los resultados (para consultas SELECT). `None` para otras operaciones.

- **`execute_script(self, script_string)`**:
  - *Descripción*: Ejecuta un bloque de texto que contiene múltiples sentencias SQL separadas por punto y coma. Utiliza `multi=True` del cursor de MySQL. Ideal para ejecutar archivos `.sql` completos como el de creación de tablas.
  - *Entradas*:
    - `script_string` (str): La cadena de texto con las sentencias SQL a ejecutar.
  - *Salida*: Ninguna.

- **`execute_many(self, query, data_list)`**:
  - *Descripción*: Ejecuta múltiples inserciones (INSERT) en la base de datos en una sola operación usando `executemany`. Más eficiente que múltiples llamadas a `execute_query` para inserciones masivas.
  - *Entradas*:
    - `query` (str): La consulta SQL INSERT a ejecutar.
    - `data_list` (list of tuple): Lista de tuplas con los datos para insertar.
  - *Salida*: Ninguna.

- **`fetch_one(self, query, params=None)`**:
  - *Descripción*: Ejecuta una consulta SELECT y devuelve únicamente el primer registro encontrado.
  - *Entradas*:
    - `query` (str): La consulta SQL SELECT a ejecutar.
    - `params` (tuple, opcional): Parámetros para la consulta preparada.
  - *Salida*:
    - `tuple`: El primer registro obtenido, o `None` si no hay resultados.

- **`start_transaction(self)`**:
  - *Descripción*: Inicia explícitamente una transacción en la base de datos.
    - *Entradas*: Ninguna.
    - *Salida*: Ninguna.

- **`commit(self)`**:
  - *Descripción*: Confirma (commit) la transacción activa en la base de datos.
    - *Entradas*: Ninguna.
    - *Salida*: Ninguna.

- **`rollback(self)`**:
  - *Descripción*: Revierte (rollback) la transacción activa en caso de error.
    - *Entradas*: Ninguna.
    - *Salida*: Ninguna.

---

#### **CurvaProcessor**

- **Descripción**: Clase para procesar curvas I-V desde la base de datos y aplicarles el ajuste al modelo de un diodo. Orquesta la recuperación de datos, la aplicación de filtros de calidad y el guardado de resultados. Depende de `DatabaseHandler`, `SQLHandler`, `SolarParameterCalculator` y `MeanParameterCalculator`.

##### Métodos

- **`__init__(self, db_handler)`**:
  - *Descripción*: Inicializa la clase con un `DatabaseHandler` para manejar las consultas SQL. Instancia internamente un `SQLHandler`.
  - *Entradas*:
    - `db_handler` (DatabaseHandler): Una instancia activa de `DatabaseHandler`.
  - *Salida*: Ninguna.

- **`procesar_todas_las_curvas(self, metodo=None, ruta_guardado=None)`**:
  - *Descripción*: Procesa todas las curvas I-V en orden: por analizador (AnP01, AnP02, ...) y por fecha (de más antigua a más reciente). Si la tabla `Resultados_Ajuste` está vacía, comienza desde el primer analizador. Si no, retoma desde la última curva procesada y avanza al siguiente analizador cuando termina el actual.
  - *Entradas*:
    - `metodo` (str, opcional): Método de ajuste a utilizar. Puede ser `'fmin'`, `'nelder'` o `'hibrido'`.
    - `ruta_guardado` (str, opcional): Ruta del directorio donde se guardarán los archivos CSV y PNG generados.
  - *Salida*:
    - `str` o `None`: Retorna el ID de la última curva procesada si ocurrió un error, o `None` si todo se procesó correctamente.

- **`procesar_curva_db(self, path_list, db_handler, metodo=None, ruta_guardado=None)`**:
  - *Descripción*: Procesa una curva I-V específica leyendo su archivo `.parquet`, aplicando los filtros de calidad y ejecutando el ajuste. Guarda los parámetros solares en la base de datos independientemente de si la curva pasa o no los filtros.

    **Filtros aplicados (en orden)**:
    1. **Filtro horario**: Descarta curvas fuera del rango 6:30–17:30.
    2. **Vmpp > Voc**: Descarta curvas donde el voltaje en el punto de máxima potencia supera el voltaje de circuito abierto.
    3. **Impp > Isc**: Descarta curvas donde la corriente en el punto de máxima potencia supera la corriente de cortocircuito.
    4. **Coeficiente de Pearson ≤ 0.6**: Descarta curvas con baja correlación lineal entre voltaje y corriente (curvas malformadas).

  - *Entradas*:
    - `path_list` (list): Lista de tuplas `(path_archivo, id_curva)` de los archivos a procesar.
    - `db_handler` (DatabaseHandler): Instancia de `DatabaseHandler`.
    - `metodo` (str, opcional): Método de ajuste (`'fmin'`, `'nelder'`, `'hibrido'`).
    - `ruta_guardado` (str, opcional): Ruta donde se guardarán los resultados.
  - *Salida*: Ninguna.

- **`procesar_curva_por_id(self, nombre_archivo, metodo, ruta_guardado)`**:
  - *Descripción*: Procesa una única curva I-V buscando su ruta en la base de datos a partir del nombre del archivo `.parquet`. Aplica el ajuste y guarda los resultados en un CSV e imagen PNG.
  - *Entradas*:
    - `nombre_archivo` (str): Nombre del archivo `.parquet` a procesar (ej: `'AnP03_25.01.30_15.00.10.parquet'`).
    - `metodo` (str): Método de ajuste a utilizar.
    - `ruta_guardado` (str): Directorio donde se guardarán los resultados.
  - *Salida*: Ninguna.

- **`procesar_curva_con_filtros_CSV(self, nombre_archivo, metodo, ruta_guardado)`**:
  - *Descripción*: Similar a `procesar_curva_por_id` pero con aplicación explícita de los 4 filtros de calidad. Retorna un diccionario con el estado del procesamiento, permitiendo al llamador conocer si la curva fue ajustada o descartada y los parámetros calculados en cualquier caso.
  - *Entradas*:
    - `nombre_archivo` (str): Nombre del archivo `.parquet` a procesar.
    - `metodo` (str): Método de ajuste a utilizar.
    - `ruta_guardado` (str): Directorio donde se guardarán los resultados.
  - *Salida*:
    - `dict`: Diccionario con claves `'status'` (`'ajustado'` o `'filtrado'`), `'resultados_ajuste'`, `'parametros_solares'`, `'parametros_promediados'` y `'coef_pearson'`. Retorna `None` si la curva está fuera del rango horario.

---

#### **AnalizadorCurvaIV**

- **Descripción**: Clase de bajo nivel para analizar y ajustar curvas I-V al modelo de un diodo. Implementa los algoritmos de optimización numérica. Contiene la implementación propia del algoritmo Nelder-Mead.

##### Métodos

- **`__init__(self)`**:
  - *Descripción*: Inicializa el objeto con valores predeterminados. La tensión térmica (`Vt`) se fija en `0.03875220203` V.
  - *Entradas*: Ninguna.
  - *Salida*: Ninguna.

- **`ajustar(self, V_rango, I_rango, P, metodo='fmin')`**:
  - *Descripción*: Método principal de ajuste. Delega al método específico según el parámetro `metodo`.
  - *Entradas*:
    - `V_rango` (list): Lista de voltajes medidos.
    - `I_rango` (list): Lista de corrientes medidas.
    - `P` (list): Lista de potencias calculadas.
    - `metodo` (str): `'fmin'`, `'nelder'` o `'hibrido'`.
  - *Salida*:
    - `tuple`: `(data_ajustada, res_ajuste, metodo_usado, error)`.

- **`ajuste_fmin(self, V_rango, I_rango)`**:
  - *Descripción*: Ajusta la curva I-V utilizando el método de optimización `scipy.optimize.fmin` (método simplex de Nelder-Mead de Scipy), con máximo de 10,000 evaluaciones de función.
  - *Entradas*:
    - `V_rango` (list): Lista de voltajes.
    - `I_rango` (list): Lista de corrientes.
  - *Salida*:
    - `tuple`: `(data_fmin, res_fmin)` donde `data_fmin` es un array numpy de dimensiones (N, 2) con voltajes y corrientes ajustadas, y `res_fmin` son los parámetros óptimos `[I_ph, I_s, n_d, R_s, R_p]`.

- **`ajuste_nelder(self, V_rango, I_rango)`**:
  - *Descripción*: Ajusta la curva I-V utilizando la implementación propia del algoritmo Nelder-Mead (`self.Nelder_Mead()`), con un mínimo de 1,000 y máximo de 10,000 iteraciones y tolerancia de `1e-8`.
  - *Entradas*:
    - `V_rango` (list): Lista de voltajes.
    - `I_rango` (list): Lista de corrientes.
  - *Salida*:
    - `tuple`: `(data_nelder, res_nelder)`.

- **`ajuste_hibrido(self, V_rango, I_rango)`**:
  - *Descripción*: Ejecuta primero `ajuste_fmin`. Si el error del resultado es ≤ 1 o ≥ 500, acepta el resultado de `fmin`. En caso contrario (error entre 1 y 500), considera que el ajuste de `fmin` no fue satisfactorio y aplica `ajuste_nelder` como segundo intento.
  - *Entradas*:
    - `V_rango` (list): Lista de voltajes.
    - `I_rango` (list): Lista de corrientes.
  - *Salida*:
    - `tuple`: `(data_ajustada, res_ajuste, metodo_usado, error)`.

- **`Dat_init1(self, V_rango, I_rango)`**:
  - *Descripción*: Calcula los parámetros iniciales `X_0 = [I_ph, I_s, n_d, R_s, R_p]` para el proceso de optimización usando interpolación lineal de la curva y estimaciones analíticas.
  - *Entradas*:
    - `V_rango` (list): Lista de voltajes.
    - `I_rango` (list): Lista de corrientes.
  - *Salida*:
    - `tuple`: `(X_0, Xv)` donde `X_0` son los valores iniciales y `Xv` son sus nombres.

- **`CurvaS_003b(self, X)`**:
  - *Descripción*: Función objetivo de mínimos cuadrados (norma L2 del residuo) para el modelo de diodo. Esta es la función que los algoritmos de optimización minimizan. Si algún parámetro es negativo, aplica una penalización de 1000.
  - *Entradas*:
    - `X` (list): Parámetros del modelo `[I_ph, I_s, n_d, R_s, R_p]`.
  - *Salida*:
    - `float`: El valor del error (norma del residuo).

- **`CurvaS_004a(self, X, rV)`**:
  - *Descripción*: Calcula la corriente teórica para cada voltaje en `rV` dados los parámetros del modelo, resolviendo la ecuación implícita del diodo using `scipy.optimize.fsolve`.
  - *Entradas*:
    - `X` (list): Parámetros del modelo ajustado `[I_ph, I_s, n_d, R_s, R_p]`.
    - `rV` (list): Lista de voltajes para los cuales calcular la corriente.
  - *Salida*:
    - `list`: Lista de valores de corriente calculados.

- **`Nelder_Mead(self, CurvaS_003b, X, MinI, MaxI, ToleranciaF)`**:
  - *Descripción*: Implementación propia del algoritmo de Nelder-Mead. Minimiza la función `CurvaS_003b` a partir de condiciones iniciales `X` usando operaciones de reflexión, extensión, contracción y encogimiento sobre un símplex de N+1 vértices.
  - *Entradas*:
    - `CurvaS_003b` (function): Función objetivo a minimizar.
    - `X` (array_like): Valores iniciales `[I_ph, I_s, n_d, R_s, R_p]`.
    - `MinI` (int): Número mínimo de iteraciones (típicamente 1000).
    - `MaxI` (int): Número máximo de iteraciones (típicamente 10000).
    - `ToleranciaF` (float): Tolerancia para la convergencia (típicamente `1e-8`).
  - *Salida*:
    - `tuple`: `(Minimo, FunValor, contador)` donde `Minimo` son los parámetros óptimos, `FunValor` es el error en el mínimo y `contador` el número de iteraciones.

- **`completar_curvaIV(self, V_rango, res_fmin, data_file_path)`**:
  - *Descripción*: Extiende la curva I-V ajustada hasta el voltaje de circuito abierto (`Voc`) leído del archivo original, generando 100 puntos adicionales con `np.linspace`. Recorta la extensión en el punto donde la corriente se vuelve ≤ 0.
  - *Entradas*:
    - `V_rango` (list): Lista de voltajes medidos.
    - `res_fmin` (list): Parámetros del ajuste.
    - `data_file_path` (str): Ruta al archivo CSV que contiene el valor de `Voc`.
  - *Salida*:
    - `tuple`: `(V_extra, I_extra)` listas de voltajes y corrientes extendidos.

---

#### **Recorrer_dia**

- **Descripción**: Clase de orquestación de alto nivel para procesar un conjunto de archivos de curvas I-V de un día o período. Coordina el ajuste, el guardado en CSV y base de datos, y la generación de gráficas.

##### Métodos

- **`__init__(self, metodo, analizador, dia, db_client)`**:
  - *Descripción*: Inicializa la clase con el método de ajuste, el identificador del analizador y la fecha de procesamiento.
  - *Entradas*:
    - `metodo` (str): Método de ajuste (`'fmin'`, `'nelder'` o `'hibrido'`).
    - `analizador` (str): Identificador del analizador (ej: `'AnP03'`).
    - `dia` (str): Fecha/hora en formato string (ej: `'2021-06-08 12:39:10'`).
    - `db_client`: Cliente de la base de datos (`DatabaseHandler`).
  - *Salida*: Ninguna.

- **`guardar_parametros_en_csv(analizador, file_name, X_0, res_ajuste, data_ajustada, path_to_save, metodo_usado, error_metodo, Isc)`** *(estático)*:
  - *Descripción*: Guarda los parámetros iniciales y finales del ajuste, el coeficiente de Pearson, el método usado y el error en un archivo CSV de forma acumulativa (modo `append`).
  - *Salida*: Ninguna.

- **`guardar_parametros_en_db(self, id_curva, X_0, res_ajuste, data_ajustada, db_handler, metodo_usado, error)`**:
  - *Descripción*: Guarda los resultados del ajuste en la tabla `Resultados_Ajuste` de la base de datos. Calcula los coeficientes de Pearson y Spearman sobre la curva ajustada antes de insertar.
  - *Salida*: Ninguna.

- **`procesar_archivo(self, V_rango, I_rango, P, output_csv_path, output_png_path, name_archivo, Isc)`**:
  - *Descripción*: Procesa una curva I-V aplicando el ajuste, guardando los parámetros en CSV y generando la gráfica PNG correspondiente.
  - *Salida*:
    - `tuple`: `(V_rango, I_rango, data_ajustada, res_ajuste)`.

- **`procesar_archivo_db(self, V_rango, I_rango, P, db_handler, output_png_path, name_archivo)`**:
  - *Descripción*: Similar a `procesar_archivo` pero guarda los resultados directamente en la base de datos usando `guardar_parametros_en_db`.
  - *Salida*: Ninguna.

---

#### **SolarParameterCalculator**

- **Descripción**: Clase para calcular parámetros solares clave (Voc, Isc, Pmax, Vmpp, Impp, FF) a partir de los datos crudos de voltaje y corriente usando ajuste polinomial de grado 6 (Metodología 2 - Elektra).

##### Métodos

- **`calcular_parametros_solares(V, I)`** *(estático)*:
  - *Descripción*: Calcula los parámetros solares mediante ajuste polinomial de grado 6 sobre la potencia P = V·I para encontrar el punto de máxima potencia, y ajuste lineal sobre los primeros 10 puntos para estimar Isc.
  - *Entradas*:
    - `V` (list): Lista de voltajes.
    - `I` (list): Lista de corrientes.
  - *Salida*:
    - `list`: `[FF, Voce, Isc, Pmax, Vmax, Imax, Vmin, Imin]`.

- **`insertar_parametros_solares(self, analizador, datetime, parametros_solares)`**:
  - *Descripción*: Inserta los parámetros solares calculados en la tabla `Parametros_Metodologia2` de la base de datos, junto con el identificador del analizador y la fecha/hora.
  - *Entradas*:
    - `analizador` (str): Identificador del analizador.
    - `datetime` (datetime): Fecha y hora de la medición.
    - `parametros_solares` (list): Lista con los parámetros `[Voc, FF, Voce, Isc, Pmax, Vmpp, Impp, Vmin, Imin]`.
  - *Salida*: Ninguna.

---

#### **MeanParameterCalculator**

- **Descripción**: Clase para calcular parámetros solares usando promedios sobre los extremos de la curva (Metodología 1). Más sencilla y robusta que el ajuste polinomial, ideal para curvas con ruido.

##### Métodos

- **`calcular_parametros_promediados(V, I)`** *(estático)*:
  - *Descripción*: Calcula Pmax como el máximo directo de P = V·I, Vmpp e Impp en ese índice, Voc como el voltaje máximo donde |I| ≤ 10% de Isc, Isc como el promedio de los primeros 3 puntos de corriente, y FF como `(Vmpp·Impp)/(Voce·Isc)`.
  - *Entradas*:
    - `V` (list): Lista de voltajes.
    - `I` (list): Lista de corrientes.
  - *Salida*:
    - `list`: `[FF, Voce, Isc, Pmax, Vmpp, Impp, Vmin, Imin]`.

- **`insertar_parametros_promediados(self, analizador, datetime, parametros_solares)`**:
  - *Descripción*: Inserta los parámetros solares calculados en la tabla `Parametros_Metodologia1` de la base de datos.
  - *Entradas*:
    - `analizador` (str): Identificador del analizador.
    - `datetime` (datetime): Fecha y hora de la medición.
    - `parametros_solares` (list): Lista de parámetros calculados.
  - *Salida*: Ninguna.

---

#### **SQLHandler**

- **Descripción**: Clase utilitaria para leer archivos `.sql` y generar consultas SQL dinámicas reemplazando marcadores de posición `{nombre_parametro}` con los valores del diccionario provisto.

##### Métodos

- **`__init__(self, sql_script_path)`**:
  - *Descripción*: Inicializa el manejador con la ruta a la carpeta de scripts SQL.
  - *Entradas*:
    - `sql_script_path` (str): Ruta relativa o absoluta a la carpeta de archivos `.sql`.
  - *Salida*: Ninguna.

- **`generar_query_sql(self, script_path, params)`**:
  - *Descripción*: Lee el archivo `.sql` especificado y reemplaza los marcadores `{clave}` con los valores del diccionario `params` usando `.format(**params)`. Devuelve la cadena SQL lista para ejecutar.
  - *Entradas*:
    - `script_path` (str): Ruta completa al archivo `.sql`.
    - `params` (dict): Diccionario con los valores a sustituir en la plantilla SQL.
  - *Salida*:
    - `str`: Consulta SQL con los parámetros sustituidos.

---

#### **CredentialHandler**

- **Descripción**: Clase para cargar credenciales desde archivos JSON. Separa la configuración sensible del código fuente, permitiendo que las credenciales sean inyectadas via volumen Docker o variables de entorno.

##### Métodos

- **`__init__(self, credentials_dir)`**:
  - *Descripción*: Inicializa el manejador con el directorio donde se encuentran los archivos de credenciales.
  - *Entradas*:
    - `credentials_dir` (str): Ruta al directorio que contiene los archivos JSON de credenciales.
  - *Salida*: Ninguna.

- **`load_db_credentials(self)`**:
  - *Descripción*: Carga las credenciales de la base de datos desde el archivo `db_creds.json` ubicado en `credentials_dir`.
  - *Entradas*: Ninguna.
  - *Salida*:
    - `dict`: Diccionario con claves `host`, `user`, `password`, `database` y opcionalmente `port`.

- **`load_server_credentials(self)`**:
  - *Descripción*: Carga las credenciales del servidor desde el archivo `server_creds.json`.
  - *Entradas*: Ninguna.
  - *Salida*:
    - `dict`: Diccionario con las credenciales del servidor.

### Ejemplo de Uso

Proporciona ejemplos de cómo instanciar las clases y llamar a los métodos. Por ejemplo:

```python

# Conectar a la base de datos
db_manager = DatabaseHandler(
    host='localhost',
    user='root',
    password='tu_contraseña',
    port=3306,
    database='tu_BBDD'
)
db_manager.connect()

# Procesar todas las curvas I-V con método híbrido
procesador_curvas = CurvaProcessor(db_manager)
procesador_curvas.procesar_todas_las_curvas(
    metodo='hibrido',
    ruta_guardado='/ruta/para/guardar/resultados'
)

# Procesar una curva específica por nombre de archivo
procesador_curvas.procesar_curva_por_id(
    nombre_archivo='AnP03_25.01.30_15.00.10.parquet',
    metodo='nelder',
    ruta_guardado='/ruta/para/guardar/resultados'
)

# Desconectar de la base de datos
db_manager.disconnect()
```
