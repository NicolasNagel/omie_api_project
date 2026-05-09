from datetime import datetime

from airflow.sdk import dag, task

from src.data_collector.omie_collector import OMIECollector

@dag(
    dag_id='OMIE_collector_pipeline',
    description='Coleta de Dados da API da OMIE',
    start_date=datetime(2026, 5, 9),
    schedule='@hourly',
    catchup=False
)
def pipeline():

    @task
    def pipeline_collector():
        collector = OMIECollector().collect_all()
        return collector
    
    t1 = pipeline_collector()

pipeline()