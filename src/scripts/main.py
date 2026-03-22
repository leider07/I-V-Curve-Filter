import os
import data
import logging
from database_handler import DatabaseHandler
from sql_handler import SQLHandler
from credential_handler import CredentialHandler  # Asumo que existe
from curva_processor import CurvaProcessor

def inicializar_base_de_datos(db_handler, sql_handler):
    """
    Prepara y ejecuta la consulta SQL para crear las tablas de la base de datos,
    siguiendo el patrón de la aplicación.
    """
    try:
        logging.info("Verificando y creando tablas de la base de datos si es necesario...")
        
        # 1. Parámetros para reemplazar en el archivo SQL
        param_crear_tablas = {
            'table_parameters_metodologia1': data.PARAMETERS_SOLAR_TABLE,
            'table_parameters_metodologia2': data.PARAMETERS_SOLAR_ELEKTRA_TABLE,
            'table_resultados_ajuste': data.RESULTADOS_AJUSTE_TABLE,
            'table_curvas': data.CURVAS_TABLE,
        }

        # 2. Ruta al archivo SQL
        script_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
        script_crear_tablas = os.path.join(script_dir, 'crear_tablas.sql')

        # 3. Generar la consulta SQL final reemplazando los parámetros
        query_crear_tablas = sql_handler.generar_query_sql(script_crear_tablas, param_crear_tablas)

        # 4. Ejecutar la consulta generada
        db_handler.execute_script(query_crear_tablas)

        logging.info("Las tablas de la base de datos están listas.")
    except Exception as e:
        logging.error(f"No se pudo inicializar la base de datos: {e}")
        raise

