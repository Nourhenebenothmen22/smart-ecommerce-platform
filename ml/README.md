# Machine Learning Workspace

This folder contains the Python ML services and pipelines for the e-commerce platform.

## Installation

```powershell
pip install -r requirements.txt
```

## Customer Segmentation

The customer segmentation pipeline trains clustering models from backend-generated `user_features`.

```powershell
python -m ml.customer_segmentation.run_pipeline
```

Outputs are stored under `ml/artifacts/customer_segmentation/`.

## Real Database ML Validation

Use the real database validation workflow before promoting segmentation or price models:

```powershell
python -m ml.validation.real_db_validation
```

It trains and validates:

* client segmentation from `user_features`;
* price prediction baseline from `products`, `categories`, and `subcategories`;
* price prediction performant model from the same real product rows.

The workflow:

* removes duplicate product rows and invalid prices;
* clips invalid numeric ranges such as negative stock, negative review counts, discount values outside `0..100`, and ratings outside `0..5`;
* removes extreme target outliers using configured quantile bounds;
* avoids leaking or invalid features by excluding `final_price`, `product_id`, `category_id`, and `subcategory_id`;
* creates discount, stock, review, text-richness, rating-review, category-combination, and bucket features;
* encodes categorical variables with unknown/rare-category handling;
* scales numeric variables inside sklearn pipelines fitted only on the training split;
* evaluates price models with MAE, RMSE, and R2 against real database prices;
* evaluates segmentation with train/test/current clustering metrics;
* checks leakage, overfitting/underfitting, outliers, invalid records, and train/test/current data drift.

Every run creates a new non-overwriting folder:

```text
ml/artifacts/validation/ml_validation_<models>_<yyyymmdd_hhmmss>_v<versions>/
```

Inside it:

* `reports/ml_validation_report_<run_id>.json`
* `client_segmentation/client_segmentation_kmeans_<run_id>.pkl`
* `client_segmentation/client_segmentation_preprocessing_<run_id>.pkl`
* `price_prediction/price_prediction_baseline_<run_id>.pkl`
* `price_prediction/price_prediction_performant_<run_id>.pkl`
* `price_prediction/price_prediction_holdout_predictions_<run_id>.csv`
* `plots/client_segmentation_pca_<run_id>.png`
* `plots/price_prediction_actual_vs_predicted_<run_id>.png`
* `plots/price_prediction_model_metrics_<run_id>.png`

Read price metrics in `price_prediction.models.*.test`, segmentation metrics in `client_segmentation.*_metrics`, and drift checks in each `drift_check` block.

## FastAPI Inference

```powershell
python ml/api/main.py
```

Chatbot endpoint:

```http
POST /chat
```

Price prediction endpoint:

```http
POST /price/predict
X-ML-Service-Token: <ML_SERVICE_TOKEN>
```

Example price payload:

```json
{
  "product_id": 10
}
```

The backend gateway calls this service through `POST /api/ml/price/predict`.

## Embeddings And Search

```powershell
python -m ml.scripts.generate_embeddings
```

Embeddings are versioned by `(product_id, model_name, model_version)`.

## Seeder And Health Checks

```powershell
python -m ml.scripts.seed --mode reset
python -m ml.scripts.health_check_db
```

## Tests

```powershell
python -m unittest discover -s ml/tests -v
pytest ml/test_chat.py -q
python -m ml.validation.real_db_validation
```

## Folder Map

* `ml/customer_segmentation/`
* `ml/price_prediction/`
* `ml/validation/`
* `ml/nlp/chatbot/`
* `ml/nlp/retrieval/`
* `ml/scripts/`
* `ml/seeder/`
* `ml/artifacts/`
