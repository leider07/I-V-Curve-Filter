from sql_handler import SQLHandler
import logging
import numpy as np
import data 
import os

class SolarParameterCalculator:
    """
    Clase para calcular parámetros solares a partir de curvas I-V.
    """
    def __init__(self, db_handler):
        """
        Inicializa la clase con el método de ajuste, el nombre del analizador y el día.

        Args:
            db_client: Cliente de la base de datos para ejecutar consultas.

        Returns:
            None
        """

        self.db_handler = db_handler
        self.sql_handler = SQLHandler(sql_script_path="../queries")

    @staticmethod
    def calcular_parametros_solares(V, I):
        """
        Calcula los parámetros solares (FF, Voce, Isc, Pmax, Vmax, Imax) a partir de voltaje y corriente.

        Args:
            V (list): Lista de voltajes.
            I (list): Lista de corrientes.

        Returns:
            list: Lista de parámetros solares [FF, Voce, Isc, Pmax, Vmax, Imax, Vmin, Imin].
        """
        # Encontrar el índice del voltaje mínimo
        ind = [i for (i, val) in enumerate(V) if val == min(V)]
        V = np.array(V[ind[0] + 1:])
        I = np.array(I[ind[0] + 1:])

        # Calcular la potencia
        Pv = V * I
        FitP = np.polyfit(V, Pv, 6)
        RootFitP = np.roots(FitP)
        DerP = np.polyder(FitP)
        RootP = np.roots(DerP)

        # Calcular Isc (corriente de cortocircuito)
        Isc1 = np.polyfit(V[0:10], I[0:10], 1)
        Isc = Isc1[1]

        # Calcular Voce (voltaje de circuito abierto)
        Voce = []
        ind = [i for (i, val) in enumerate(RootFitP) if np.real(val) > 0.1 and np.imag(val) == 0]
        if len(ind) == 0:
            Voce = 0
        elif len(ind) == 1:
            Vop = RootFitP[ind]
            Voce = min(Vop.real)
            if Voce > 1.5 * max(V):
                Voce = 0
        else:
            Vop = []
            for jind in ind:
                Vop.append(np.linalg.norm(RootFitP[jind] - max(V)))
            Voce = RootFitP[ind[Vop.index(min(Vop))]]

        # Calcular Vmax e Imax (punto de máxima potencia)
        ind = [i for (i, val) in enumerate(RootP) if np.real(val) > 0 and np.imag(val) == 0 and np.real(val) < Voce]

        if not ind:
            Vmax = 0
            Imax = 0
        else:
            Vmax = max(RootP[ind].real)
            Imax = np.polyval(FitP, Vmax) / Vmax

        # Calcular Pmax y FF (factor de llenado)
        Pmax = Vmax * Imax
        FF = Pmax / (Isc * Voce) if Isc * Voce != 0 else 0

        # Devolver los resultados
        Results = [float(FF), float(Voce), float(Isc), float(Pmax), float(Vmax), float(Imax), float(min(V)), float(min(I))]
        return Results
    
    def insertar_parametros_solares(self, analizador, datetime, parametros_solares):
        """
        Inserta los parámetros solares en la tabla Parameters_Grupo_Solar.

        Args:
            id_curva (str): El ID_Curva asociado a los parámetros.
            datetime (datetime): Estampa de tiempo para guardar en la base de datos
            parametros_solares (list): Lista de parámetros solares [Voc, FF, Voc_calculado, Isc, Pmax, Vnpp, Inpp, Vmin, Imin].

        Returns:
            None
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
            analizador              # ID_Curva
        )

        params = {
                'tabla_parametros_Grupo_Solar': data.PARAMETERS_SOLAR_ELEKTRA_TABLE,
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
        script_path_guardar_parametros_solares = os.path.join(script_dir, 'guardar_parametros_solares.sql')

        query = self.sql_handler.generar_query_sql(script_path_guardar_parametros_solares, params)

        # Ejecutar la consulta SQL
        self.db_handler.execute_query(query, parametros)

        self.db_handler.connection.commit()

        logging.info(f"Parámetros solares (Metodología 2) insertados en la tabla Parametros_Metodologia2.")