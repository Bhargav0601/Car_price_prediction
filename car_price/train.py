import numpy as np
import pandas as pd
from xgboost import XGBRegressor
import joblib
from sklearn.metrics import mean_squared_log_error
from sklearn.metrics import r2_score
import os
from .preprocess import clean_and_fill_data
from .preprocess import preprocess_features
from sklearn.model_selection import train_test_split
from typing import Dict
from . import NUMERICAL_FEATURES, CATEGORICAL_FEATURES


def train_model(X_train: np.array, y_train: pd.Series,
                model_dir: str) -> None:
    param = {
        'max_depth': 4,
        'objective': 'reg:squarederror',
        'learning_rate': 0.1,
        'n_estimators': 200,
        'subsample': 0.7,
        'colsample_bytree': 0.8,
        'eval_metric': 'rmse'
    }
    model = XGBRegressor(**param)
    model.fit(X_train, y_train)
    joblib.dump(model, os.path.join(model_dir, 'model.joblib'))


def compute_rmsle(y_test: np.ndarray, y_pred: np.ndarray,
                  precision: int = 2) -> float:
    rmsle = np.sqrt(mean_squared_log_error(y_test, y_pred))
    return round(rmsle, precision)


def evaluate_performance(y_test, y_pred) -> Dict[str, float]:
    rmsle_score = compute_rmsle(np.log(y_test), np.log(y_pred))
    mse = np.mean((y_test - y_pred) ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(y_test - y_pred))
    r2 = r2_score(y_test, y_pred)
    evaluation_results = {
        "rmsle_score": rmsle_score,
        "MSE": mse,
        "RMSE": rmse,
        "MAE": mae,
        "R^2": r2
                }
    return evaluation_results


def model_training(X_train, y_train, model_dir) -> None:
    X_train = clean_and_fill_data(X_train)
    X_train_processed = preprocess_features(
        X_train,
        NUMERICAL_FEATURES,
        CATEGORICAL_FEATURES,
        model_dir,
        'train')
    train_model(X_train_processed, y_train, model_dir)


def model_evaluation(X_test, y_test, model_dir) -> Dict[str, float]:
    X_test = clean_and_fill_data(X_test)

    X_test_processed = preprocess_features(
        X_test,
        NUMERICAL_FEATURES,
        CATEGORICAL_FEATURES,
        model_dir,
        'test')
    model = joblib.load(os.path.join(model_dir, 'model.joblib'))
    y_pred = model.predict(X_test_processed)

    evaluation_results = evaluate_performance(y_test, y_pred)
    return evaluation_results


def build_model(data: pd.DataFrame) -> Dict[str, float]:
    model_dir = '../models'
    X = data.drop(columns=['selling_price'])
    y = data['selling_price']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    model_training(X_train, y_train, model_dir)
    performances = model_evaluation(X_test, y_test, model_dir)
    return performances
