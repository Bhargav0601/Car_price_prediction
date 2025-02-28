import streamlit as st
import pandas as pd
import requests
import datetime
import json

# Set the API base URL as a global variable
API_BASE_URL = "http://34.16.139.133:5001"
st.set_page_config(layout="wide")


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
            past_predictions = (
                response.json()
            )  # Get the past predictions from the response
            return past_predictions
        else:
            st.error(f"Failed to fetch past predictions: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error fetching past predictions: {e}")
        return None


def upload_file(file):
    default_source = "webapp"
    api_url = f"{API_BASE_URL}/predict/?source={default_source}"
    uploaded_file = pd.read_csv(file)
    uploaded_data = uploaded_file.to_dict(orient="records")

    try:
        headers = {
            "Content-Type": "application/json"
        }  # This header is technically optional here as requests infers it

        response = requests.post(
            api_url, data=json.dumps({"data": uploaded_data}), headers=headers
        )

        # Check if the request was successful
        return response.status_code, response.json()
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None


def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to", ["Vehicle Price Prediction", "Past Predictions"])
    if page == "Vehicle Price Prediction":
        # Streamlit app layout
        st.title("Vehicle Price Prediction")

        # Form for user input
        with st.form(key="vehicle_form"):
            year = st.number_input("Year", min_value=1980,
                                   max_value=2024, step=1)
            km_driven = st.number_input("Kilometers Driven", min_value=0)
            seats = st.number_input("Seats", min_value=1, max_value=10, step=1)
            mileage = st.number_input("Mileage (km/l)")
            engine = st.number_input("Engine (CC)")
            max_power = st.number_input("Max Power (bhp)")
            car_company_name = st.text_input("Car Company Name")
            fuel = st.selectbox(
                "Fuel Type", ["Petrol", "Diesel", "CNG", "LPG", "Electric"]
            )
            transmission = st.selectbox("Transmission",
                                        ["Manual", "Automatic"])
            owner = st.selectbox(
                "Owner Type", ["First", "Second", "Third", "Fourth & Above"]
            )

            submit_button = st.form_submit_button(label="Predict Price")

        # POST request to the endpoint
        if submit_button:
            vehicle_data = {
                "year": year,
                "km_driven": km_driven,
                "seats": seats,
                "mileage": mileage,
                "engine": engine,
                "max_power": max_power,
                "car_company_name": car_company_name,
                "fuel": fuel,
                "transmission": transmission,
                "owner": owner,
            }

            data_to_send = [vehicle_data]
            # Endpoint URL
            default_source = "webapp"
            api_url = f"{API_BASE_URL}/predict/?source={default_source}"
            response = requests.post(api_url, data=json.dumps(
                {"data": data_to_send}))

            if response.status_code == 200:
                response_data = response.json()
                print("Response data:", response_data)
                if response_data:

                    predictions_df = pd.DataFrame(response_data["data"])

                    st.dataframe(predictions_df)
            else:

                st.error(f"Failed to predict price. Error: {response.text}")

        st.title("Upload file for prediction ")

        # File uploader widget
        uploaded_file = st.file_uploader("Upload CSV file here :",
                                         type=["csv"])

        # Add a "Predict" button
        if st.button("Predict on CSV file"):
            if uploaded_file is not None:
                # Call the function to upload the file and get predictions

                status_code, predictions_json = upload_file(uploaded_file)
                if status_code == 200:
                    print(predictions_json)
                    # Convert the JSON response to a DataFrame
                    predictions_df = pd.DataFrame(predictions_json["data"])

                    # Display the DataFrame in Streamlit
                    st.write("## Predictions from CSV file")
                    st.dataframe(predictions_df)
            else:
                st.write("Please upload a CSV file to proceed.")
    elif page == "Past Predictions":
        st.title("Past predictions ")

        start_date = st.date_input(
            "Start Date", datetime.date.today() - datetime.timedelta(days=30)
        )
        end_date = st.date_input("End Date", datetime.date.today())
        prediction_source = st.selectbox(
            "Select Prediction Source",
            options=["webapp", "scheduled predictions", "all"],
            index=2,
        )  # Default to 'all'

        if st.button("Fetch Past Predictions"):
            past_predictions = fetch_past_predictions(
                start_date, end_date, source=prediction_source
            )

            if past_predictions:
                # Convert the list of dictionaries to a DataFrame for display
                past_predictions_df = pd.DataFrame(past_predictions)

                st.write("The length of the dataframe is ",
                         len(past_predictions_df))
                st.dataframe(past_predictions_df.head(20))


if __name__ == "__main__":
    main()
