# I-V Curve Filter
Link del proyecto: https://github.com/AI-GIMEL/IV-Curve-Filter.git

## Descripción

Este proyecto está diseñado para procesar curvas I-V almacenadas en una base de datos MySQL, aplicando algoritmos de ajuste y procesamiento a los datos. Utiliza un gestor de base de datos para la conexión y ejecución de consultas, y herramientas de procesamiento de curvas para analizar y ajustar los datos obtenidos.

## Estructura del Repositorio

El repositorio está estructurado de la siguiente manera:

- **src/**: Contiene el código fuente del proyecto, incluyendo el manejo de la base de datos y el procesamiento de curvas.
- **test/**: Contiene pruebas para asegurar la calidad y funcionalidad del código.
- **.gitignore**: Archivos y carpetas que deben ser ignorados por Git.
- **README.md**: Este archivo, que proporciona una descripción del proyecto y su uso.
- **poetry.lock**: Archivo generado por Poetry que bloquea las versiones de las dependencias.
- **pyproject.toml**: Archivo de configuración del proyecto que define las dependencias y otras configuraciones.

## Instalación

Para instalar y configurar el proyecto, sigue estos pasos:

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

## Uso

Para utilizar el proyecto, sigue estos pasos:

1. **Configura la base de datos MySQL**:
   - Asegúrate de que tienes una base de datos MySQL en ejecución con los datos necesarios. Actualiza las credenciales en el código fuente para conectarte a la base de datos correcta.

2. **Ejecuta el script**:
   - El script principal se encuentra en `src/`. Para procesar todas las curvas I-V almacenadas en la base de datos, ejecuta el script principal (asegurate de cambiar los parámetros correspondientes):

    ```bash
    python src/main.py
    ```

3. **Ejecuta las pruebas**:
   - Corre las pruebas para verificar la funcionalidad del código usando:

    ```bash
    pytest
    ```

## Scripts, Clases y Métodos

A continuación se describen las principales clases y métodos en el código fuente.

### Scripts

- **main.py**:
  - Procesa curvas I-V almacenadas en una base de datos MySQL.

- **ajuste_curvasIV_modelo_diodo.py**:
  - Contiene lo necesario para realizar el ajuste al modelo de un diodo de una curva I-V de un panel solar aplicando el algoritmo Nelder-Mead o fmin Scipy.
  - Cada método se explica detalladamente en el repositorio: https://github.com/AI-GIMEL/IV-Curve-Fitting.git

### Clases

#### **DatabaseManager**

- **Descripción**: Clase para manejar la conexión a la base de datos MySQL y ejecutar consultas SQL.

##### Métodos

- **`__init__(self, host, user, password, port, database='')`**:
  - *Descripción*: Inicializa una instancia de `DatabaseManager` con las credenciales de conexión.
  - *Entradas*:
    - `host` (str): La dirección del host donde se encuentra la base de datos.
    - `user` (str): El nombre de usuario para conectarse a la base de datos.
    - `password` (str): La contraseña para conectarse a la base de datos.
    - `port` (int): El puerto utilizado para la conexión a la base de datos.
    - `database` (str, opcional): El nombre de la base de datos a la cual conectarse.
  - *Salida*: Ninguna.

- **`connect(self)`**:
  - *Descripción*: Establece la conexión a la base de datos.
      - *Entradas*: Ninguna.
      - *Salida*: Ninguna.

- **`disconnect(self)`**:
  - *Descripción*: Cierra la conexión a la base de datos.
    - *Entradas*: Ninguna.
    - *Salida*: Ninguna.



- **`execute_query(self, query, params=None)`**:
  - *Descripción*: Ejecuta una consulta SQL y retorna el resultado.
  - *Entradas*: 
    - `query` (str): Consulta SQL para ejecutar.
    - `params` (tuple, optional): Parámetros opcionales para la consulta (si la consulta es parametrizada).
  - *Salida*: 
    - `tuple` (tuple): El resultado de la consulta.


#### **CurvaProcessor**

- **Descripción**: Clase para procesar curvas I-V desde la base de datos y aplicarles el ajuste al modelo de un diodo aplicando el algoritmo Nelder-Mead.

##### Métodos

- **`__init__(self, db_manager)`**:
  - *Descripción*: Inicializa la clase con una instancia de `DatabaseManager` para manejar las consultas SQL.
    - *Entradas*: Ninguna.
    - *Salida*: Ninguna.

- **`procesar_todas_las_curvas(self)`**:
  - *Descripción*: Procesa todas las curvas I-V almacenadas en la base de datos, aplicando ajustes y almacenando los resultados.
      - *Entradas*: Ninguna.
    - *Salida*: Ninguna

- **`procesar_curva(self, resultados, timestamp)`**:
  - *Descripción*: Procesa una curva I-V específica, convierte los datos JSON a formato utilizable y aplica un ajuste utilizando el modelo de diodo.
    - *Entradas*: Ninguna.
    - *Salida*: Ninguna

### Ejemplo de Uso

Proporciona ejemplos de cómo instanciar las clases y llamar a los métodos. Por ejemplo:

```python

# Conectar a la base de datos
db_manager = DatabaseManager(
    host='localhost',
    user='root',
    password='tu_contraseña',
    port=3306,
    database='tu_BBDD'
)
db_manager.connect()

# Procesar todas las curvas I-V
procesador_curvas = CurvaProcessor(db_manager)
procesador_curvas.procesar_todas_las_curvas()

# Desconectar de la base de datos
db_manager.disconnect()

