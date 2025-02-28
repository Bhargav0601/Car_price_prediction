import os
import pandas as pd
import random
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.exc import SQLAlchemyError
import requests
import json
from great_expectations.dataset.pandas_dataset import PandasDataset
from great_expectations.data_context.data_context import DataContext
from airflow.operators.python import BranchPythonOperator
from great_expectations.core.batch import BatchRequest
import time
from sqlalchemy import DateTime, JSON

# Define the global path variable
RAW_DATA_PATH = "/mnt/c/Users/Bhargav/car_price_prediction/data"
# Initialize the storage paths for good and bad data
good_data_path = os.path.join(
    "/mnt/c/Users/Bhargav/car_price_prediction/output_data/good_data"
)
bad_data_path = os.path.join(
    "/mnt/c/Users/Bhargav/car_price_prediction/output_data/bad_data"
)


def read_data(**kwargs):

    files = os.listdir(RAW_DATA_PATH)
    selected_file = random.choice(files)
    file_path = os.path.join(RAW_DATA_PATH, selected_file)
    print("file_path in   read_datais ", file_path)
    kwargs["ti"].xcom_push(key="file_path", value=file_path)


def validate_data(**kwargs):
    # Extract the file path from Airflow XCom (assuming Airflow context)
    file_path = kwargs["ti"].xcom_pull(key="file_path", task_ids="read_data")
    print("file_path in validate_data is ", file_path)
    data_asset_name = os.path.basename(file_path).split(".")[0]
    print("data_asset_name is ", data_asset_name)

    # Load data into a DataFrame
    df = pd.read_csv(file_path)

    # Initialize Great Expectations context
    context = DataContext(context_root_dir="/home/bhargav06/airflow/great_expectations/")

    # Load the existing expectation suite
    expectation_suite_name = "my_ex"
    expectation_suite = context.get_expectation_suite(expectation_suite_name)

    # Create a GE DataFrame, attaching the expectation suite
    ge_df = PandasDataset(df)
    ge_df._initialize_expectations(expectation_suite)

    # Validate the data against the expectations
    validation_results = ge_df.validate()

    # Push validation results and Run ID to XCom
    run_id = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    kwargs["ti"].xcom_push(key="validation_results", value=validation_results)
    kwargs["ti"].xcom_push(key="run_id", value=run_id)

    if validation_results["success"]:
        print(file_path, "is good data")
        kwargs["ti"].xcom_push(key="data_quality", value="good_data")
        return "save_file"
    else:
        print(file_path, "is bad data")
        kwargs["ti"].xcom_push(key="data_quality", value="bad_data")

        # Define the batch request for loading data correctly
        batch_request = BatchRequest(
            datasource_name="my_csv_datasource",
            data_connector_name="default_inferred_data_connector_name",
            data_asset_name=data_asset_name,
        )

        # Create a checkpoint for validation
        checkpoint_name = f"my_checkpoint_{int(time.time())}"
        context.add_checkpoint(
            name=checkpoint_name,
            config_version=1,
            class_name="SimpleCheckpoint",
            validations=[
                {
                    "batch_request": batch_request.to_json_dict(),
                    "expectation_suite_name": expectation_suite_name,
                }
            ],
        )

        # Run the checkpoint
        context.run_checkpoint(checkpoint_name=checkpoint_name)

        # Build and print the location of Data Docs
        context.build_data_docs()
        data_docs_site = context.get_docs_sites_urls()[0]["site_url"]
        print(f"Data Docs generated at: {data_docs_site}")
        return ["send_alerts", "save_data_errors", "save_file"]


