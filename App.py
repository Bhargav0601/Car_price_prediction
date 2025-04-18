from flask import Flask, request, jsonify, render_template
import pandas as pd
import requests
import datetime
import json
from datetime import date

app = Flask(__name__)

# Set the API base URL as a global variable
API_BASE_URL = "http://34.16.139.133:5001"

def fetch_past_predictions(start_date, end_date, source):
    # API endpoint URL for fetching past predictions
    api_url = (
        f"{API_BASE_URL}/past-predictions?"
        f"start_date={start_date}&"
        f"end_date={end_date}&"
        f"source={source}"
    )

    try:
        # Send GET request to the API endpoint with the date range
        response = requests.get(api_url)
        if response.status_code == 200:
            past_predictions = response.json()  # Get the past predictions from the response
            return past_predictions
        else:
            return None
    except Exception as e:
        print(f"Error fetching past predictions: {e}")
        return None

def upload_file(file):
    default_source = "webapp"
    api_url = f"{API_BASE_URL}/predict/?source={default_source}"
    uploaded_file = pd.read_csv(file)
    uploaded_data = uploaded_file.to_dict(orient="records")

    try:
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            api_url, data=json.dumps({"data": uploaded_data}), headers=headers
        )
        return response.status_code, response.json()
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        vehicle_data = {
            "year": int(request.form['year']),
            "km_driven": int(request.form['km_driven']),
            "seats": int(request.form['seats']),
            "mileage": float(request.form['mileage']),
            "engine": float(request.form['engine']),
            "max_power": float(request.form['max_power']),
            "car_company_name": request.form['car_company_name'],
            "fuel": request.form['fuel'],
            "transmission": request.form['transmission'],
            "owner": request.form['owner'],
        }

        data_to_send = [vehicle_data]
        default_source = "webapp"
        api_url = f"{API_BASE_URL}/predict/?source={default_source}"
        response = requests.post(api_url, data=json.dumps({"data": data_to_send}))

        if response.status_code == 200:
            response_data = response.json()
            predictions_df = pd.DataFrame(response_data["data"])
            return jsonify({
                'status': 'success',
                'prediction': predictions_df.to_dict(orient='records')[0]
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f"Failed to predict price. Error: {response.text}"
            }), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/predict_csv', methods=['POST'])
def predict_csv():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected'}), 400
    
    if file and file.filename.endswith('.csv'):
        status_code, predictions_json = upload_file(file)
        if status_code == 200:
            predictions_df = pd.DataFrame(predictions_json["data"])
            return jsonify({
                'status': 'success',
                'predictions': predictions_df.to_dict(orient='records')
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get predictions from API'
            }), 400
    else:
        return jsonify({
            'status': 'error',
            'message': 'Invalid file type. Please upload a CSV file.'
        }), 400

@app.route('/past_predictions', methods=['POST'])
def past_predictions():
    try:
        data = request.get_json()
        start_date = data['start_date']
        end_date = data['end_date']
        prediction_source = data['source']
        
        past_predictions = fetch_past_predictions(
            start_date, end_date, source=prediction_source
        )

        if past_predictions:
            past_predictions_df = pd.DataFrame(past_predictions)
            return jsonify({
                'status': 'success',
                'predictions': past_predictions_df.head(20).to_dict(orient='records'),
                'count': len(past_predictions_df)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No predictions found for the given criteria'
            }), 404
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)