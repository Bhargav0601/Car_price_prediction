from .preprocess import clean_and_fill_data
from .preprocess import preprocess_features
import joblib
import os
import pandas as pd
from . import NUMERICAL_FEATURES, CATEGORICAL_FEATURES


def make_predictions(test_data: pd.DataFrame) -> pd.DataFrame:
    model_dir = "./models"
    test_data_cleand = clean_and_fill_data(test_data)

    test_data_processed = preprocess_features(
        test_data_cleand, NUMERICAL_FEATURES, CATEGORICAL_FEATURES,
        model_dir, "test"
    )

    model = joblib.load(os.path.join(model_dir, "model.joblib"))
    test_data_pred = model.predict(test_data_processed)
    return test_data_pred
