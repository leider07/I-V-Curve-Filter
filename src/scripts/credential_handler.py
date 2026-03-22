import os
import json

class CredentialHandler:
    def __init__(self, credentials_dir):
        """
        Inicializa el manejador de credenciales.

        Args:
            credentials_dir (str): Ruta a la carpeta que contiene los archivos de credenciales.
        """
        self.credentials_dir = credentials_dir

    def load_server_credentials(self):
        """
        Carga las credenciales del servidor desde un archivo JSON.

        Returns:
            dict: Un diccionario con las credenciales del servidor.
        """
        server_creds_path = os.path.join(self.credentials_dir, 'server_creds.json')
        return self._load_json(server_creds_path)

    def load_db_credentials(self):
        """
        Carga las credenciales de la base de datos desde un archivo JSON.

        Returns:
            dict: Un diccionario con las credenciales de la base de datos.
        """
        db_creds_path = os.path.join(self.credentials_dir, 'db_creds.json')
        return self._load_json(db_creds_path)

    def _load_json(self, file_path):
        """
        Carga un archivo JSON y devuelve su contenido.

        Args:
            file_path (str): Ruta del archivo JSON a cargar.

        Returns:
            dict: Contenido del archivo JSON.

        Raises:
            Exception: Si hay un error al cargar el archivo.
        """
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error al cargar el archivo {file_path}: {e}")
            raise