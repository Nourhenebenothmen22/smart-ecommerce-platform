# Price Prediction

This module trains a backend-compatible product price prediction model from PostgreSQL product data.

## Workflow

1. Load dynamic product rows from `products`, `categories`, `subcategories`, `orders`, `order_items`, `user_interactions`, `reviews`, `cart_items`, and `wishlists`.
2. Clean missing values, duplicates, invalid types, invalid ranges, and extreme target outliers.
3. Avoid leaking/invalid fields such as `final_price`, `product_id`, `category_id`, and `subcategory_id`.
4. Use real database `products.price` values as the validation target.
5. Engineer discount, stock, review, text-richness, rating-review, sales-history, historical-price, demand, cart, wishlist, category-combination, and bucket features.
6. Encode categorical variables with unknown/rare-category handling.
7. Add train-only target mean price priors for brand/category/subcategory without leaking holdout targets.
8. Scale numeric variables inside sklearn pipelines fitted only on the training split.
9. Train a median baseline and a RandomForest regressor.
10. Evaluate both final models with MAE, RMSE, and R2.
11. Save artifacts only after validation succeeds, replacing the previous valid artifact.
12. Serve predictions through the FastAPI `/price/predict` endpoint.

## Real Pricing Signals

Available in the current PostgreSQL schema:

* Sales history: `order_items` joined to `orders`.
* Historical price proxy: `order_items.unit_price`, with min/max/average/stddev.
* Order quantity and demand: order line count, total quantity sold, fulfilled quantity, distinct buyers, revenue, sales velocity.
* Stock movement: current `products.stock` combined with quantity sold and demand ratios.
* Product demand: `user_interactions` counts for views, clicks, add-to-cart, wishlist, purchase, share, and search.
* Cart and wishlist pressure: `cart_items` and `wishlists`.
* Customer/review behavior: review count, verified reviews, positive/negative review counts, average review rating.
* Category price priors: brand/category/subcategory target mean encodings fitted only on the training split.

Not available yet in the database:

* Supplier cost.
* Profit margin.
* Dedicated campaign or promotion tables.
* Product specification tables.
* Dedicated product price history table.

## Models

Baseline model:
`DummyRegressor(strategy="median")`, used to prove the ML model is better than predicting a typical catalog price.

Performant model:
`RandomForestRegressor`, used for nonlinear interactions between category, brand, stock, discount, reviews, text, sales history, historical unit prices, and demand features.

Target handling:
The improved baseline uses `log1p(price)` with inverse `expm1` predictions. RandomForest keeps the raw target because this produced better RMSE during validation on the current seeded catalog.

## Commands

```bash
python -m ml.price_prediction.run_pipeline
python -m ml.validation.real_db_validation
```

Generated artifacts are written to `ml/artifacts/price_prediction/`.

The project keeps only the latest valid price prediction artifact. Training writes to a temporary staging folder first. If model files, reports, plots, raw data, processed data, and metadata validate successfully, the old artifact folder is replaced. If validation fails, the previous valid artifact remains.

```text
ml/artifacts/price_prediction/
  model/
  plots/
  reports/
  data/
    raw/
    processed/
  metadata/
```

Real database validation artifacts are latest-only:

```text
ml/artifacts/validation/
```

## Evaluation Outputs

```text
ml/artifacts/price_prediction/reports/model_comparison.csv
ml/artifacts/price_prediction/reports/preprocessing_report.json
ml/artifacts/price_prediction/metadata/metadata.json
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

* `ml/artifacts/validation/plots/price_prediction_actual_vs_predicted_latest_validation.png`
* `ml/artifacts/validation/plots/price_prediction_model_metrics_latest_validation.png`
* `ml/artifacts/validation/price_prediction/data/processed/price_prediction_holdout_predictions.csv`
* `ml/artifacts/validation/reports/ml_validation_report_latest_validation.json`

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
