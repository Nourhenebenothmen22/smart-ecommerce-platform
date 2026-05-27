# 📊 Customer Segmentation ML Pipeline

Machine Learning pipeline for customer segmentation in an e-commerce platform using K-Means and DBSCAN clustering algorithms.

---

# 🚀 Run Pipeline

Execute the complete ML pipeline:

```powershell
python -m ml.customer_segmentation.run_pipeline
```

---

# 📌 Project Overview

This project performs customer segmentation on an e-commerce database containing:

- 1200 users
- 23 engineered behavioral features
- PostgreSQL data source

The pipeline includes:

- Data extraction
- Feature preprocessing
- Outlier handling
- Feature scaling
- K-Means clustering
- DBSCAN clustering
- Model comparison
- Business interpretation
- Artifact persistence

---

# 🧠 Machine Learning Workflow

```text
PostgreSQL Database
        ↓
Data Loader
        ↓
Feature Engineering
        ↓
Outlier Handling (Winsorization)
        ↓
RobustScaler
        ↓
K-Means Training & Tuning
        ↓
DBSCAN Training & Tuning
        ↓
Model Evaluation & Comparison
        ↓
Business Interpretation
        ↓
Production Model Export
```

---

# ⚙️ Preprocessing Pipeline

## ✅ Outlier Handling

The pipeline uses:

- IQR-based outlier detection
- Winsorization (capping extreme values)

Applied on:

- 10 numerical columns

Saved artifact:

```text
winsorization_bounds.json
```

---

## ✅ Feature Scaling

The pipeline uses:

```python
RobustScaler
```

Reason:

- More resistant to outliers than StandardScaler
- Better for skewed e-commerce behavioral data

Saved artifact:

```text
scaler.pkl
```

---

# 📈 K-Means Results

## Tested Values

| k | Inertia | Silhouette Score |
|---|---|---|
| 2 | 6119.89 | 0.3087 |
| 3 | 4415.47 | **0.3674** |
| 4 | 3799.64 | 0.3330 |
| 5 | 3331.62 | 0.2976 |

---

# ✅ Best K Selected

```text
best_k = 3
```

Reason:

- Highest silhouette score
- Best cluster separation
- Elbow method confirms optimal balance

---

# 📊 K-Means Interpretation

The data naturally separates into:

- 3 major behavioral customer groups

The segmentation is considered:

- statistically valid
- business realistic
- production compatible

---

# 🔍 DBSCAN Results

## Dynamic Tuning Result

```text
eps = 1.519
min_samples = 10
```

## Performance

| Metric | Value |
|---|---|
| Silhouette Score | 0.4346 |
| Noise Percentage | 4.42% |

---

# 📌 DBSCAN Interpretation

DBSCAN achieved:

- better offline clustering quality
- stronger density separation
- improved outlier handling

Only:

```text
4.42%
```

of users were classified as noise.

This indicates:

- relatively clean customer behavioral patterns
- stable density structure

---

# ⚖️ Model Comparison

| Metric | K-Means | DBSCAN |
|---|---|---|
| Silhouette Quality | Good | Better |
| Production Prediction | ✅ Yes | ❌ No |
| Predict New Users | ✅ Yes | ❌ No |
| Deterministic Inference | ✅ Yes | ❌ No |
| Noise Handling | Medium | Excellent |
| Scalability | Excellent | Medium |

---

# 🏆 Final Production Model

## Selected Model

```text
K-Means
```

---

# ❗ Why K-Means Was Selected

Even though DBSCAN achieved a better offline score:

```text
DBSCAN Final Score: 0.5995
KMeans Final Score: 0.5669
```

K-Means was selected for production because:

- it supports deterministic prediction
- it can classify unseen users
- it exposes a stable `.predict()` API
- it is easier to deploy in backend systems

DBSCAN was kept for:

- offline analytics
- exploratory clustering
- anomaly detection

---

# 📊 Final Segment Distribution

The final segmentation generated 3 business-oriented customer groups:

| Segment | Users |
|---|---|
| VIP Customers | 859 |
| Inactive Customers | 239 |
| Loyal Buyers | 102 |

---

# 📌 Business Interpretation

## VIP Customers

Users with:

- high spending activity
- frequent purchases
- strong engagement

---

## Loyal Buyers

Users with:

- regular purchasing behavior
- medium-to-high retention
- stable activity patterns

---

## Inactive Customers

Users with:

- low engagement
- low recency activity
- weak purchasing behavior

---

# 📈 Generated Visualizations

| File | Description |
|---|---|
| `kmeans_elbow.png` | Elbow method analysis |
| `kmeans_silhouette.png` | Silhouette optimization |
| `dbscan_k_distance.png` | DBSCAN eps estimation |
| `kmeans_vs_dbscan_comparison.png` | Model comparison |
| `final_best_model_segments.png` | Final segment distribution |

---

# 📁 Output Artifacts

## Models

```text
ml/artifacts/customer_segmentation/model/kmeans_model.pkl
ml/artifacts/customer_segmentation/model/dbscan_model.pkl
```

---

## Processed Data

```text
ml/artifacts/customer_segmentation/data/processed/best_model_users_labelled.csv
```

---

## Reports

```text
ml/artifacts/customer_segmentation/reports/model_comparison.csv
```

---

## Segment Mapping

```text
ml/artifacts/customer_segmentation/model/segment_map.json
```

---

# 🛠️ Technologies Used

- Python
- Scikit-learn
- Pandas
- NumPy
- PostgreSQL
- SQLAlchemy
- Matplotlib
- Seaborn

---

# 📌 Key ML Features

## ✅ Dynamic K Selection

Automatic K optimization using:

- Silhouette Score
- Elbow Method

---

## ✅ Dynamic DBSCAN Tuning

Automatic:

- eps tuning
- density analysis

---

## ✅ Production-Ready Artifacts

Saved components:

- trained models
- preprocessing artifacts
- segment mappings
- plots
- reports

---

# ⚠️ Current Limitations

## DBSCAN

- Cannot predict unseen users directly
- Difficult real-time deployment

---

## K-Means

- Assumes spherical clusters
- Sensitive to feature distribution

---

## Business Labels

Cluster naming may require:

- manual validation
- domain expert review

---

# 🔮 Future Improvements

- Add PCA dimensionality reduction
- Add HDBSCAN support
- Add automatic cluster profiling
- Add MLflow experiment tracking
- Add FastAPI inference endpoint
- Add drift monitoring
- Add automated retraining

---

# ✅ Final Verdict

The pipeline is:

- modular
- production-oriented
- statistically coherent
- scalable
- backend compatible

The system successfully performs customer segmentation using advanced preprocessing, automated clustering evaluation, and production-ready model persistence.
