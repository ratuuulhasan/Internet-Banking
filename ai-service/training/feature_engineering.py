"""
Feature engineering for fraud detection.
Extracts features from raw transaction data.
"""
import numpy as np
import pandas as pd


def extract_features(raw_transaction: dict) -> dict:
    """
    Extract engineered features from a raw transaction.
    
    Input:
        raw_transaction = {
            'amount': 5000.0,
            'hour': 14,
            'txn_type': 1,
            'device_change': 0,
            'location_change': 0,
            'account_age_days': 365,
            'txn_count_24h': 3,
            'avg_amount_24h': 3000.0,
        }
    
    Output: dict of engineered features
    """
    amount = float(raw_transaction.get('amount', 0))
    hour = int(raw_transaction.get('hour', 12))
    txn_type = int(raw_transaction.get('txn_type', 1))
    device_change = int(raw_transaction.get('device_change', 0))
    location_change = int(raw_transaction.get('location_change', 0))
    account_age_days = int(raw_transaction.get('account_age_days', 0))
    txn_count_24h = int(raw_transaction.get('txn_count_24h', 1))
    avg_amount_24h = float(raw_transaction.get('avg_amount_24h', amount))

    features = {
        # Basic
        'amount': amount,
        'log_amount': np.log1p(amount),

        # Time features
        'hour': hour,
        'is_night': 1 if hour in [0, 1, 2, 3, 4, 5] else 0,
        'is_business_hours': 1 if 9 <= hour <= 17 else 0,

        # Transaction context
        'txn_type': txn_type,
        'device_change': device_change,
        'location_change': location_change,

        # Account features
        'account_age_days': account_age_days,
        'is_new_account': 1 if account_age_days < 30 else 0,

        # Velocity features
        'txn_count_24h': txn_count_24h,
        'is_high_velocity': 1 if txn_count_24h > 10 else 0,

        # Amount anomaly
        'amount_vs_avg_ratio': amount / (avg_amount_24h + 1),
        'is_large_amount': 1 if amount > avg_amount_24h * 3 else 0,
        'is_small_amount': 1 if amount < 10 else 0,  # fraudsters test with small amounts

        # Combined risk signals
        'night_plus_device_change': 1 if (hour in [0,1,2,3,4,5] and device_change) else 0,
        'new_account_plus_large': 1 if (account_age_days < 30 and amount > avg_amount_24h * 3) else 0,
        'location_and_device_change': device_change + location_change,
    }
    return features


FEATURE_COLUMNS = [
    'amount', 'log_amount', 'hour', 'is_night', 'is_business_hours',
    'txn_type', 'device_change', 'location_change', 'account_age_days',
    'is_new_account', 'txn_count_24h', 'is_high_velocity',
    'amount_vs_avg_ratio', 'is_large_amount', 'is_small_amount',
    'night_plus_device_change', 'new_account_plus_large',
    'location_and_device_change',
]


def features_to_vector(features: dict) -> list:
    """Convert features dict to ordered list for model input."""
    return [float(features.get(k, 0)) for k in FEATURE_COLUMNS]