def send_alerts(**kwargs):
    validation_results = kwargs["ti"].xcom_pull(
        key="validation_results", task_ids="validate_data"
    )
    run_id = kwargs["ti"].xcom_pull(key="run_id", task_ids="validate_data")
    file_path = kwargs["ti"].xcom_pull(key="file_path", task_ids="read_data")
    df = pd.read_csv(file_path)

    failed_expectations = [
        result
        for result in validation_results["results"]
        if not result["success"]
    ]
    print('validation_results is ', validation_results)
    print('failed_expectations is ', failed_expectations)
    total_failed_count = len(failed_expectations)
    error_summary = os.linesep.join(
        [
            f"- Expectation {index + 1}: "
            f"{expectation['expectation_config']['expectation_type']} "
            f"failed with "
            f"{expectation['result'].get('unexpected_count', 'no')} "
            f"unexpected values. "
            for index, expectation in enumerate(failed_expectations)
        ]
    )
    teams_webhook_url = (
        "https://epitafr.webhook.office.com/webhookb2/66c8b7ae-6477-4603-9a5b-"
        "49d5f2191a91@3534b3d7-316c-4bc9-9ede-605c860f49d2/IncomingWebhook/"
        "f76d2dd16d7e44189ed49093915d8360/4981d105-4c57-4ae4-ac72-2623b4a8b6b8"
    )
    headers = {"Content-Type": "application/json"}

    bad_rows_indices = set()

    # Process each result to find failed expectations and their indices
    for result in validation_results["results"]:
        if not result["success"]:
            if (
                "partial_unexpected_list" in result["result"]
                and result["result"]["partial_unexpected_list"]
            ):
                '''Assume partial_unexpected_list contains the row indices
                (this might need adjustment based on actual data structure)'''
                for value in result["result"]["partial_unexpected_list"]:
                    ''' Find all occurrences of this unexpected
                    value in the specified column'''
                    column = result["expectation_config"]["kwargs"]["column"]
                    condition = df[column] == value
                    index_list = df.index[condition].tolist()

                    bad_rows_indices.update(index_list)
    bad_rows_indices_len = len(bad_rows_indices)
    kwargs["ti"].xcom_push(
        key="bad_rows_indices_len",
        value=bad_rows_indices_len
        )

    if bad_rows_indices_len > 5:
        criticality = "high"
    elif bad_rows_indices_len > 3:
        criticality = "medium"
    else:
        criticality = "low"

    kwargs["ti"].xcom_push(key="criticality", value=criticality)
    alert_message = {
        "text": (
            f"Data Problem Alert (Run ID: {run_id} look at this run id "
            f"in the datadocs):\n\n "
            f"filepath is: {file_path}\n\n "
            f"Criticality: {criticality}\n\n "
            f"Number of failed rows: {len(bad_rows_indices)}\n\n "
            f"Summary: {total_failed_count} expectations "
            f"failed validation.\n\n "
            f"Error Details:\n\n{error_summary}\n\n "
            f"Check the detailed report here: [Data Docs] "
            f"(http://34.16.139.133:8000/index.html) "
        )
    }

    print("alert_message is", alert_message)

    try:
        response = requests.post(teams_webhook_url, headers=headers,
                                 json=alert_message)
        if response.status_code == 200:
            print("Alert sent to Teams successfully.")
        else:
            print(f"Failed to send alert to Teams."
                  f"Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending alert to Teams: {e}")


