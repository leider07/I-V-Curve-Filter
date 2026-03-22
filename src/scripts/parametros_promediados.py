from sql_handler import SQLHandler
import logging
import numpy as np
import data 
import os

class MeanParameterCalculator:
    """
    Clase para calcular parámetros solares a partir de curvas I-V.
    """
    def __init__(self, db_handler):
        """
        Inicializa la clase con el manejador de base de datos.

        Args:
            db_handler: Manejador de la base de datos.
        """
        self.db_handler = db_handler
        self.sql_handler = SQLHandler(sql_script_path="../queries")

    @staticmethod
    def calcular_parametros_promediados(V, I):
        """
        Calcula los parámetros solares a partir de voltaje y corriente.

        Args:
            V (list): Lista de voltajes.
            I (list): Lista de corrientes.

        Returns:
            dict: Diccionario con los parámetros calculados.
        """
        # Encontrar el índice del voltaje mínimo
        ind = [i for (i, val) in enumerate(V) if val == min(V)]
        V = np.array(V[ind[0] + 1:])
        I = np.array(I[ind[0] + 1:])
        
        # Calcular Pmax, Vmpp, Impp
        P = V * I
        Pmax = np.max(P)
        max_idx = np.argmax(P)
        Vmpp = V[max_idx]
        Impp = I[max_idx]
        
        # Calcular Voc (voltaje en corriente cercana a cero)
        zero_current_threshold = 0.1 * np.max(np.abs(I))
        voc_indices = np.where(np.abs(I) <= zero_current_threshold)[0]
        Voc = np.max(V[voc_indices]) if len(voc_indices) > 0 else np.max(V)
        
        # Calcular Voce (voltaje al final de la curva)
        Voce = np.mean(V[-3:])
        
        # Calcular Isc (corriente al inicio de la curva)
        Isc = np.mean(I[:3])
        
        # Calcular FF
        FF = (Vmpp * Impp) / (Voce * Isc) if (Voce * Isc) != 0 else 0
        
        # Calcular Imin y Vmin
        Imin = np.mean(I[-3:])
        Vmin = np.mean(V[:3])
        
        Results = [float(FF), float(Voce), float(Isc), float(Pmax), float(Vmpp), float(Impp), float(Vmin), float(Imin)]
        return Results
    
    def insertar_parametros_promediados(self, analizador, datetime, parametros_solares):
        """
        Inserta los parámetros solares en la base de datos.

        Args:
            id_curva (str): ID de la curva asociada.
            datetime (datetime): Fecha y hora de la medición.
            parametros_solares (dict): Diccionario con los parámetros calculados.
        """

        # Parámetros para la consulta SQL
        parametros = (
            datetime,               # Estampa de tiempo
            parametros_solares[0],  # Voc (extraído del archivo Parquet)
            parametros_solares[2],  # Voce (Voc calculado)
            parametros_solares[1],  # FF
            parametros_solares[3],  # Isc
            parametros_solares[4],  # Pmax
            parametros_solares[5],  # Vmpp (Vmax)
            parametros_solares[6],  # Impp (Imax)
            parametros_solares[7],  # Vmin
            parametros_solares[8],  # Imin
            analizador              # Analizador
        )

        params = {
                'tabla_parametros_Elektra': data.PARAMETERS_SOLAR_TABLE,
                'datetime_curve': 'Datetime',
                'Voc': "Voc",
                'Voce': "Voce",
                'FF': "FF",
                'Isc': "Isc",
                'Pmax': "Pmax",
                'Vmpp': "Vmpp",
                'Impp': "Impp",
                'Vmin': "Vmin",
                'Imin': "Imin",
                'analizador': "Analizador",
            }
        
        script_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
        script_path = os.path.join(script_dir, 'guardar_parametros_promediados.sql')
        query = self.sql_handler.generar_query_sql(script_path, params)

        self.db_handler.execute_query(query, parametros)
        self.db_handler.connection.commit()

        logging.info(f"Parámetros solares (Metodología 1) insertados en la tabla Parametros_Metodologia2.")