def main():
    try:
        logging.info("Iniciando ejecución del script.")

        # Configuración de paths
        #current_dir = os.path.dirname(os.path.abspath(__file__))
        #project_root = os.path.dirname(os.path.dirname(current_dir))
        #credenciales_dir = os.path.join(project_root, "..", ".credenciales")

        # Ruta absoluta a las credenciales en Airflow
        credenciales_dir = data.CREDENTIALES_DIR

        # Carga de credenciales
        cred_handler = CredentialHandler(credenciales_dir)
        db_creds = cred_handler.load_db_credentials()

        # Conexión a la base de datos
        db_handler = DatabaseHandler(
            host=db_creds['host'],
            user=db_creds['user'],
            password=db_creds['password'],
            database=db_creds['database'],
            port=db_creds.get('port', 3306)
        )

        # Conectar a la base de datos
        db_handler.connect()
        sql_handler = SQLHandler(sql_script_path="../queries")

        inicializar_base_de_datos(db_handler, sql_handler)

        # Procesamiento
        processor = CurvaProcessor(db_handler)

        from datetime import datetime

        def recorrer_curvas_desde(directorio_base, analizador, fecha_inicio, processor):
            """
            Recorre las curvas I-V desde una fecha y hora específicas, procesando todos los archivos desde ese punto en adelante.
            
            Args:
                directorio_base (str): Ruta base donde están las carpetas organizadas por año/mes/día.
                analizador (str): Identificador del analizador, por ejemplo 'AnP04'.
                fecha_inicio (str): Nombre del archivo parquet desde donde quieres comenzar. Ejemplo: 'AnP04_25.02.01_06.30.09.parquet'.
                processor (obj): Objeto que procesa la curva.
            
            Returns:
                None
            """
            # Extraer la fecha y hora inicial
            nombre_sin_ext = fecha_inicio.replace('.parquet', '')
            partes = nombre_sin_ext.split('_')
            fecha_hora = '_'.join(partes[1:])  # Toma desde el segundo elemento en adelante
            fecha_inicio_dt = datetime.strptime(fecha_hora, '%y.%m.%d_%H.%M.%S')

            archivos_a_procesar = []

            # Recorremos los años
            for año in sorted(os.listdir(directorio_base)):
                path_año = os.path.join(directorio_base, año)
                if not os.path.isdir(path_año):
                    continue

                # Recorremos los meses
                for mes in sorted(os.listdir(path_año)):
                    path_mes = os.path.join(path_año, mes)
                    if not os.path.isdir(path_mes):
                        continue

                    # Recorremos los días
                    for dia in sorted(os.listdir(path_mes)):
                        path_dia = os.path.join(path_mes, dia)
                        if not os.path.isdir(path_dia):
                            continue

                        # Listamos todos los archivos parquet en el día
                        archivos = [f for f in os.listdir(path_dia) if f.endswith('.parquet') and f.startswith(analizador)]

                        # Ordenamos los archivos por nombre (lo cual ordena cronológicamente por cómo están nombrados)
                        for archivo in sorted(archivos):
                            nombre_sin_ext = archivo.replace('.parquet', '')
                            partes = nombre_sin_ext.split('_')
                            fecha_hora_archivo = '_'.join(partes[1:])
                            fecha_archivo_dt = datetime.strptime(fecha_hora_archivo, '%y.%m.%d_%H.%M.%S')

                            # Solo procesamos si la fecha y hora del archivo es igual o posterior a la fecha de inicio
                            if fecha_archivo_dt >= fecha_inicio_dt:
                                ruta_archivo = os.path.join(path_dia, archivo)
                                archivos_a_procesar.append(ruta_archivo)

            print(f"Total de archivos a procesar: {len(archivos_a_procesar)}")

            for archivo_path in archivos_a_procesar:
                archivo = os.path.basename(archivo_path)

                try:
                    print(f"Procesando archivo: {archivo}")
                    processor.procesar_curva_con_filtros(
                        nombre_archivo=archivo,
                        metodo='hibrido',
                        ruta_guardado='/home/leider/Documentos/prueba_final_airflow'
                    )
                except Exception as e:
                    print(f"Error procesando archivo {archivo}: {e}")
                    continue  # Si hay error, continúa con el siguiente archivo
            
        directorio_base = '/home/solarudea/Projects/SolarInformation/Analyzers/PanelAnalyzers/AnP03/Data'
        analizador = 'AnP03'
        fecha_inicio = 'AnP03_21.03.08_15.58.09.parquet'

        #recorrer_curvas_desde(directorio_base, analizador, fecha_inicio, processor)

        # Procesar todas las curvas en la base de datos
        processor.procesar_todas_las_curvas(
            metodo='hibrido',
            ruta_guardado='/home/leider/Documentos/prueba_final_airflow'
        )

        # # Procesar una curva específica
        # processor.procesar_curva_por_id(
        #     nombre_archivo='AnP03_25.01.30_15.00.10.parquet',
        #     metodo='nelder',
        #     ruta_guardado='/home/leider/Descargas'
        # )

    #     directorio = '/home/solarudea/Projects/SolarInformation/Analyzers/PanelAnalyzers/AnP04/Data/2025/01/30'

    #     # Prefijo del día que quieres procesar
    #     prefijo = 'AnP04_25.01.30'

    #     # Listar todos los archivos que empiezan con el prefijo
    #     archivos_a_procesar = [
    #         archivo for archivo in os.listdir(directorio)
    #         if archivo.startswith(prefijo) and archivo.endswith('.parquet')
    #     ]

    #     print(len(archivos_a_procesar))

    #     for archivo in sorted(archivos_a_procesar):
    #         print(f"Procesando archivo: {archivo}")
    #         processor.procesar_curva_con_filtros(
    #             nombre_archivo=archivo,
    #             metodo='hibrido',
    #             ruta_guardado='/home/leider/Descargas/filtrado_pearson/AnP04/AnP04_ajustada_filtro'
    # )

        # Procesar una curva aplicando filtros
        # processor.procesar_curva_con_filtros(
        #     nombre_archivo='AnP03_21.06.08_12.39.10.parquet',
        #     metodo='hibrido',
        #     ruta_guardado='/home/leider/Descargas/'
        # )

    except Exception as e:
        logging.error(f"Error durante la ejecución: {str(e)}", exc_info=True)
        raise
    finally:
        if 'db_handler' in locals():
            db_handler.disconnect()
            logging.info("Desconectado de la base de datos.")
        logging.info("Ejecución finalizada.")

if __name__ == "__main__":
    main()