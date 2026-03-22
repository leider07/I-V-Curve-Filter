import os
import mysql.connector
import logging

class SQLHandler:
    def __init__(self, sql_script_path: str):
        """
        Inicializa el manejador de consultas SQL.

        Args:
            queries_folder (str): Nombre de la carpeta donde se almacenan los archivos .sql.
            db_client: Cliente de la base de datos para ejecutar consultas.
        """
        # Obtener la ruta absoluta a la carpeta de consultas
        self._queries_folder = "/home/leider/Escritorio/curve_filter/IV-Curve-Filter/src/queries"
        #self._client = db_client
        self.sql_script_path = sql_script_path
        self.connection = None

    def ejecutar_script_sql(self, connection, params, script_name):
        """
        Lee y ejecuta un archivo SQL que contiene los comandos para crear la base de datos,
        reemplazando los marcadores de posición con los valores proporcionados en `params`.
        :param connection: Objeto de conexión a la base de datos.
        :param params: Diccionario con los parámetros a reemplazar en el script SQL.
        :param script_name: Nombre del archivo SQL a ejecutar.
        :return: None
        """
        script_name_sql = script_name.split('\\')[-1] # Nombre del archivo .sql a ejecutar

        logging.info(f"Ejecutando script SQL en '{script_name_sql}'.")

        cursor = connection.cursor()  # Crea un cursor para ejecutar consultas
        try:
            with open(script_name, 'r') as file:
                sql_script = file.read()  # Leer el contenido del archivo SQL
                #print(sql_script)

            # Reemplazar los marcadores de posición con los valores del diccionario
            sql_script_formateado = sql_script.format(**params)

            # Dividir el script en comandos individuales
            sql_commands = sql_script_formateado.split(';')

            for command in sql_commands:
                command = command.strip()  # Eliminar espacios innecesarios
                if command:
                    cursor.execute(command)  # Ejecutar el comando SQL
                    connection.commit()  # Confirmar la transacción
                    
        except mysql.connector.Error as err:

            connection.rollback()  # Revierte la transacción en caso de error
        finally:
            cursor.close()  # Cierra el cursor después de ejecutar los comandos
    
    def generar_query_sql(self, script_path: str, params: dict):
        """Lee un archivo .sql, reemplaza los parámetros de la plantilla y devuelve la consulta resultante.

        Args:
            script_path (str): Ruta del archivo .sql a leer.
            params (dict): Diccionario con los valores a reemplazar en la plantilla.

        Returns:
            str: Consulta SQL con los parámetros sustituidos.
        """
        # print(params)
        # f = open("/media/leider/Respaldo/Documentos/curve_filter/IV-Curve-Filter/src/queries/guardar_parametros_en_db.sql", 'r')
        # try:
        #     for i in f:
        #         print(i)
        # finally:
        #     f.close()

        # Leer el contenido del archivo SQL y reemplazar los marcadores de posición con los valores proporcionados
        with open(script_path, 'r') as file:
            sql_script = file.read().format(**params)

        # Retornar la consulta generada
        return sql_script
    