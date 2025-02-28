# Car Price Prediction Web Application and Monitoring System
 
This repository contains the source code and documentation for a comprehensive Car Price Prediction Web Application and Monitoring System. The system includes components for making predictions, visualizing past predictions, model serving via an API, data ingestion with quality validation, scheduled predictions, and monitoring dashboards.
 
## Project Structure
 
The project is structured into several components:
 
### Web Application
 
#### Prediction Page:
- Allows users to make single or multiple predictions using a form or by uploading a CSV file.
- Utilizes a model API service for predictions.
 
#### Past Predictions Page:
- Enables users to visualize past predictions with options to select date range and prediction source.
 
### Model Service (API)
 
#### Endpoints:
- **predict**: For making model predictions from the webapp or the prediction job (single and multi prediction without file input).
- **past-predictions**: To get past predictions along with the used features.
 
### Database
- Utilizes PostgreSQL for storing predictions and data quality issues.
 
### Data Ingestion Job
- **Ingests New Data**: Simulates continuous data flow by ingesting new data at regular intervals.
- **Validates Data Quality**: Validates the quality of ingested data, saves data issues, and generates reports.
- **Error Handling**: Generates various types of data errors for testing and validation purposes.
 
### Prediction Job
- **Scheduled Predictions**: Executes scheduled predictions on ingested data at regular intervals.
 
### Monitoring Dashboards
- **Ingested Data Monitoring Dashboard**: Helps the data operations team monitor ingested data problems.
- **Data Drift and Prediction Issues Dashboard**: Aids ML engineers and data scientists in detecting model or application issues.
 
## Installation
 
### Prerequisites
- Python 3.7+
- PostgreSQL
- Docker (optional for containerized deployment)
 
### Setup
1. Clone the repository
    ```bash
    git clone https://github.com/anandhukrishna1998/car_price_prediction.git
    cd car_price_prediction
    ```
2. Create and activate a virtual environment
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows use `venv\Scripts\activate`
    ```
3. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```
4. Set up the PostgreSQL database
    - Install PostgreSQL and create a database.
    - Update the `DATABASE_URL` in the `.env` file with your PostgreSQL connection string.
 
5. Run database migrations
    ```bash
    alembic upgrade head
    ```
 
6. Start the FastAPI server
    ```bash
    uvicorn app.main:app --reload
    ```
 
7. Start the Streamlit web application
    ```bash
    streamlit run app/webapp.py
    ```
 
8. Set up Airflow
    - Follow the official Airflow installation guide.
    - Configure and start the Airflow scheduler and web server.
 
## Usage
 
### Web Application
 
- **Prediction Page**: Access via (http://34.16.139.133:5002/)
    - Fill in the form for single prediction or upload a CSV file for multi predictions.
    - Click the "Predict" button to get predictions.
 
- **Past Predictions Page**: Access via (http://34.16.139.133:5002/)
    - Select the date range and prediction source to view past predictions.
 
### Model Service (API)
 
- **Make Predictions**: Send a POST request to `/predict` with the required features.
- **Retrieve Past Predictions**: Send a GET request to `/past_predictions`.
 
### Data Ingestion and Prediction Jobs
 
- **Airflow DAGs**: Trigger the data ingestion and prediction jobs via the Airflow UI.
 
### Monitoring Dashboards
 
- **Grafana Dashboards**: Access the Grafana dashboards to monitor ingested data quality and model performance.
 
## Support
 
For support or inquiries related to the project, please feel free to contact me.
 
## Acknowledgements
 
- Streamlit
- FastAPI
- PostgreSQL
- Airflow
- Great Expectations
- Grafana