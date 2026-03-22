import os
import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d
from scipy.stats import pearsonr, spearmanr
import logging  
from datetime import datetime
import data
from sql_handler import SQLHandler

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

class AnalizadorCurvaIV:
    """
    Clase para analizar y ajustar curvas IV (corriente vs. voltaje) de un panel solar u otros dispositivos eléctricos.

    Atributos:
        v_p (float): Valor del voltaje en el punto de máxima potencia.
        i_p (float): Valor de la corriente en el punto de máxima potencia.
        Vt (float): Tensión térmica para el diodo en el modelo.
        Ns (int): Número de celdas en serie del panel.

    Métodos:
        procesar_curva(data_file_path):
            Procesa los datos de voltaje y corriente de un archivo CSV.
    """
    def __init__(self):
        """
        Inicializa el objeto AnalizadorCurvaIV con valores predeterminados.

        Args:
            Ninguno

        Returns:
            None
        """
        self.v_p = None
        self.i_p = None
        self.Vt = 0.03875220203
        self.Ns = None
        self.metodo_usado = None  
        self.error = None  
    
    def procesar_curva(self, data_file_path):
        """
        Procesa la curva de voltaje y corriente proveniente de un analizador y extrae los datos para su análisis.

        Args:
            data_file_path (: Ruta del archivo CSV que contiene los datos de voltaje y corriente.

        Returns:
            None
        """
        logging.info(f"Procesando curva desde el archivo: {data_file_path}")
        try:
            data = pd.read_csv(data_file_path, delimiter=',', skiprows=6)
            V_rango1 = data['Voltaje'].values
            I_rango1 = data['Corriente'].values
            Voltaje_float = [float(elemento) for elemento in V_rango1]
            Corriente_float = [float(elemento) for elemento in I_rango1]

            Vmin_index = Voltaje_float.index(min(Voltaje_float))
            V_rango = Voltaje_float[Vmin_index:]
            I_rango = Corriente_float[Vmin_index:]
            P = list(map(lambda x, y: x * y, V_rango, I_rango))

            return V_rango, I_rango, P
        except Exception as e:
            logging.error(f"Error al procesar la curva: {e}")
            raise

    def ajustar(self, V_rango, I_rango, P, metodo='fmin'):
        try:
            if metodo == 'fmin':
                data_ajustada, res_ajuste = self.ajuste_fmin(V_rango, I_rango)
                self.metodo_usado = 'fmin'
                error = self.CurvaS_003b(res_ajuste)
            elif metodo == 'nelder':
                data_ajustada, res_ajuste = self.ajuste_nelder(V_rango, I_rango)
                self.metodo_usado = 'nelder'
                error = self.CurvaS_003b(res_ajuste)
            elif metodo == 'hibrido':
                data_ajustada, res_ajuste, metodo_final, error_final = self.ajuste_hibrido(V_rango, I_rango)
                self.metodo_usado = metodo_final
                error = error_final
            else:
                raise ValueError("Método no reconocido. Use 'fmin', 'nelder' o 'hibrido'.")

            return data_ajustada, res_ajuste, self.metodo_usado, error

        except Exception as e:
            logging.error(f"Error en el ajuste de la curva: {e}")
            raise


    def ajuste_fmin(self, V_rango, I_rango):
        """
        Ajusta la curva IV utilizando el método de optimización 'fmin'.

        Args:
            V_rango (list): Lista de valores de voltaje.
            I_rango (list): Lista de valores de corriente.

        Returns:
            tuple: Una matriz con los datos ajustados y los parámetros resultantes al aplicar fmin.
        """
        try:
            self.v_p = V_rango
            self.i_p = I_rango
            self.Ns = int(np.ceil(self.v_p[-1] / 0.6))
            X_0, Xv = self.Dat_init1(V_rango, I_rango)

            res_fmin = opt.fmin(self.CurvaS_003b, X_0, maxfun=10000, xtol=1e-6, ftol=1e-6)

            I_fmin = self.CurvaS_004a(res_fmin, V_rango)
            data_fmin = np.zeros((len(I_fmin), 2))

            for i in range(len(I_fmin)):
                data_fmin[i, 0] = self.v_p[i]
                data_fmin[i, 1] = I_fmin[i]
            
            logging.info("Ajuste fmin completado exitosamente")
            return data_fmin, res_fmin
        except Exception as e:
            logging.error(f"Error en el ajuste fmin: {e}")
            raise
    
    def ajuste_hibrido(self, V_rango, I_rango):
        """
        Ajuste híbrido: usa fmin y nelder según calidad del ajuste.
        """
        try:
            self.v_p = V_rango
            self.i_p = I_rango
            self.Ns = int(np.ceil(self.v_p[-1] / 0.6))
            X_0, Xv = self.Dat_init1(V_rango, I_rango)

            res_fmin = opt.fmin(self.CurvaS_003b, X_0, maxfun=10000, xtol=1e-6, ftol=1e-6, disp=False)
            error = self.CurvaS_003b(res_fmin)

            logging.info(f"Error final fmin: {error}")

            if error <= 1 or error >= 500:
                I_fmin = self.CurvaS_004a(res_fmin, V_rango)
                data_fmin = np.zeros((len(I_fmin), 2))
                for i in range(len(I_fmin)):
                    data_fmin[i, 0] = self.v_p[i]
                    data_fmin[i, 1] = I_fmin[i]
                logging.info("Ajuste fmin aceptado")
                metodo_usado = "fmin"
                return data_fmin, res_fmin, metodo_usado, error

            else:
                logging.info("Error fmin alto, usando Nelder-Mead")
                data_nelder, res_nelder = self.ajuste_nelder(V_rango, I_rango)
                metodo_usado = "nelder"
                error = self.CurvaS_003b(res_nelder)
                logging.info(f"Error final nelder: {error}")
                return data_nelder, res_nelder, metodo_usado, error

        except Exception as e:
            logging.error(f"Error en el ajuste combinado: {e}")
            raise



        except Exception as e:
            logging.error(f"Error en el ajuste combinado: {e}")
            raise

    def ajuste_nelder(self, V_rango, I_rango):
        """
        Ajusta la curva IV utilizando el método de optimización 'Nelder-Mead'.

        Args:
            V_rango (list): Lista de valores de voltaje.
            I_rango (list): Lista de valores de corriente.

        Returns:
            tuple: Una matriz con los datos ajustados y los parámetros resultantes aplicando fmin.
        """
        logging.info("Aplicando ajuste con método Nelder-Mead")
        try:
            self.v_p = V_rango
            self.i_p = I_rango
            self.Ns = int(np.ceil(self.v_p[-1] / 0.6))
            X_0, Xv = self.Dat_init1(V_rango, I_rango)
            res_nelder, FunValor, C = self.Nelder_Mead(self.CurvaS_003b, X_0, 1000, 10000, 1e-8)
            I_nelder = self.CurvaS_004a(res_nelder, V_rango)
            data_nelder = np.zeros((len(I_nelder), 2))

            for i in range(len(I_nelder)):
                data_nelder[i, 0] = self.v_p[i]
                data_nelder[i, 1] = I_nelder[i]

            logging.info("Ajuste Nelder-Mead completado exitosamente")
            self.metodo_usado = "nelder"
            return data_nelder, res_nelder
        except Exception as e:
            logging.error(f"Error en el ajuste Nelder-Mead: {e}")
            raise

    def Dat_init1(self, V_rango, I_rango):
        """
        Inicializa los parámetros para el ajuste de la curva IV.

        Args:
            V_rango (list): Lista de valores de voltaje.
            I_rango (list): Lista de valores de corriente.

        Returns:
            tuple: Lista de parámetros iniciales y sus nombres.
        """
        try:
            I_sc = max(I_rango)
            I_ph_0 = I_sc
            I_s_0 = 9.825e-8
            Voc = V_rango[-1]
            n_0 = 1.5 * self.Ns * self.Vt  # Factor de idealidad

            ppp = np.array(V_rango) * np.array(I_rango)
            Pmax = max(ppp)
            imax = list(ppp).index(Pmax)

            Vmp = self.v_p[imax]
            Imax = self.i_p[imax]
            Vx = 0.5 * Voc
            Vxx = 0.5 * (Vmp + Voc)

            interpolacion = interp1d(self.v_p, self.i_p, kind='linear', fill_value="extrapolate")

            Ix = interpolacion(Vx)
            Ixx = interpolacion(Vxx)        

            FF = (Pmax) / (I_sc * Voc)

            R_s_0 = (Voc - Vxx) / Ixx
            R_p_0 = Vx / (I_sc - (Ix + 0.00001))

            X_0 = [I_ph_0, I_s_0, n_0, R_s_0, R_p_0]
            Xv = ['I_ph', 'I_s', 'n_d', 'R_s', 'R_p']

            return X_0, Xv
        except Exception as e:
            logging.error(f"Error al inicializar parámetros: {e}")
            raise

    def CurvaS_004a(self, X, rV):
        """ 
        Calcula la curva IV a partir de los parámetros ajustados y los valores de voltaje.

        Args:
            X (list): Parámetros del ajuste [I_ph, I_s, n_d, R_s, R_p].
            rV (list): Lista de valores de voltaje para los cuales calcular la corriente.

        Returns:
            list: Lista de valores de corriente ajustada.
        """
        try:
            I_ph, I_s, n_d, R_s, R_p = X
            I_graf = []
            for VD in rV:
                f_graf = lambda I: I_ph - I_s * (np.exp((I * R_s + VD) / (n_d)) - 1) - ((VD + I * R_s) / R_p) - I
                ss = opt.fsolve(f_graf, I_ph)
                ss = float(ss[0])
                I_graf.append(ss)

            return I_graf
        except Exception as e:
            logging.error(f"Error al calcular la curva IV: {e}")
            raise

    def CurvaS_003b(self, X):
        """
        Función de mínimos cuadrados para calcular los parámetros de una celda solar a partir de la curva I-V.

        Args:
            X (list): Parámetros del ajuste [I_ph, I_s, n_d, R_s, R_p].

        Returns:
            float: El valor de la función de error (mínimos cuadrados).
        """
        try:
            I_ph, I_s, n_d, R_s, R_p = X
            rs1 = 0

            if R_p < 0 or R_s < 0 or n_d < 0 or I_s < 0 or I_ph < 0:
                rs1 = 1000

            res = []
            n = len(self.v_p)
            for q in range(n):
                vd = self.v_p[q] + self.i_p[q] * R_s
                I_d = I_s * (np.exp(vd / (n_d)) - 1)
                I_p = vd / R_p
                f = -self.i_p[q] + I_ph - I_d - I_p
                res.append(f)

            resT = np.linalg.norm(res, 2) + rs1

            return resT
        except Exception as e:
            logging.error(f"Error en el cálculo de mínimos cuadrados: {e}")
            raise
    
    def completar_curvaIV(self, V_rango, res_fmin, data_file_path):
        """
        Completa la curva IV para un panel solar generando valores adicionales de voltaje y corriente.

        Esta función genera un conjunto adicional de valores de voltaje (`V_extra`) que se extienden desde 
        el último valor de `V_rango` hasta un valor máximo especificado (`Voc_comp`). Luego calcula la corriente
        asociada (`I_extra`) usando la función `CurvaS_004a`. La función ajusta `Voc_comp` para que coincida con
        el valor de voltaje donde la corriente se vuelve cero (Isc=0 y Voc=máx), y recorta las listas `V_extra` e `I_extra` 
        hasta ese punto. Finalmente, retorna las listas ajustadas.

        Args:
            V_rango (list): Lista de valores de voltaje existentes.
            res_fmin (list): Parámetros del ajuste 'fmin'.
            data_file_path (: Ruta al archivo de datos que contiene información adicional para completar la curva.

        Returns:
            tuple: Dos listas con los valores de voltaje y corriente extendidos.
        """
        logging.info("Completando curva IV con valores adicionales")
        try:
            df = pd.read_csv(data_file_path, header=None)   # Curva sin quitar encabezado
            Voc_comp = float(df[df[0] == 'Voc'].iloc[0, 1]) # Voc a completar propuesto

            V_extra = np.linspace(V_rango[-1], Voc_comp, 100).tolist()
            I_extra = self.CurvaS_004a(res_fmin, V_extra)

            # Se encuentra el índice donde I_extra se vuelve menor o igual a cero
            for idx, I_val in enumerate(I_extra):
                if I_val <= 0:
                    Voc_comp = V_extra[idx]
                    V_extra = V_extra[:idx+1]
                    I_extra = I_extra[:idx+1]
                    break
            
            logging.info("Curva IV completada exitosamente")
            return V_extra, I_extra
        except Exception as e:
            logging.error(f"Error al completar la curva IV: {e}")
            raise
    
    def Nelder_Mead(self, CurvaS_003b, X, MinI, MaxI, ToleranciaF):
        """
        Implementa el algoritmo de Nelder-Mead para minimizar una función no lineal.

        Descripción general del método de Nelder-Mead:
        - El método encuentra el mínimo de una función de varias variables usando un símplex,
            un cuerpo geométrico cuya forma en 2D es un triángulo y en 3D es un tetraedro.
        - Se evalúan los vértices del símplex (condiciones iniciales) para determinar el peor vértice,
            que es el que menos minimiza la función.
        - La figura cambia de forma y se reduce hasta que los vértices están lo suficientemente juntos
            y el valor de la función es aproximadamente constante.

        Algoritmo de Nelder-Mead:
        1. Definir la figura inicial, es decir, los vértices iniciales o condiciones iniciales.
        2. Identificar los mejores puntos que minimizan la función y calcular su punto medio.
        3. Reflexión: Reflejar el peor punto respecto al punto medio hacia la otra cara de la figura 'óptima'.
        4. Extensión: Si la reflexión mejora el valor, extender la figura duplicando la distancia entre el reflejo y el punto medio.
        5. Contracción: Si no se mejora con la reflexión, buscar dos puntos medios entre el baricentro y los puntos malos.
        6. Encogimiento: Si aún no se encuentra un buen punto, encoger el símplex hacia el mejor punto.

        Args:
            CurvaS_003b (function): Función objetivo a minimizar.
            X (array_like): Valores iniciales de las variables a optimizar.
            MinI (int): Mínimo número de iteraciones.
            MaxI (int): Máximo número de iteraciones.
            ToleranciaF (float): Tolerancia para la convergencia del algoritmo.

        Returns:
            Minimo (array_like): Valores óptimos de las variables que minimizan la función.
            FunValor (float): Valor de la función objetivo en el mínimo.
            contador (int): Número de iteraciones realizadas.
        """

        try:
            import numpy as np

            # Inicialización de contenedores para los vértices y los valores de la función
            n = np.size(X)
            FunValor = np.zeros([1, n + 1])
            Vertices = np.zeros([n + 1, n])

            # Desviación de los datos (diferentes de 0 al 5%, igual a cero al 0.025%)
            Delta = 0.05
            Delta0 = 0.00025

            # Evaluación de la condición inicial
            Vertices[0, :] = X
            f = CurvaS_003b(X)
            FunValor[0, 0] = f

            # Evaluación de las condiciones iniciales desviadas
            for i in range(0, n):
                y = X
                if y[i] != 0:
                    y[i] = (1 + Delta) * y[i]
                else:
                    y[i] = (1 + Delta0) * y[i]

                Vertices[i + 1, :] = y
                f = CurvaS_003b(y)
                FunValor[0, i + 1] = f

            # Identificación del vértice con el máximo y mínimo valor de la función
            Max = max(FunValor[0, :])
            Min = min(FunValor[0, :])
            PosM = 0
            PosMin = 0

            for i in range(0, n + 1):
                if FunValor[0, i] == Max:
                    break
                PosM += 1

            for i in range(0, n + 1):
                if FunValor[0, i] == Min:
                    break
                PosMin += 1

            PM = PosM
            PMX = PosMin

            for j in range(0, n + 1):
                if j != PosMin and j != PosM and FunValor[0, j] <= FunValor[0, PM]:
                    PM = j
                if j != PosM and j != PosMin and FunValor[0, j] >= FunValor[0, PMX]:
                    PMX = j

            # Comenzamos a desarrollar el método de Nelder-Mead
            contador = 0

            while (FunValor[0, PosM] > FunValor[0, PosMin] and contador < MaxI) or contador < MinI:
                if (abs(FunValor[0, PosMin] - FunValor[0, PosM]) <= ToleranciaF and
                        max(abs(Vertices[PosMin, :] - Vertices[PosM, :])) <= ToleranciaF):
                    break

                Z = np.zeros([1, n])
                for q in range(0, n + 1):
                    Z = Z + Vertices[q, :]

                M = (Z - Vertices[PosM, :]) / n  # Punto medio, baricentro
                R = 2 * M - Vertices[PosM, :]  # Reflexión
                EvalR = CurvaS_003b(list(R[0, :]))  # Evaluación del punto reflejado

                if EvalR < FunValor[0, PosMin]:  # Si la reflexión es mejor que el mejor punto, procedemos a la extensión
                    E = 3 * M - Vertices[PosM, :]  # Extensión
                    EvalE = CurvaS_003b(list(E[0, :]))  # Evaluación del punto de extensión

                    if EvalE < EvalR:  # Si la extensión es mejor que la reflexión, usamos la extensión
                        Vertices[PosM, :] = E
                        FunValor[0, PosM] = EvalE
                    else:  # Si la reflexión es mejor que la extensión, usamos la reflexión
                        Vertices[PosM, :] = R
                        FunValor[0, PosM] = EvalR
                else:
                    if EvalR < FunValor[0, PMX]:  # Si la reflexión es mejor que el segundo peor punto
                        Vertices[PosM, :] = R
                        FunValor[0, PosM] = EvalR
                    else:
                        if EvalR < FunValor[0, PosM]:  # Si la extensión es mejor que el peor punto
                            C1 = M + (-Vertices[PosM, :] + M) / 2.0  # Contracción exterior
                            EvalC1 = CurvaS_003b(list(C1[0, :]))

                            if EvalC1 <= EvalR:  # Si la contracción exterior es mejor que la reflexión
                                Vertices[PosM, :] = C1
                                FunValor[0, PosM] = EvalC1
                            else:  # Si la reflexión es mejor que la contracción, realizamos el encogimiento
                                for j in range(0, n + 1):
                                    Vertices[j, :] = Vertices[PosMin, :] + (Vertices[j, :] - Vertices[PosMin, :]) / 2
                                    w = Vertices[j, :]
                                    FunValor[0, j] = CurvaS_003b(w)
                        else:  # Si la extensión es peor que el peor punto
                            C2 = M + (Vertices[PosM, :] - M) / 2.0  # Contracción interior
                            EvalC2 = CurvaS_003b(list(C2[0, :]))

                            if EvalC2 < FunValor[0, PosM]:  # Si la contracción interior es mejor que la reflexión
                                Vertices[PosM, :] = C2
                                FunValor[0, PosM] = EvalC2
                            else:  # Si la reflexión es mejor que la contracción, realizamos el encogimiento
                                for j in range(0, n + 1):
                                    Vertices[j, :] = Vertices[PosMin, :] + (Vertices[j, :] - Vertices[PosMin, :]) / 2
                                    w = Vertices[j, :]
                                    FunValor[0, j] = CurvaS_003b(w)

                # Actualización de los vértices con el máximo y mínimo valor de la función
                Max = max(FunValor[0, :])
                Min = min(FunValor[0, :])
                PosM = 0
                PosMin = 0

                for i in range(0, n + 1):
                    if FunValor[0, i] == Max:
                        break
                    PosM += 1

                for i in range(0, n + 1):
                    if FunValor[0, i] == Min:
                        break
                    PosMin += 1

                PM = PosM
                PMX = PosMin

                for j in range(0, n + 1):
                    if (j != PosMin and j != PosM and FunValor[0,j] <= FunValor[0,PM]):
                        PM = j
                    if (j != PosM and j != PosMin and FunValor[0,j] >= FunValor[0,PMX]):
                        PMX = j
                
                contador += 1

            # Determinamos el mínimo
            Minimo = Vertices[PosMin, :]
            FunValor = CurvaS_003b(Minimo)

            logging.info("Algoritmo de Nelder-Mead completado exitosamente")
            return Minimo, FunValor, contador
        except Exception as e:
            logging.warning(f"Error al aplicar el algoritmo de Nelder-Mead: {e}")
            Minimo_predeterminado = np.zeros_like(X) 
            FunValor_predeterminado = np.inf  
            contador_predeterminado = MaxI   
            
            return Minimo_predeterminado, FunValor_predeterminado, contador_predeterminado
    
    def graficar_resultados(self, V_rango, I_rango, P, metodo='fmin', completar_curva=False, data_file_path=None):
        """
        Grafica los datos originales, el ajuste seleccionado y, opcionalmente, los datos completados.

        Args:
            V_rango (list): Lista de voltajes medidos del panel solar.
            I_rango (list): Lista de corrientes medidas correspondientes a los valores de V_rango.
            P (list): Lista de potencias calculadas a partir de los valores de voltaje y corriente.
            metodo (: Método de ajuste de la curva IV. Puede ser 'fmin' (por defecto) o 'nelder'.
            completar_curva (bool, opcional): Indica si se deben completar los datos de la curva IV. 
                                              El valor por defecto es False.
            data_file_path ( opcional): Ruta al archivo CSV que contiene los datos necesarios para 
                                            completar la curva IV. Requerido si completar_curva es True.

        Returns:
            None
        """
        try:
            # Ajuste de datos
            if metodo == 'fmin':
                data_ajustada, _ = self.ajustar(V_rango, I_rango, P, metodo='fmin')
            elif metodo == 'nelder':
                data_ajustada, _ = self.ajustar(V_rango, I_rango, P, metodo='nelder')
            else:
                raise ValueError("Método no soportado. Use 'fmin' o 'nelder'.")
            
            # Preparar datos para el ajuste
            V_ajustada = data_ajustada[:, 0]
            I_ajustada = data_ajustada[:, 1]

            # Si se requiere completar la curva IV
            if completar_curva and data_file_path:
                V_extra, I_extra = self.completar_curvaIV(V_rango, _, data_file_path)
                V_rango_completo = V_rango + V_extra
                I_rango_completo = I_rango + I_extra
                plt.plot(V_extra, I_extra, label='Datos Completados', color='red', linestyle='--')
            else:
                V_rango_completo = V_rango
                I_rango_completo = I_rango
            
            # Graficar
            plt.plot(V_rango, I_rango, label='Datos I-V', color='blue')
            plt.plot(V_ajustada, I_ajustada, label=f'Ajuste {metodo}', color='green')
            plt.xlabel('Voltaje (V)')
            plt.ylabel('Corriente (I)')
            plt.legend()
            plt.title('Ajuste I-V del Panel Solar')
            plt.grid(True)
            plt.show()

            logging.info("Grafico generado exitosamente")
        except Exception as e:
            logging.error(f"Error al graficar los resultados: {e}")
            raise

