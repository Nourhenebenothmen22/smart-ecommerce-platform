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

## Price Prediction

The price prediction pipeline trains regression models from dynamic PostgreSQL product data.

```powershell
python -m ml.price_prediction.run_pipeline
```

It loads rows from `products`, `categories`, and `subcategories`, engineers reusable product features, trains a median baseline and a RandomForest regressor, then compares them with MAE, MSE, RMSE, and R2.

Generated plots are stored under `ml/artifacts/price_prediction/plots/`:

* `price_distribution.png`
* `feature_correlation.png`
* `actual_vs_predicted_price.png`
* `model_performance_comparison.png`

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
```

## Folder Map

* `ml/customer_segmentation/`
* `ml/price_prediction/`
* `ml/nlp/chatbot/`
* `ml/nlp/retrieval/`
* `ml/scripts/`
* `ml/seeder/`
* `ml/artifacts/`
