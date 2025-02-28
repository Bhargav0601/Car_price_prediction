import numpy as np
import pandas as pd
import joblib
import os
from sklearn.preprocessing import StandardScaler, OneHotEncoder


def clean_and_fill_data(data: pd.DataFrame) -> pd.DataFrame:

    numerical_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = data.select_dtypes(exclude=[np.number]).columns.tolist()
    for col in numerical_cols:
        data[col] = data[col].fillna(data[col].mean())
    for col in categorical_cols:
        data[col] = data[col].fillna(data[col].mode()[0])
    return data


def scale_numeric_features(data, numeric_features, model_dir,
                           mode='train') -> np.ndarray:
    """
    Scale numeric features.

    Args:
    - data: DataFrame with data.
    - numeric_features: List of numeric feature names to scale.
    - model_dir: Directory path for saving/loading the scaler object.
    - mode: 'train' for training mode, 'test' for testing mode.

    Returns:
    - A numpy array of scaled numeric features.
    """
    scaler_path = os.path.join(model_dir, 'scaler.joblib')

    if mode == 'train':
        scaler = StandardScaler()
        scaler.fit(data[numeric_features])
        joblib.dump(scaler, scaler_path)
    else:
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler object not found"
                                    f" at {scaler_path}. Please fit it"
                                    f" in train mode.")
        scaler = joblib.load(scaler_path)

    data_scaled = scaler.transform(data[numeric_features])

    return data_scaled


def encode_categorical_features(data, categorical_features,
                                model_dir, mode='train') -> np.ndarray:
    """
    Encode categorical features.

    Args:
    - data: DataFrame with data.
    - categorical_features: List of categorical feature names to encode.
    - model_dir: Directory path for saving/loading the encoder object.
    - mode: 'train' for training mode, 'test' for testing mode.

    Returns:
    - A numpy array of encoded categorical features.
    """
    encoder_path = os.path.join(model_dir, 'encoder.joblib')

    if mode == 'train':
        encoder = OneHotEncoder(handle_unknown='ignore')
        encoder.fit(data[categorical_features])
        joblib.dump(encoder, encoder_path)
    else:
        if not os.path.exists(encoder_path):
            raise FileNotFoundError(f"Encoder object not found\
                                    at {encoder_path}. Please fit it\
                                    in train mode.")
        encoder = joblib.load(encoder_path)

    data_encoded = encoder.transform(data[categorical_features]).toarray()

    return data_encoded


def preprocess_features(data, numeric_features, categorical_features,
                        model_dir, mode='train') -> np.ndarray:
    data_encoded = encode_categorical_features(data, categorical_features,
                                               model_dir, mode)
    data_scaled = scale_numeric_features(data, numeric_features,
                                         model_dir, mode)

    processed_data = np.hstack((data_scaled, data_encoded))

    return processed_data
