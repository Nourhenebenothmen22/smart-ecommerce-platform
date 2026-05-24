# Price Prediction

This module trains a backend-compatible product price prediction model from PostgreSQL product data.

## Workflow

1. Load dynamic product rows from `products`, `categories`, and `subcategories`.
2. Engineer numeric and categorical features.
3. Train a median baseline and a RandomForest regressor.
4. Evaluate both models with MAE, MSE, RMSE, and R2.
5. Save comparison reports, plots, model artifacts, and model metadata.
6. Serve predictions through the FastAPI `/price/predict` endpoint.

## Commands

```bash
python -m ml.price_prediction.run_pipeline
```

Generated artifacts are written to `ml/artifacts/price_prediction/`.

