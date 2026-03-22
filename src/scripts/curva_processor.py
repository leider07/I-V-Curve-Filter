from ajuste_curvasIV_modelo_diodo import *
from database_handler import *
from credential_handler import *
from sql_handler import SQLHandler
from datetime import datetime, time
import data
import os
import logging 
import pandas as pd
from parametros_solar import SolarParameterCalculator
from parametros_promediados import MeanParameterCalculator

class CurvaProcessor:
    """
    Una clase para procesar curvas I-V desde la base de datos y aplicarles un ajuste.

    Métodos:
        procesar_todas_las_curvas(start_id=None):
            Procesa todas las curvas en la base de datos, comenzando desde un ID específico.
        procesar_curva_db(path_list, db_handler):
            Procesa una curva I-V específica y aplica el ajuste.
        procesar_curva_por_id(id_curva, metodo, ruta_guardado):
            Procesa una sola curva I-V aplicando el ajuste y guardando los parametros en un csv y guarda la imagen en la ruta especificada

    Atributos:
        db_handler (DatabaseHandler): Una instancia de DatabaseHandler para manejar las consultas SQL.
    """

    def __init__(self, db_handler):
        """
        Inicializa la clase con un DatabaseHandler para manejar las consultas SQL.

        Args:
            db_handler (DatabaseHandler): Una instancia de DatabaseHandler.
        """
        self.db_handler = db_handler
        self.sql_handler = SQLHandler(sql_script_path="../queries")

    def procesar_todas_las_curvas(self, metodo=None, ruta_guardado=None):
        """
        Procesa todas las curvas en orden: por analizador (AnP01, AnP02...) y por fecha (antigua -> reciente).
        Si la tabla resultados_ajuste está vacía, comienza desde AnP01.
        Si no, continúa desde el último punto y pasa al siguiente analizador cuando sea necesario.
        """

        # 1. Verificar si resultados_ajuste está vacío
        param_check_empty_query = {'tabla': data.RESULTADOS_AJUSTE_TABLE,}

        script_dir_check_empty_query = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
        script_check_empty_query = os.path.join(script_dir_check_empty_query, 'contar_filas.sql')
        query_check_empty_query = self.sql_handler.generar_query_sql(script_check_empty_query, param_check_empty_query)
        is_empty = self.db_handler.execute_query(query_check_empty_query, param_check_empty_query)[0][0] == 0

        # 2. Obtener todos los analizadores ordenados (AnP01, AnP02...)
        param_obtener_analizadores = {'tabla_curvas': data.CURVAS_TABLE, 
                                      'analizador': 'Analizador',}

        script_dir_obtener_analizadores = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
        script_obtener_analizadores = os.path.join(script_dir_obtener_analizadores, 'obtener_analizadores.sql')

        query_obtener_analizadores = self.sql_handler.generar_query_sql(script_obtener_analizadores, param_obtener_analizadores)

        analizadores = [a[0] for a in self.db_handler.execute_query(query_obtener_analizadores, param_obtener_analizadores)]

        if not analizadores:
            logging.error("No hay analizadores en la tabla Curvas")
            return None

        # 3. Determinar por dónde empezar
        if is_empty:
            # Caso 1: Tabla vacía -> comenzar desde el primer analizador (ejemplo: AnP01)
            analizador_actual = analizadores[0]
            start_id = None  # Procesar todo el analizador desde el inicio

        else:
            param_ultima_curva_procesada = {'tabla_resultados_ajuste': data.RESULTADOS_AJUSTE_TABLE,
                                            'analizador': 'Analizador',
                                            'datetime': 'Datetime',}
            
            script_dir_ultima_curva_procesada = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
            script_ultima_curva_procesada = os.path.join(script_dir_ultima_curva_procesada, 'ultima_curva_procesada.sql')
            query_ultima_curva_procesada = self.sql_handler.generar_query_sql(script_ultima_curva_procesada, param_ultima_curva_procesada)
            ultima_curva_procesada = self.db_handler.execute_query(query_ultima_curva_procesada, param_ultima_curva_procesada)
            
            if ultima_curva_procesada:
                analizador_actual, ultima_fecha, ultimo_id = ultima_curva_procesada[0]

                param_curvas_restantes = {'tabla_curvas': data.CURVAS_TABLE,
                                          'path_archivo': 'Path_Archivo',
                                          'analizador': 'Analizador', 
                                          'datetime': 'Datetime',}
                
                param_insertar_curvas_restantes = (analizador_actual,
                                                   ultima_fecha)
                
                script_dir_curvas_restantes = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
                script_curvas_restantes = os.path.join(script_dir_curvas_restantes, 'curvas_restantes.sql')
                query_curvas_restantes = self.sql_handler.generar_query_sql(script_curvas_restantes, param_curvas_restantes)

                siguiente_curva = self.db_handler.execute_query(query_curvas_restantes, param_insertar_curvas_restantes)
                
                if siguiente_curva:
                    start_id = siguiente_curva[0][1] #hice cambi [0][0] por [0][1]
                else:
                    # Pasar al siguiente analizador
                    idx_actual = analizadores.index(analizador_actual)
                    if idx_actual + 1 < len(analizadores):
                        analizador_actual = analizadores[idx_actual + 1]
                        start_id = None  # Comenzar desde el inicio del nuevo analizador
                    else:
                        logging.info("Ya se procesaron todas las curvas de todos los analizadores")
                        return None
            else:
                # Fallback: comenzar desde el primer analizador
                analizador_actual = analizadores[0]
                start_id = None

        # 4. Procesar los analizadores en orden
        idx_analizador = analizadores.index(analizador_actual)
        for analizador in analizadores[idx_analizador:]:
            logging.info(f"Procesando analizador: {analizador}")
            
            # Consulta base para obtener curvas del analizador actual
            if start_id:

                param_curvas_con_start_id = {'tabla_curvas': data.CURVAS_TABLE,
                                            'path_archivo': 'Path_Archivo',
                                            'analizador': 'Analizador',
                                            'datetime': 'Datetime',}
                
                analizador_procesar, fecha_str = start_id.split('_', 1)
        
                # Convertir la parte de fecha/hora a datetime
                fecha_procesar = datetime.strptime(fecha_str, '%y.%m.%d_%H.%M.%S')

                script_dir_curvas_con_start_id = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
                script_curvas_con_start_id = os.path.join(script_dir_curvas_con_start_id, 'obtener_curvas_con_start_id.sql')
                query_curvas = self.sql_handler.generar_query_sql(script_curvas_con_start_id, param_curvas_con_start_id)
                params= (analizador_procesar, fecha_procesar)

            else:
                param_curvas_sin_start_id = {'tabla_curvas': data.CURVAS_TABLE,
                                            'analizador': 'Analizador',
                                            'datetime': 'Datetime',
                                            'path_archivo': 'Path_Archivo',}
                script_dir_curvas_sin_start_id = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
                script_curvas_sin_start_id = os.path.join(script_dir_curvas_sin_start_id, 'obtener_curvas_sin_start_id.sql')
                query_curvas = self.sql_handler.generar_query_sql(script_curvas_sin_start_id, param_curvas_sin_start_id)
                params = (analizador,)

            curvas_bad = self.db_handler.execute_query(query_curvas, params)

            def actualizar_rutas(curvas):
                nuevas_curvas = []
                for ruta_original, id_curva in curvas:
                    # Extraer los componentes de la ruta
                    partes = ruta_original.split('/')
                    
                    # Obtener los elementos importantes (AnPXX, año, mes, día, nombre archivo)
                    analizador = next(p for p in partes if p.startswith('AnP'))
                    fecha_partes = id_curva.split('_')[1].split('.')
                    año = f"20{fecha_partes[0]}"
                    mes = fecha_partes[1]
                    dia = fecha_partes[2]
                    nombre_archivo = os.path.basename(ruta_original)
                    
                    # Construir la nueva ruta
                    nueva_ruta = os.path.join(
                        #'/home/solarudea/Projects/SolarInformation/Analyzers/PanelAnalyzers',
                        '/opt/airflow/data/analyzers/PanelAnalyzers', # Ruta modificada para Airflow
                        analizador,
                        'Data',
                        año,
                        mes,
                        dia,
                        nombre_archivo
                    )
                    
                    nuevas_curvas.append((nueva_ruta, id_curva))
                
                return nuevas_curvas
            
            curvas = actualizar_rutas(curvas_bad)

            if not curvas:
                logging.warning(f"No hay curvas para el analizador {analizador}")
                continue

            # Procesar cada curva
            for id_curva, path_archivo in curvas:
                try:
                    self.procesar_curva_db([(path_archivo, id_curva)], self.db_handler, metodo, ruta_guardado)
                    last_processed = id_curva
                except Exception as e:
                    logging.error(f"Error al procesar {id_curva}: {str(e)}")
                    # Opción: retornar last_processed para reanudar luego
                    return last_processed if 'last_processed' in locals() else None

        logging.info("Procesamiento completado")
        return None  # Todo se procesó correctamente

    def procesar_curva_db(self, path_list, db_handler, metodo=None, ruta_guardado=None):
        """
        Procesa una curva I-V específica aplicando filtros antes del ajuste.
        
        Filtros aplicados:
        1. Solo entre 6:30am y 5:30pm
        2. No ajustar si Vmpp > Voc
        3. No ajustar si Impp > Isc
        4. No ajustar si coeficiente de Pearson > 0.6 o coeficiente de Pearson == -1

        Args:
            path_list (list): Lista de tuplas (ID_Curva, Path_Archivo) de archivos a procesar.
            db_handler (DatabaseHandler): Instancia de DatabaseHandler para manejar las consultas SQL.
            metodo (str): Método de ajuste a utilizar ('fmin' o 'nelder').
            ruta_guardado (str): Ruta donde se guardarán los resultados.

        Returns:
            None
        """
        for id_curva, path in path_list:
            # Extraer el analizador del ID_Curva (los primeros 5 caracteres)
            analizador = id_curva[:5]  # Por ejemplo, "AnP03"

            # Leer el archivo Parquet
            data = pd.read_parquet(path)

            # Extraer el valor de Voc del archivo Parquet
            voc_value = None
            for row in data.itertuples(index=False):
                
                if isinstance(row[0], str) and row[0] == "Voc":
                    try:
                        voc_value = float(row[1])  # Tomar directamente el valor de la segunda columna
                        break
                    except (ValueError, TypeError):
                        print(f"Error al convertir Voc a float: {row[1]}")

            # Extraer las columnas de voltaje y corriente, omitiendo las primeras 6 filas
            Voltaje = data['Medicion Analizador PCB Raspberry Pi 2'][6:].tolist()
            Corriente = data['Unnamed: 1'][6:].tolist()

            # Obtener la fecha del archivo y convertirla a formato datetime
            date_str = data.iloc[2]['Medicion Analizador PCB Raspberry Pi 2']
            datetime = pd.to_datetime(date_str)
            datetime_str = str(datetime)

            # Convertir los datos a listas de floats
            voltaje = [float(v) for v in Voltaje]
            corriente = [float(c) for c in Corriente]

            # Calcular los parámetros solares
            parametros_solares = SolarParameterCalculator.calcular_parametros_solares(voltaje, corriente)

            # Calcular los parámetros solares usando metodología de Cesar (promediados)
            parametros_solares_promediados = MeanParameterCalculator.calcular_parametros_promediados(voltaje, corriente)

            # Añadir el valor de Voc en la primera posición de parametros_solares
            if voc_value is not None:
                parametros_solares.insert(0, voc_value)
                parametros_solares_promediados.insert(0, voc_value)

            else:
                logging.warning(f"No se encontró el valor de Voc en el archivo {id_curva}.")

            #logging.info(f"Parámetros solares (Metodología 1) calculados para {id_curva}: {parametros_solares}")
            #logging.info(f"Parámetros solares (Metodología 2) calculados para {id_curva}: {parametros_solares_promediados}")

            # Encontrar el índice del voltaje mínimo
            Vmin_index = voltaje.index(min(voltaje))

            # Definir el rango de voltaje y corriente a partir del voltaje mínimo
            V_rango = voltaje[Vmin_index:]
            I_rango = corriente[Vmin_index:]

            # Calcular la potencia
            P = [v * i for v, i in zip(V_rango, I_rango)]

            # Filtrado antes de procesar

            try:
                isc = parametros_solares[3]
                voc = parametros_solares[0]
                impp = parametros_solares[6]
                vmpp = parametros_solares[5]
            except IndexError:
                logging.error(f"Error extrayendo parámetros para filtros en la curva {id_curva}. Se omite.")
                return

            filtros_pasados = True

            # Filtro 1: Rango Horario 
            try:
                # Extraer la parte de la fecha del ID de la curva
                fecha_str = id_curva.split('_', 1)[1]
                fecha_procesar = pd.to_datetime(fecha_str, format='%y.%m.%d_%H.%M.%S')
                
                hora_curva = fecha_procesar.time()
                if not (time(6, 30) <= hora_curva <= time(17, 30)):
                    logging.info(f"FILTRADO: Curva {id_curva} fuera del rango horario (6:30-17:30).")
                    return 
            except (ValueError, IndexError) as e:
                logging.warning(f"No se pudo parsear la fecha del ID: {id_curva}. Error: {e}. Saltando filtro horario.")
                return
            
            # Filtro 2: Vmpp > Voc
            if vmpp > voc:
                logging.info(f"FILTRADO: Curva {id_curva} descartada. Motivo: Vmpp ({vmpp:.2f}) > Voc ({voc:.2f}).")
                filtros_pasados = False
            
            # Filtro 3: Impp > Isc
            if impp > isc:
                logging.info(f"FILTRADO: Curva {id_curva} descartada. Motivo: Impp ({impp:.2f}) > Isc ({isc:.2f}).")
                filtros_pasados = False

            # Filtro 4: Coeficiente de Pearson
            coef_pearson, _ = pearsonr(V_rango, I_rango)
            if (abs(coef_pearson) <= 0.6):
                logging.info(f"FILTRADO: Curva {id_curva} descartada. Motivo: Coef. Pearson ({coef_pearson:.3f}) <= 0.6.")
                filtros_pasados = False

            if not filtros_pasados:

                guardar_parametros_solares = SolarParameterCalculator(db_handler)
                guardar_parametros_solares.insertar_parametros_solares(analizador, datetime, parametros_solares)

                guardar_parametros_promediados = MeanParameterCalculator(db_handler)
                guardar_parametros_promediados.insertar_parametros_promediados(analizador, datetime, parametros_solares_promediados)

                return 

            # Procesar la curva con Recorrer_dia
            procesador = Recorrer_dia(metodo=metodo, analizador=analizador, dia=datetime_str, db_client=db_handler)
            procesador.procesar_archivo_db(
                V_rango,
                I_rango,
                P,
                db_handler,
                ruta_guardado,
                datetime_str
            )

            guardar_parametros_solares = SolarParameterCalculator(db_handler)
            guardar_parametros_solares.insertar_parametros_solares(analizador, datetime, parametros_solares)

            guardar_parametros_promediados = MeanParameterCalculator(db_handler)
            guardar_parametros_promediados.insertar_parametros_promediados(analizador, datetime, parametros_solares_promediados)

            logging.info(f"Curva con ID_Curva {id_curva} procesada correctamente.")
    
    def procesar_curva_por_id(self, nombre_archivo, metodo, ruta_guardado):
        """
        Procesa una curva I-V específica basada en su ID_Curva y aplica el ajuste.

        Args:
            id_curva (str): El ID_Curva de la curva a procesar.
            metodo (str): Método de ajuste a utilizar.
            ruta_guardado (str): Directorio donde se guardarán los resultados.

        Returns:
            None
        """
        import data
        from datetime import datetime

        nombre_archivo = nombre_archivo.replace('.parquet', '')

        analizador_procesar, fecha_str = nombre_archivo.split('_', 1)
        fecha_procesar = datetime.strptime(fecha_str, '%y.%m.%d_%H.%M.%S')
        fecha_param = fecha_procesar.strftime('%Y-%m-%d %H:%M')

        print(f"Analizador: {analizador_procesar}, Fecha: {fecha_procesar}")


        # Parámetros para la consulta SQL
        param_obtener_path_archivo = {
            'tabla_curvas': data.CURVAS_TABLE,
            'path_archivo': 'Path_Archivo',
            'analizador': 'Analizador',
            'datetime': 'Datetime',
        }

        # Ruta al archivo SQL
        script_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
        script_obtener_path_archivo = os.path.join(script_dir, 'obtener_id_path.sql')

        # Generar la consulta SQL
        query_obtener_path_archivo = self.sql_handler.generar_query_sql(script_obtener_path_archivo, param_obtener_path_archivo)

        # Ejecutar la consulta para obtener el Path_Archivo de la curva específica
        return_query_path = self.db_handler.execute_query(query_obtener_path_archivo, params=(analizador_procesar, fecha_param))

        curvas_validas = [
        (ruta[0], os.path.basename(ruta[0]).replace('.parquet', ''))
        for ruta in return_query_path
    ]  

        def actualizar_rutas(curvas):
                nuevas_curvas = []
                for ruta_original, id_curva in curvas:
                    # Extraer los componentes de la ruta
                    partes = ruta_original.split('/')
                    
                    # Obtener los elementos importantes (AnPXX, año, mes, día, nombre archivo)
                    analizador = next(p for p in partes if p.startswith('AnP'))
                    fecha_partes = id_curva.split('_')[1].split('.')
                    año = f"20{fecha_partes[0]}"
                    mes = fecha_partes[1]
                    dia = fecha_partes[2]
                    nombre_archivo = os.path.basename(ruta_original)
                    
                    # Construir la nueva ruta
                    nueva_ruta = os.path.join(
                        '/home/solarudea/Projects/SolarInformation/Analyzers/PanelAnalyzers',
                        analizador,
                        'Data',
                        año,
                        mes,
                        dia,
                        nombre_archivo
                    )
                    
                    nuevas_curvas.append((nueva_ruta, id_curva))
                
                return nuevas_curvas

        path = actualizar_rutas(curvas_validas)
        print(curvas_validas)

        id_curva = nombre_archivo
        path = path[0][0]

        try:
            # Extraer el analizador del ID_Curva (los primeros 5 caracteres)
            analizador = id_curva[:5]  

            # Leer el archivo Parquet
            data = pd.read_parquet(path)

            # Extraer Voc del archivo
            voc_value = None
            for row in data.itertuples(index=False):
                if isinstance(row[0], str) and row[0] == "Voc":
                    try:
                        voc_value = float(row[1])
                        break
                    except (ValueError, TypeError):
                        print(f"Error al convertir Voc a float: {row[1]}")

            # Extraer las columnas de voltaje y corriente, omitiendo las primeras 6 filas
            Voltaje = data['Medicion Analizador PCB Raspberry Pi 2'][6:].tolist()
            Corriente = data['Unnamed: 1'][6:].tolist()

            # Obtener la fecha del archivo y convertirla a formato datetime
            date_str = data.iloc[2]['Medicion Analizador PCB Raspberry Pi 2']
            datetime = pd.to_datetime(date_str)
            datetime_str = str(datetime)

            # Convertir los datos a listas de floats
            voltaje = [float(v) for v in Voltaje]
            corriente = [float(c) for c in Corriente]

            # Encontrar el índice del voltaje mínimo
            Vmin_index = voltaje.index(min(voltaje))

            # Definir el rango de voltaje y corriente a partir del voltaje mínimo
            V_rango = voltaje[Vmin_index:]
            I_rango = corriente[Vmin_index:]

            # Calcular la potencia
            P = [v * i for v, i in zip(V_rango, I_rango)]

                        # Calcular parámetros solares
            parametros_solares = SolarParameterCalculator.calcular_parametros_solares(V_rango, I_rango)
            parametros_solares_promediados = MeanParameterCalculator.calcular_parametros_promediados(V_rango, I_rango)

            # Añadir el valor de Voc en la primera posición de parametros_solares
            if voc_value is not None:
                parametros_solares.insert(0, voc_value)
                parametros_solares_promediados.insert(0, voc_value)
            
            Isc = parametros_solares[3] 

            # Procesar la curva con Recorrer_dia
            procesador = Recorrer_dia(metodo=metodo, analizador=analizador, dia=datetime_str, db_client=self.db_handler)
            procesador.procesar_archivo(
                V_rango,
                I_rango,
                P,
                ruta_guardado,
                ruta_guardado,
                datetime_str,
                Isc
            )

            logging.info(f"Curva con ID_Curva {id_curva} procesada correctamente.")

        except Exception as e:
            logging.error(f"Error al procesar la curva con ID_Curva {id_curva}: {e}")
            raise

    def procesar_curva_con_filtros_CSV(self, nombre_archivo, metodo, ruta_guardado):
        """
        Procesa una curva I-V específica aplicando filtros antes del ajuste.
        
        Filtros aplicados:
        1. Solo entre 6:30am y 5:30pm
        2. No ajustar si Vmpp > Voc
        3. No ajustar si Impp > Isc
        4. No ajustar si coeficiente de Pearson > 0.6
        
        Args:
            nombre_archivo (str): Nombre del archivo de curva a procesar (sin extensión .parquet)
            metodo (str): Método de ajuste a utilizar
            ruta_guardado (str): Directorio donde se guardarán los resultados
            
        Returns:
            dict: Resultados del procesamiento o None si no pasó los filtros
        """
        from scipy.stats import pearsonr, spearmanr
        import data
        from datetime import datetime, time
        
        # 1. Obtener los datos de la curva (similar a procesar_curva_por_id)
        nombre_archivo = nombre_archivo.replace('.parquet', '')
        analizador_procesar, fecha_str = nombre_archivo.split('_', 1)
        fecha_procesar = datetime.strptime(fecha_str, '%y.%m.%d_%H.%M.%S')
        fecha_param = fecha_procesar.strftime('%Y-%m-%d %H:%M')
        
        # Verificar hora (filtro 1: 6:30am - 5:30pm)
        hora_curva = fecha_procesar.time()
        if not (time(6, 30) <= hora_curva <= time(17, 30)):
            logging.info(f"Curva {nombre_archivo} fuera del rango horario (6:30am-5:30pm)")
            return None
        
        # Parámetros para la consulta SQL
        param_obtener_path_archivo = {
            'tabla_curvas': data.CURVAS_TABLE,
            'path_archivo': 'Path_Archivo',
            'analizador': 'Analizador',
            'datetime': 'Datetime',
        }

        # Ruta al archivo SQL
        script_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
        script_obtener_path_archivo = os.path.join(script_dir, 'obtener_id_path.sql')

        # Generar la consulta SQL
        query_obtener_path_archivo = self.sql_handler.generar_query_sql(script_obtener_path_archivo, param_obtener_path_archivo)

        # Ejecutar la consulta para obtener el Path_Archivo de la curva específica
        return_query_path = self.db_handler.execute_query(query_obtener_path_archivo, params=(analizador_procesar, fecha_param))
        
        curvas_validas = [
            (ruta[0], os.path.basename(ruta[0]).replace('.parquet', ''))
            for ruta in return_query_path
        ]
        
        def actualizar_rutas(curvas):
            nuevas_curvas = []
            for ruta_original, id_curva in curvas:
                partes = ruta_original.split('/')
                analizador = next(p for p in partes if p.startswith('AnP'))
                fecha_partes = id_curva.split('_')[1].split('.')
                año = f"20{fecha_partes[0]}"
                mes = fecha_partes[1]
                dia = fecha_partes[2]
                nombre_archivo = os.path.basename(ruta_original)
                
                nueva_ruta = os.path.join(
                    '/home/solarudea/Projects/SolarInformation/Analyzers/PanelAnalyzers',
                    analizador,
                    'Data',
                    año,
                    mes,
                    dia,
                    nombre_archivo
                )
                nuevas_curvas.append((nueva_ruta, id_curva))
            return nuevas_curvas
        
        path = actualizar_rutas(curvas_validas)
        id_curva = nombre_archivo
        path = path[0][0]
        
        try:
            # Leer datos del archivo
            data = pd.read_parquet(path)
            
            # Extraer Voc del archivo
            voc_value = None
            for row in data.itertuples(index=False):
                if isinstance(row[0], str) and row[0] == "Voc":
                    try:
                        voc_value = float(row[1])
                        break
                    except (ValueError, TypeError):
                        print(f"Error al convertir Voc a float: {row[1]}")
            
            # Obtener datos de voltaje y corriente
            Voltaje = data['Medicion Analizador PCB Raspberry Pi 2'][6:].tolist()
            Corriente = data['Unnamed: 1'][6:].tolist()
            date_str = data.iloc[2]['Medicion Analizador PCB Raspberry Pi 2']
            datetime_curva = pd.to_datetime(date_str)
            datetime_str = str(datetime_curva)
            
            voltaje = [float(v) for v in Voltaje]
            corriente = [float(c) for c in Corriente]

            # Encontrar el índice del voltaje mínimo
            Vmin_index = voltaje.index(min(voltaje))
            
            # Definir el rango de voltaje y corriente a partir del voltaje mínimo
            V_rango = voltaje[Vmin_index:]
            I_rango = corriente[Vmin_index:]
            
            # Calcular parámetros solares
            parametros_solares = SolarParameterCalculator.calcular_parametros_solares(V_rango, I_rango)
            parametros_solares_promediados = MeanParameterCalculator.calcular_parametros_promediados(V_rango, I_rango)

            # Añadir el valor de Voc en la primera posición de parametros_solares
            if voc_value is not None:
                parametros_solares.insert(0, voc_value)
                parametros_solares_promediados.insert(0, voc_value)
            
            # Extraer parámetros relevantes para los filtros
            try:
                isc = parametros_solares[3]  
                voc = parametros_solares[0]   
                impp = parametros_solares[6]  
                vmpp = parametros_solares[5] 
            except IndexError:
                logging.error(f"No se pudieron extraer todos los parámetros necesarios para los filtros")
                return None
            
            # Aplicar filtros
            filtros_pasados = True
            
            # Filtro 2: Vmpp > Voc
            if vmpp > voc:
                logging.info(f"Curva {id_curva} no ajustada - Vmpp ({vmpp}) > Voc ({voc})")
                filtros_pasados = False
            
            # Filtro 3: Impp > Isc
            if impp > isc:
                logging.info(f"Curva {id_curva} no ajustada - Impp ({impp}) > Isc ({isc})")
                filtros_pasados = False
            
            # Filtro 4: Coeficiente de Pearson
            coef_pearson, _ = pearsonr(V_rango, I_rango)
            if (abs(coef_pearson) <= 0.6):
                logging.info(f"Curva {id_curva} no ajustada - Coef. Pearson ({coef_pearson:.3f}) < 0.6")
                filtros_pasados = False
            
            if not filtros_pasados:
                # Guardar parámetros solares pero no ajustar curva
                guardar_parametros_solares = SolarParameterCalculator(self.db_handler)
                guardar_parametros_solares.insertar_parametros_solares(analizador_procesar, datetime_curva, parametros_solares)
                
                guardar_parametros_promediados = MeanParameterCalculator(self.db_handler)
                guardar_parametros_promediados.insertar_parametros_promediados(analizador_procesar, datetime_curva, parametros_solares_promediados)
                
                return {
                    'status': 'filtrado',
                    'motivo': 'No pasó los filtros de calidad',
                    'parametros_solares': parametros_solares,
                    'parametros_promediados': parametros_solares_promediados,
                    'coef_pearson': coef_pearson
                }
            
            # Si pasa los filtros, proceder con el ajuste
            Vmin_index = voltaje.index(min(voltaje))
            V_rango = voltaje[Vmin_index:]
            I_rango = corriente[Vmin_index:]
            P = [v * i for v, i in zip(V_rango, I_rango)]
            
            # Procesar curva
            procesador = Recorrer_dia(metodo=metodo, analizador=analizador_procesar, 
                                    dia=datetime_str, db_client=self.db_handler)
            resultados_ajuste = procesador.procesar_archivo(
                V_rango,
                I_rango,
                P,
                ruta_guardado,
                ruta_guardado,
                datetime_str,
                isc
            )
            
            # Guardar parámetros solares
            guardar_parametros_solares = SolarParameterCalculator(self.db_handler)
            guardar_parametros_solares.insertar_parametros_solares(analizador_procesar, datetime_curva, parametros_solares)
            
            guardar_parametros_promediados = MeanParameterCalculator(self.db_handler)
            guardar_parametros_promediados.insertar_parametros_promediados(analizador_procesar, datetime_curva, parametros_solares_promediados)
            
            logging.info(f"Curva {id_curva} procesada correctamente con ajuste.")
            
            return {
                'status': 'ajustado',
                'resultados_ajuste': resultados_ajuste,
                'parametros_solares': parametros_solares,
                'parametros_promediados': parametros_solares_promediados,
                'coef_pearson': coef_pearson
            }
    
            
        except Exception as e:
            logging.error(f"Error al procesar la curva {id_curva}: {e}")
            raise
