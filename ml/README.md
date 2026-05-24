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

The price prediction pipeline trains regression models from dynamic PostgreSQL product data. It compares the original legacy preprocessing profile with the improved production preprocessing profile.

```powershell
python -m ml.price_prediction.run_pipeline
```

It loads rows from `products`, `categories`, and `subcategories`, then:

* removes duplicate product rows and invalid prices;
* clips invalid numeric ranges such as negative stock, negative review counts, discount values outside `0..100`, and ratings outside `0..5`;
* removes extreme target outliers using configured quantile bounds;
* avoids leaking or invalid features by excluding `final_price`, `category_id`, and `subcategory_id` from the improved profile;
* creates discount, stock, review, text-richness, rating-review, category-combination, and bucket features;
* encodes categorical variables with unknown/rare-category handling;
* scales numeric variables inside sklearn pipelines fitted only on the training split;
* compares a median baseline model and a RandomForest regressor with MAE, MSE, RMSE, and R2;
* uses log target transformation for the improved baseline when helpful, while the performant RandomForest uses the raw target because it validated better.

Evaluation outputs:

* `ml/artifacts/price_prediction/reports/model_comparison.csv`
* `ml/artifacts/price_prediction/reports/preprocessing_report.json`
* `ml/artifacts/price_prediction/models/metadata.json`

Generated plots are stored under `ml/artifacts/price_prediction/plots/`:

* `price_distribution.png`: cleaned target distribution and skew.
* `feature_correlation.png`: numeric feature correlation with price.
* `actual_vs_predicted_price.png`: held-out actual prices versus selected model predictions.
* `model_performance_comparison.png`: legacy vs improved baseline and RandomForest metrics.

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
python -m ml.price_prediction.run_pipeline
```

## Folder Map

* `ml/customer_segmentation/`
* `ml/price_prediction/`
* `ml/nlp/chatbot/`
* `ml/nlp/retrieval/`
* `ml/scripts/`
* `ml/seeder/`
* `ml/artifacts/`
