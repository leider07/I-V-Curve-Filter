# Usa la imagen oficial de Apache Airflow como base
FROM apache/airflow:2.10.5

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /opt/airflow

# Copia los archivos de definición de dependencias
COPY pyproject.toml poetry.lock /opt/airflow/

# Instala Poetry y las dependencias del proyecto
RUN pip install --no-cache-dir poetry && poetry install --no-root

# Copia el resto de los archivos de tu proyecto al contenedor
COPY . /opt/airflow

# Comando por defecto al iniciar
CMD ["airflow", "celery", "worker"]