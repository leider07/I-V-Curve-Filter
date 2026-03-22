import mysql.connector
from mysql.connector import Error
import logging
import os

# Configuración básica del logging
current_dir = os.path.dirname(os.path.abspath(__file__))    
log_folder = os.path.join(current_dir, "..", "..", "logs")

logging.basicConfig(
    level=logging.INFO,                                  # Nivel mínimo de los mensajes que se registrarán
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato de los mensajes
    handlers=[
        logging.FileHandler(os.path.join(log_folder, 'log_ajuste_curvasIV_modelo_diodo.log')),  # Guardar logs en un archivo
        logging.StreamHandler()                                                    # Mostrar logs en la consola
    ]
)

class DatabaseHandler:
    """
    Clase para manejar conexiones y operaciones con una base de datos MySQL.
    """

    def __init__(self, host, user, password, database, port=3306):
        """
        Inicializa el manejador de base de datos.

        Args:
            host (str): Dirección IP o nombre del servidor de base de datos.
            user (str): Usuario para la autenticación en la base de datos.
            password (str): Contraseña del usuario.
            database (str): Nombre de la base de datos a la que se conectará.
            port (int, optional): Puerto del servidor MySQL, por defecto 3306.
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None

    def connect(self):
        """
        Establece la conexión con la base de datos MySQL.

        Raises:
            mysql.connector.Error: Si ocurre un error al conectar con la base de datos.
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            if self.connection.is_connected():
                logging.info(f"Conexión exitosa a la base de datos {self.database} en {self.host}.")
        except Error as e:
            logging.error(f"Error al conectar a la base de datos: {e}")
            raise

    def disconnect(self):
        """
        Cierra la conexión con la base de datos MySQL.
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logging.info("Conexión con la base de datos cerrada.")

    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta SQL (SELECT, INSERT, UPDATE, DELETE, etc.) en la base de datos.

        Args:
            query (str): La consulta SQL a ejecutar.
            params (tuple, optional): Parámetros para consultas preparadas.

        Returns:
            result (list): Resultados de la consulta SELECT, si aplica.

        Raises:
            mysql.connector.Error: Si ocurre un error al ejecutar la consulta.
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            if query.strip().lower().startswith("select"):
                result = cursor.fetchall()
                return result
            else:
                self.connection.commit()
                #logging.info("Consulta ejecutada correctamente.")
        except Error as e:
            logging.error(f"Error al ejecutar la consulta: {e}")
            raise
        finally:
            cursor.close()
    # Dentro de la clase DatabaseHandler

    def execute_script(self, script_string):
        """Ejecuta un bloque de texto que contiene múltiples sentencias SQL.

        Este método es ideal para ejecutar archivos .sql completos, como los
        utilizados para la creación inicial de tablas en la base de datos.
        Utiliza la opción 'multi=True' del cursor para manejar varias
        sentencias separadas por punto y coma.

        Args:
            script_string (str): La cadena de texto con las sentencias SQL a ejecutar.

        Returns:
            None

        Raises:
            Exception: Re-lanza la excepción original del conector de la base
                    de datos si ocurre un error durante la ejecución del script.
        """
        if not self.connection:
            logging.error("No hay conexión para ejecutar el script.")
            raise ConnectionError("Intento de ejecutar un script sin una conexión activa.")

        cursor = None
        try:
            cursor = self.connection.cursor()
            # La clave es multi=True, que maneja la sincronización de comandos.
            for result in cursor.execute(script_string, multi=True):
                # No es necesario procesar los resultados, solo asegurar su ejecución.
                pass
            self.connection.commit()
            logging.info("Script ejecutado y cambios confirmados correctamente.")
        except Exception as e:
            logging.error(f"Error al ejecutar el script SQL: {e}")
            if self.connection:
                self.connection.rollback() # Deshacer cambios si hay un error.
            raise # Vuelve a lanzar la excepción para que sea manejada por el código que llamó al método.
        finally:
            if cursor:
                cursor.close()

    def execute_many(self, query, data_list):
        """
        Ejecuta múltiples inserciones (INSERT) en la base de datos en una sola operación.

        Args:
            query (str): La consulta SQL a ejecutar.
            data_list (list of tuple): Lista de tuplas con los datos para insertar.

        Raises:
            mysql.connector.Error: Si ocurre un error al ejecutar la operación.
        """
        cursor = self.connection.cursor()
        try:
            cursor.executemany(query, data_list)
            self.connection.commit()
            logging.info(f"{cursor.rowcount} registros insertados correctamente.")
        except Error as e:
            logging.error(f"Error al ejecutar las inserciones: {e}")
            raise
        finally:
            cursor.close()

    def start_transaction(self):
        """
        Inicia una transacción en la base de datos.
        """
        self.connection.start_transaction()
        logging.info("Transacción iniciada.")

    def commit(self):
        """
        Confirma (commit) la transacción en la base de datos.
        """
        self.connection.commit()
        logging.info("Transacción confirmada.")

    def rollback(self):
        """
        Revierte (rollback) la transacción en caso de error.
        """
        self.connection.rollback()
        logging.info("Transacción revertida.")

    def fetch_one(self, query, params=None):
        """
        Ejecuta una consulta SELECT y devuelve un solo registro.

        Args:
            query (str): La consulta SQL a ejecutar.
            params (tuple, optional): Parámetros para la consulta preparada.

        Returns:
            result (tuple): El primer registro obtenido.

        Raises:
            mysql.connector.Error: Si ocurre un error al ejecutar la consulta.
        """
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result
        except Error as e:
            logging.info(f"Error al ejecutar la consulta: {e}")
            raise
        finally:
            cursor.close()
