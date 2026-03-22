from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id='iv_curve_filter_single_run',
    start_date=datetime(2025, 1, 1),
    schedule=None,  # <-- ASÍ SE HACE AHORA
    catchup=False,
) as dag:
    run_main_script = BashOperator(
        task_id='run_main_py',
        bash_command='python /opt/airflow/src/scripts/main.py',
    )