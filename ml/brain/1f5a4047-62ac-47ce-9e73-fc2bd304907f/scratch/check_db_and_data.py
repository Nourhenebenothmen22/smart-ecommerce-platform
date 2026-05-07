import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(os.getcwd())

from ml.customer_segmentation.data_loader import get_engine, load_and_prepare
from ml.customer_segmentation.config import cfg
from sqlalchemy import text

def audit_database():
    print("--- Auditing Database ---")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Check view columns
            res = conn.execute(text("SELECT * FROM v_user_behavior_features LIMIT 1"))
            print(f"Columns in v_user_behavior_features: {list(res.keys())}")
            
            # Check row count
            count = conn.execute(text("SELECT COUNT(*) FROM v_user_behavior_features")).scalar()
            print(f"Total users in database: {count}")
            
            if count == 0:
                print("WARNING: No data found in v_user_behavior_features!")
                
    except Exception as e:
        print(f"Database Error: {e}")

def audit_data_loader():
    print("\n--- Auditing Data Loader ---")
    try:
        df = load_and_prepare(cfg, force_reload=True)
        print(f"Data shape: {df.shape}")
        print("Feature summary:")
        print(df.describe().T[['mean', 'std', 'min', 'max']])
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            print("\nMissing values detected:")
            print(missing[missing > 0])
            
    except Exception as e:
        print(f"Data Loading Error: {e}")

if __name__ == "__main__":
    audit_database()
    audit_data_loader()
