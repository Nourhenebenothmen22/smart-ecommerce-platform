# Price Prediction

This module trains a backend-compatible product price prediction model from PostgreSQL product data.

## Workflow

1. Load dynamic product rows from `products`, `categories`, and `subcategories`.
2. Clean missing values, duplicates, invalid types, invalid ranges, and extreme target outliers.
3. Avoid leaking/invalid fields such as `final_price`, `product_id`, `category_id`, and `subcategory_id`.
4. Use real database `products.price` values as the validation target.
5. Engineer discount, stock, review, text-richness, rating-review, category-combination, and bucket features.
6. Encode categorical variables with unknown/rare-category handling.
7. Scale numeric variables inside sklearn pipelines fitted only on the training split.
8. Train a median baseline and a RandomForest regressor.
9. Evaluate both final models with MAE, RMSE, and R2.
10. Save comparison reports, plots, model artifacts, and model metadata.
11. Serve predictions through the FastAPI `/price/predict` endpoint.

## Models

Baseline model:
`DummyRegressor(strategy="median")`, used to prove the ML model is better than predicting a typical catalog price.

Performant model:
`RandomForestRegressor`, used for nonlinear interactions between category, brand, stock, discount, review, and text features.

Target handling:
The improved baseline uses `log1p(price)` with inverse `expm1` predictions. RandomForest keeps the raw target because this produced better RMSE during validation on the current seeded catalog.

## Commands

```bash
python -m ml.price_prediction.run_pipeline
python -m ml.validation.real_db_validation
```

Generated artifacts are written to `ml/artifacts/price_prediction/`.

Real database validation artifacts are written to a new non-overwriting folder:

```text
ml/artifacts/validation/ml_validation_<models>_<yyyymmdd_hhmmss>_v<versions>/
```

## Evaluation Outputs

```text
ml/artifacts/price_prediction/reports/model_comparison.csv
ml/artifacts/price_prediction/reports/preprocessing_report.json
ml/artifacts/price_prediction/models/metadata.json
```

## Plots

```text
ml/artifacts/price_prediction/plots/price_distribution.png
ml/artifacts/price_prediction/plots/feature_correlation.png
ml/artifacts/price_prediction/plots/actual_vs_predicted_price.png
ml/artifacts/price_prediction/plots/model_performance_comparison.png
```

Plot explanations:

* `price_distribution.png`: cleaned price distribution and skew.
* `feature_correlation.png`: numeric feature correlation with price.
* `actual_vs_predicted_price.png`: held-out actual prices versus selected model predictions.
* `model_performance_comparison.png`: MAE, MSE, RMSE, and R2 for the final baseline and RandomForest models.

The real DB validation workflow also writes:

* `plots/price_prediction_actual_vs_predicted_<run_id>.png`
* `plots/price_prediction_model_metrics_<run_id>.png`
* `price_prediction/price_prediction_holdout_predictions_<run_id>.csv`
* `reports/ml_validation_report_<run_id>.json`

## API Usage

FastAPI:

```bash
curl -X POST http://127.0.0.1:8000/price/predict \
  -H "Content-Type: application/json" \
  -H "X-ML-Service-Token: $ML_SERVICE_TOKEN" \
  -d '{"product_id": 10}'
```

Backend gateway:

```bash
curl -X POST http://127.0.0.1:5000/api/ml/price/predict \
  -H "Authorization: Bearer <admin_jwt>" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 10}'
```