class Recorrer_dia:
    """
    Clase para procesar archivos de datos, realizar ajustes de curvas IV y guardar los resultados.

    Atributos:
        metodo (: Método de ajuste a utilizar ('fmin' o 'nelder').
        analizador (: Identificador del analizador (por ejemplo, 'AnP0X').
        dia (: Fecha en formato 'dd.mm.yy' (por ejemplo, '21.06.01').
    
    Métodos:
        guardar_parametros_en_csv(file_name, X_0, res_ajuste, data_ajustada, path_to_save):
            Guarda los parámetros ajustados y los datos de ajuste en un archivo CSV.
        
        procesar_archivo(file_path, output_csv_path):
            Procesa un archivo CSV de datos, ajusta la curva y guarda los resultados.
        
        graficar_datos(V_rango, I_rango, data_ajustada, res_ajuste, file_name, save_path):
            Genera un gráfico de los datos originales y ajustados, y lo guarda en un archivo PNG.
        
        procesar_carpeta(ruta_carpeta, save_path):
            Procesa todos los archivos CSV en una carpeta, ajusta las curvas y guarda los resultados y gráficos.
    """
    def __init__(self, metodo, analizador, dia, db_client):
        """
        Inicializa la clase con el método de ajuste, el nombre del analizador y el día.

        Args:
            metodo (: Método de ajuste a utilizar ('fmin' o 'nelder').
            analizador (: Identificador del analizador (por ejemplo, 'AnP0X').
            dia (: Fecha en formato 'dd.mm.yy' (por ejemplo, '21.06.01').
            db_client: Cliente de la base de datos para ejecutar consultas.

        Returns:
            None
        """
        logging.info(f"Inicializando Recorrer_dia con método: {metodo}, analizador: {analizador}, día: {dia}")
        self.metodo = metodo
        self.metodo_usado = None
        self.analizador = analizador
        self.dia = dia
        self.db_client = db_client
        self.sql_handler = SQLHandler(sql_script_path="../queries")

    
    @staticmethod
    def guardar_parametros_en_csv(analizador, file_name, X_0, res_ajuste, data_ajustada, path_to_save, metodo_usado, error_metodo, Isc):
        """
        Guarda los parámetros ajustados y los datos de ajuste en un archivo CSV.

        Args:
            file_name (: Nombre del archivo de datos original.
            X_0 (list): Parámetros iniciales del ajuste.
            res_ajuste (list): Resultados del ajuste.
            data_ajustada (numpy.ndarray): Datos ajustados.
            path_to_save (: Ruta para guardar el archivo CSV.

        Returns:
            None
        """

        try:
            coef_pearson = pearsonr(x=data_ajustada[:, 0].tolist(), y=data_ajustada[:, 1].tolist())[0]
            parametros = {
                'Analizador': [analizador],
                'Datetime': [file_name],
                'Coef_Pearson': [round(coef_pearson, 4)],
                'Iph_0': [round(X_0[0], 5)],
                'Is_0': [format(round(X_0[1], 16), ".6e")],
                'nd_0': [round(X_0[2], 5)],
                'Rs_0': [round(X_0[3], 5)],
                'Rp_0': [round(X_0[4], 5)],
                'Iph': [round(res_ajuste[0], 5)],
                'Is': [format(round(res_ajuste[1], 16), ".6e")],
                'nd': [round(res_ajuste[2], 5)],
                'Rs': [round(res_ajuste[3], 5)],
                'Rp': [round(res_ajuste[4], 5)],
                'Metodo': [metodo_usado],
                'Error_Metodo': [round(error_metodo, 4)],
                'Isc':[round(Isc, 4)]
            }
            df = pd.DataFrame(parametros)
            df.to_csv(path_to_save, mode='a', header=not os.path.exists(path_to_save), index=False)
            logging.info(f"Parametros guardados exitosamente en {path_to_save}")
        except Exception as e:
            logging.error(f"Error al guardar parametros en CSV: {e}")
            raise


    def guardar_parametros_en_db(self, id_curva, X_0, res_ajuste, data_ajustada, db_handler, metodo_usado, error):
        """
        Guarda los parámetros ajustados y los datos de ajuste en la tabla resultados_ajuste de MariaDB.
        """
        try:
            if np.all(data_ajustada[:, 0] == data_ajustada[0, 0]) or np.all(data_ajustada[:, 1] == data_ajustada[0, 1]):
                coef_pearson = None
                coef_spearman = None
            else:
                # Calcular el coeficiente de Pearson
                coef_pearson = pearsonr(x=data_ajustada[:, 0].tolist(), y=data_ajustada[:, 1].tolist())[0]

                # Calcular el coeficiente de Spearman
                coef_spearman = spearmanr(a=data_ajustada[:, 0].tolist(), b=data_ajustada[:, 1].tolist())[0]

            # Formatear el ID de la curva
            fecha_hora = datetime.strptime(id_curva, "%Y-%m-%d %H:%M:%S")
            id_curva = f"{self.analizador}_{fecha_hora.strftime('%y.%m.%d_%H.%M.%S')}.parquet"

            # Conectar a la base de datos
            db_handler.connect()

            parametros = (                           
                round(coef_pearson, 4) if coef_pearson is not None else None,    # Coef_Pearson 
                round(coef_spearman, 4) if coef_spearman is not None else None,  # Coef_Spearman                       
                round(X_0[0], 5),                                                # Iph_0
                format(round(X_0[1], 16), ".6e"),                                # Is_0
                round(X_0[2], 5),                                                # nd_0
                round(X_0[3], 5),                                                # Rs_0
                round(X_0[4], 5),                                                # Rp_0
                round(res_ajuste[0], 5),                                         # Iph_f
                format(round(res_ajuste[1], 16), ".6e"),                         # Is_f
                round(res_ajuste[2], 5),                                         # nd_f
                round(res_ajuste[3], 5),                                         # Rs_f
                round(res_ajuste[4], 5),                                         # Rp_f
                self.analizador,                                                 # Analizador
                fecha_hora,                                                      # Datetime
                metodo_usado,                                                    # Metodo usado
                round(error, 4)                                                  # Error del método

            )

            params = {
                'tabla_resultados_ajuste': data.RESULTADOS_AJUSTE_TABLE,
                'Coef_Pearson': 'coef_pearson',
                'Coef_Spearman': 'coef_spearman',
                'Iph_0': "iph_0",
                'Is_0': "is_0",
                'nd_0': "nd_0",
                'Rs_0': "rs_0",
                'Rp_0': "rp_0",
                'Iph_f': "iph_f",
                'Is_f': "is_f",
                'nd_f': "nd_f",
                'Rs_f': "rs_f",
                'Rp_f': "rp_f",
                'analizador': "Analizador",
                'fecha_hora': "Datetime",
                'Metodo_usado': "metodo_usado",
                'Error_metodo': "error_metodo",
            }

            script_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'queries')
            script_path_guardar_parametros = os.path.join(script_dir, 'guardar_parametros_ajuste.sql')

            query = self.sql_handler.generar_query_sql(script_path_guardar_parametros, params)

            # Ejecutar la consulta SQL
            db_handler.execute_query(query, parametros)

            logging.info(f"Parámetros del ajuste guardados exitosamente en la base de datos para el archivo {id_curva}.")

        except Exception as e:
            logging.error(f"Error al guardar parámetros en la base de datos: {e}")
            raise

    def procesar_archivo(self, V_rango, I_rango, P, output_csv_path, output_png_path, name_archivo, Isc):
        """
        Procesa un archivo de datos, realiza el ajuste de la curva y almacena los resultados en un CSV.

        Args:
            V_rango (array): Rango de voltaje para el análisis.
            I_rango (array): Rango de corriente para el análisis.
            P (array): Parámetros iniciales para el ajuste.
            output_csv_path (: Ruta del directorio donde se guardará el archivo CSV.
            output_png_path (: Ruta del archivo PNG para guardar la gráfica.
            name_archivo (: Nombre del archivo que se está procesando.

        Returns:
            tuple: Rangos de voltaje y corriente, datos ajustados y resultados del ajuste.
        """
        try:
            analizador = AnalizadorCurvaIV()
            data_ajustada, res_ajuste, self.metodo_usado, self.error = analizador.ajustar(V_rango, I_rango, P, metodo=self.metodo)

            #data_ajustada, res_ajuste = analizador.ajustar(V_rango, I_rango, P, metodo=self.metodo)
            #self.metodo_usado = analizador.metodo_usado
            #self.error = analizador.error
            
            X_0, Xv = analizador.Dat_init1(V_rango, I_rango)
            
            # Definir el nombre del archivo CSV
            csv_filename = os.path.join(output_csv_path, "parametros_ajuste.csv")
            
            self.guardar_parametros_en_csv(self.analizador, name_archivo, X_0, res_ajuste, data_ajustada, csv_filename, self.metodo_usado, self.error, Isc)
            self.graficar_datos(V_rango, I_rango, X_0, data_ajustada, res_ajuste, name_archivo, output_png_path, self.error)
            
            logging.info(f"Archivo {name_archivo} procesado exitosamente")
            return V_rango, I_rango, data_ajustada, res_ajuste
        except Exception as e:
            logging.error(f"Error al procesar el archivo {name_archivo}: {e}")
            raise


    def procesar_archivo_db(self, V_rango, I_rango, P, db_handler, output_png_path, name_archivo):
        """
        Procesa un archivo de datos, realiza el ajuste de la curva y almacena los resultados.

        Args:
            V_rango (array): Rango de voltaje para el análisis.
            I_rango (array): Rango de corriente para el análisis.
            P (array): Parámetros iniciales para el ajuste.
            db_handler (objeto): Manejador de la base de datos para guardar los resultados.
            output_png_path (: Ruta del archivo PNG para guardar la gráfica.
            name_archivo (: Nombre del archivo que se está procesando.

        Returns:
            tuple: Rangos de voltaje y corriente, datos ajustados y resultados del ajuste.
        """

        try:
            analizador = AnalizadorCurvaIV()
            data_ajustada, res_ajuste,  self.metodo_usado, self.error = analizador.ajustar(V_rango, I_rango, P, metodo=self.metodo)
            
            self.metodo_usado = analizador.metodo_usado            
            
            X_0, Xv = analizador.Dat_init1(V_rango, I_rango)

            self.guardar_parametros_en_db(name_archivo, X_0, res_ajuste, data_ajustada, db_handler, self.metodo_usado, self.error)
            # self.graficar_datos(V_rango,I_rango,X_0, data_ajustada,res_ajuste, name_archivo, output_png_path, self.error)
            
            logging.info(f"Archivo {name_archivo} procesado exitosamente")
            return V_rango, I_rango, data_ajustada, res_ajuste
        except Exception as e:
            logging.error(f"Error al procesar el archivo {name_archivo}: {e}")
            raise

    def graficar_datos(self, V_rango, I_rango, X_0, data_ajustada, res_ajuste, id_curva, save_path, error_metodo):
        """
        Genera un gráfico de los datos originales y ajustados, y lo guarda en un archivo PNG.

        Args:
            V_rango (list): Rango de voltajes.
            I_rango (list): Rango de corrientes.
            data_ajustada (numpy.ndarray): Datos ajustados.
            res_ajuste (list): Resultados del ajuste.
            id_curva (: Nombre del archivo original para el título del gráfico.
            save_path (: Ruta para guardar el archivo PNG.

        Returns:
            None
        """

        try:
            corr_test = pearsonr(x=data_ajustada[:, 0].tolist(), y=data_ajustada[:, 1].tolist())

            plt.figure()
            plt.plot(V_rango, I_rango, label='$I$-$V$ $Data$', color='royalblue', linewidth=2.5)
            plt.plot(data_ajustada[:, 0], data_ajustada[:, 1], label=f'{self.metodo_usado}', color='orange', linestyle='--', linewidth=2)

            plt.xlabel("$Voltage$ $(V)$")
            plt.ylabel("$Current$ $(A)$")
            plt.legend(loc='lower left', fontsize=10, frameon=False) 

            plt.title(
                f'Curva I-V {self.analizador}: ({id_curva})\n'
                f'Coef. de Pearson: {corr_test[0]:.2f}, '
                f'Error: {error_metodo:.3f}\n'
                f'Vector X inicial ({self.metodo_usado}): ' +
                f'Iphi: {round(X_0[0], 3)}, ' +
                f'Isi: {format(X_0[1], ".3e")}, ' +  # Notación científica
                f'ndi: {round(X_0[2], 3)}, ' +
                f'Rsi: {round(X_0[3], 5)}, ' +
                f'Rpi: {round(X_0[4], 3)}\n' +
                f'Vector X final ({self.metodo_usado}) : ' +
                f'Iph: {round(res_ajuste[0], 3)}, ' +
                f'Is: {format(res_ajuste[1], ".3e")}, ' +  # Notación científica
                f'nd: {round(res_ajuste[2], 3)}, ' +
                f'Rs: {round(res_ajuste[3], 5)}, ' +
                f'Rp: {round(res_ajuste[4], 3)}',
                fontsize=7
            )
            
            plt.savefig(os.path.join(save_path, f"{id_curva}.png"))
            plt.close()

            logging.info(f"Grafico guardado en: {save_path}/{id_curva}.png")
        except Exception as e:
            logging.error(f"Error al generar el grafico para {id_curva}: {e}")
            raise

    def procesar_carpeta(self, ruta_carpeta, save_path):
        """
        Procesa todos los archivos CSV en una carpeta, ajusta las curvas y guarda los resultados y gráficos.

        Args:
            ruta_carpeta (: Ruta de la carpeta que contiene los archivos CSV.
            save_path (: Ruta para guardar los resultados y gráficos.

        Returns:
            list: Lista de archivos procesados.
        """
        logging.info(f"Procesando carpeta: {ruta_carpeta}")
        try:
            if not os.path.exists(save_path):
                os.makedirs(save_path)

            output_csv_path = os.path.join(save_path, "parametros_ajuste_diodo.csv")
            output_png_path = save_path  # Usar la misma carpeta para guardar los PNG
            
            archivos_procesados = []
            for file_name in os.listdir(ruta_carpeta):
                if file_name.startswith(f"{self.analizador}_{self.dia}") and file_name.endswith(".csv"):
                    file_path = os.path.join(ruta_carpeta, file_name)
                    
                    # Procesar la curva para obtener V_rango, I_rango y P
                    analizador = AnalizadorCurvaIV()
                    V_rango, I_rango, P = analizador.procesar_curva(file_path)
                    
                    # Llamar a procesar_archivo con todos los argumentos necesarios
                    V_rango, I_rango, data_ajustada, res_ajuste = self.procesar_archivo(
                        V_rango, I_rango, P, output_csv_path, output_png_path, file_name
                    )
                    
                    archivos_procesados.append((file_name, V_rango, I_rango, data_ajustada, res_ajuste))
            
            logging.info(f"Carpeta {ruta_carpeta} procesada exitosamente")
            return archivos_procesados
        except Exception as e:
            logging.error(f"Error al procesar la carpeta {ruta_carpeta}: {e}")
            raise

if __name__ == "__main__":

    # Realizar el ajuste a una curva IV de un panel aplicando el método = 'fmin' y completando los datos faltantes
    analizador = AnalizadorCurvaIV()
    V_rango, I_rango, P = analizador.procesar_curva('AnP03_21.06.01_08.09.09.csv')
    analizador.graficar_resultados(
        V_rango,
        I_rango,
        P,
        metodo='fmin',  
        completar_curva=True,  
        data_file_path='2021_06/01/AnP03_21.06.01_08.09.09.csv'
    )

    # Recorrer un dia completo
    ruta_carpeta = '2021_06/01/'
    save_path = 'curvas_ajustadas_fmin'

    metodo = 'fmin'  
    nombre_analizador = 'AnP03'  
    dia = '21.06.01'  

    procesador = Recorrer_dia(metodo, nombre_analizador, dia)
    archivos_procesados = procesador.procesar_carpeta(ruta_carpeta, save_path)