from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
import os
import glob
import json
import requests
from airflow.exceptions import AirflowSkipException
import pandas as pd


API_BASE_URL = 'http://34.16.139.133:5001'


def check_for_new_data(ti):
    good_data_path = (
        '/mnt/c/Users/Bhargav/car_price_prediction/output_data/good_data/*'
        )
    files = glob.glob(good_data_path)
    print('files are', files)
    last_processed_time = Variable.get(
        "last_processed_time",
        default_var=str(datetime.min)
    )

    print('last_processed_time is', last_processed_time)

    new_files = [
        f for f in files
        if datetime.fromtimestamp(os.path.getmtime(f)) > datetime.fromisoformat(
            last_processed_time
        )
    ]

    print('new_files are', new_files)

    if not new_files:
        print("No new data found, skipping this run.")
        raise AirflowSkipException("No new data found, skipping this run.")

    ti.xcom_push(key='new_files', value=new_files)


def make_predictions_fun(**kwargs):
    new_files = kwargs['ti'].xcom_pull(
        key='new_files',
        task_ids='check_for_new_data'
    )

    print(new_files)
    default_source = "scheduled predictions"
    api_url = f'{API_BASE_URL}/predict/?source={default_source}'

    for file_path in new_files:
        new_data_df = pd.read_csv(file_path)
        new_data_df_data = new_data_df.to_dict(orient='records')
        # This header is technically optional here as requests infers it
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            api_url,
            data=json.dumps({"data": new_data_df_data}),
            headers=headers
        )

        print(response.json())  # Assuming the response is JSON

    # Update the last processed time only if there are new files
    if new_files:
        Variable.set("last_processed_time", str(datetime.now()))


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'prediction_job',
    default_args=default_args,
    description='Scheduled prediction job',
    schedule_interval='*/2 * * * *',
    start_date=days_ago(1),
    catchup=False,
) as dag:

    check_new_data = PythonOperator(
        task_id='check_for_new_data',
        python_callable=check_for_new_data,
        provide_context=True,
    )

    make_predictions = PythonOperator(
        task_id='make_predictions',
        python_callable=make_predictions_fun,
        provide_context=True,
    )

    check_new_data >> make_predictions
