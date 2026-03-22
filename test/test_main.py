import pytest
from unittest.mock import MagicMock
from conexion import CurvaProcessor, DatabaseManager

@pytest.fixture
def db_manager():
    db_manager = DatabaseManager(
        host='localhost',
        user='root',
        password='tu_contraseña',
        port=3306,
        database='tu_BBDD'
    )
    db_manager.connect()
    yield db_manager
    db_manager.disconnect()

@pytest.fixture
def curva_processor(db_manager):
    return CurvaProcessor(db_manager)

def test_procesar_curva(curva_processor, mocker):
    # Datos simulados
    mock_resultados = ('{"Voltaje": [0.2, 0.4, 0.6], "Corriente": [1.0, 2.0, 3.0]}',)
    mock_timestamp = ('timestamp[0]',)
    
    # Simular métodos y clases
    mock_procesador = mocker.patch('main.Recorrer_dia', autospec=True)
    curva_processor.db_manager.execute_query = MagicMock(side_effect=[mock_resultados, mock_timestamp])

    # Ejecutar el procesamiento
    curva_processor.procesar_curva(mock_resultados, mock_timestamp)

    # Verificar si los datos fueron procesados
    mock_procesador.return_value.procesar_archivo.assert_called_once_with(
        [0.2, 0.4, 0.6], [1.0, 2.0, 3.0], [0.2 * 1.0, 0.4 * 2.0, 0.6 * 3.0],
        'nombre_archivo.csv', 'ruta/imagenes/', 'timestamp[0]'
    )