def save_file(**kwargs):
    # Retrieve data from XCom
    file_path = kwargs["ti"].xcom_pull(key="file_path", task_ids="read_data")
    validation_results = kwargs["ti"].xcom_pull(
        key="validation_results", task_ids="validate_data"
    )
    df = pd.read_csv(file_path)
    # Initialize an empty set to collect indices of rows with issues
    bad_rows_indices = set()

    # Process each result to find failed expectations and their indices
    for result in validation_results["results"]:
        if not result["success"]:
            if (
                "partial_unexpected_list" in result["result"]
                and result["result"]["partial_unexpected_list"]
            ):
                '''Assume partial_unexpected_list contains the row indices
                 (this might need adjustment
                 based on actual data structure) '''
                for value in result["result"]["partial_unexpected_list"]:
                    '''Find all occurrences of this
                    unexpected value in the specified column'''
                    index_list = df.index[
                        df[result["expectation_config"]["kwargs"]
                           ["column"]] == value
                    ].tolist()
                    bad_rows_indices.update(index_list)

    # Split the DataFrame
    df_bad = df.iloc[list(bad_rows_indices)]
    df_good = df.drop(index=list(bad_rows_indices))

    # Ensure directories exist
    os.makedirs(good_data_path, exist_ok=True)
    os.makedirs(bad_data_path, exist_ok=True)

    # Save the DataFrames
    good_file_path = os.path.join(good_data_path, os.path.basename(file_path))
    bad_file_path = os.path.join(bad_data_path, os.path.basename(file_path))

    if not df_good.empty:
        df_good.to_csv(good_file_path, index=False)
        print(f"Saved good data to {good_file_path}")

    if not df_bad.empty:
        df_bad.to_csv(bad_file_path, index=False)
        print(f"Saved bad data to {bad_file_path}")

    # Remove the original file
    os.remove(file_path)


def save_data_errors(**kwargs):
    file_path = kwargs["ti"].xcom_pull(key="file_path", task_ids="read_data")
    validation_results = kwargs["ti"].xcom_pull(
        key="validation_results", task_ids="validate_data"
    )
    total_rows = len(validation_results["results"])
    criticality = kwargs["ti"].xcom_pull(key="criticality",
                                         task_ids="send_alerts")
    bad_rows_indices_len = kwargs["ti"].xcom_pull(
        key="bad_rows_indices_len", task_ids="send_alerts"
    )
    error_details = {
        result["expectation_config"]["expectation_type"]: result["result"].get(
            "unexpected_count", 0  # Assuming '0' as a sensible default
        )
        for result in validation_results["results"]
        if not result["success"]
    }

    db_connection_string = "postgresql://car:password@34.16.139.133/carprice"
    engine = create_engine(db_connection_string)

    metadata = MetaData()

    data_quality_table = Table(
        "data_quality_statistics",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("total_rows", Integer),
        Column("failed_rows", Integer),
        Column("timestamp", DateTime),
        Column("file_path", String(500)),
        Column("criticality", String(500)),
        Column("error_details", JSON),
    )

    metadata.create_all(engine)

    try:
        with engine.connect() as connection:
            insert_query = data_quality_table.insert().values(
                total_rows=total_rows,
                failed_rows=bad_rows_indices_len,
                timestamp=datetime.datetime.now(),
                file_path=file_path,
                criticality=criticality,
                error_details=json.dumps(error_details),
            )
            connection.execute(insert_query)
            print("Data quality statistics saved to the database.")
    except SQLAlchemyError as e:
        print(f"Error saving data quality statistics to the database: {e}")


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.datetime(2023, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
}

dag = DAG(
    "data_ingestion_pipelines",
    default_args=default_args,
    schedule_interval="* * * * *",
    catchup=False,
)


read_data_task = PythonOperator(
    task_id="read_data",
    python_callable=read_data,
    provide_context=True,
    dag=dag,
)

validate_data_task = BranchPythonOperator(
    task_id="validate_data",
    python_callable=validate_data,
    dag=dag,
)


send_alerts_task = PythonOperator(
    task_id="send_alerts",
    python_callable=send_alerts,
    provide_context=True,
    dag=dag,
    trigger_rule="all_success",
)

save_file_task = PythonOperator(
    task_id="save_file",
    python_callable=save_file,
    provide_context=True,
    dag=dag,
)

save_data_errors_task = PythonOperator(
    task_id="save_data_errors",
    python_callable=save_data_errors,
    provide_context=True,
    dag=dag,
    trigger_rule="all_success",
)

read_data_task >> validate_data_task
validate_data_task >> save_file_task
validate_data_task >> send_alerts_task
validate_data_task >> save_data_errors_task
