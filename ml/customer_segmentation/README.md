# 📊 Customer Segmentation ML Pipeline

Machine Learning pipeline for customer segmentation in an e-commerce platform using **K-Means** and **DBSCAN** clustering algorithms.

---

# 🚀 Run Pipeline

Execute the complete ML pipeline:

```powershell
python -m ml.customer_segmentation.run_pipeline
```

---

# 📌 Project Overview

This project performs customer segmentation on an e-commerce database containing:

- **1200 users**
- **23 engineered behavioral features**
- **PostgreSQL** data source

The pipeline includes:

- Data extraction from the `user_features` table
- Feature preprocessing
- IQR-based outlier handling
- Winsorization
- Robust feature scaling
- K-Means clustering
- DBSCAN clustering
- Model comparison
- Business interpretation
- Production artifact persistence

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
- Winsorization to cap extreme values

Applied on:

- **10 numerical columns**

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

- More resistant to outliers than `StandardScaler`
- Better suited for skewed e-commerce behavioral data
- Useful when features include spending, frequency, recency, and engagement metrics

Saved artifact:

```text
scaler.pkl
```

---

# 📈 K-Means Results

## Tested K Values

| k | Inertia | Silhouette Score |
|---|---:|---:|
| 2 | 6119.89 | 0.3087 |
| 3 | 4415.47 | **0.3674** |
| 4 | 3799.64 | 0.3330 |
| 5 | 3331.62 | 0.2976 |

---

# ✅ Best K Selected

```text
best_k = 3
```

K-Means selected **3 clusters** because:

- `k=3` produced the highest silhouette score: **0.3674**
- the elbow method shows a strong improvement from `k=2` to `k=3`
- adding more clusters after `k=3` gives weaker separation
- `k=3` provides a good balance between mathematical quality and business interpretability

---

# 📊 K-Means Interpretation

K-Means produces **3 production-ready customer segments**.

This model is suitable for backend inference because it supports:

```python
model.predict(new_user_features)
```

This means new users can be assigned to a segment deterministically.

---

# 🔍 DBSCAN Results

## Dynamic Tuning Result

```text
eps = 1.5185721582089433
min_samples = 10
```

Rounded values:

```text
eps ≈ 1.52
min_samples = 10
```

---

## DBSCAN Performance

| Metric | Value |
|---|---:|
| Number of clusters | 2 |
| Silhouette Score | **0.4346** |
| Davies-Bouldin Index | **0.7313** |
| Calinski-Harabasz Score | 389.8068 |
| Noise Count | 53 users |
| Noise Percentage | 4.42% |
| Final Score | **0.5995** |

---

# 📌 DBSCAN Interpretation

DBSCAN achieved stronger offline clustering quality than K-Means.

It performed better on:

- silhouette score
- Davies-Bouldin index
- final comparison score
- outlier/noise detection

DBSCAN found:

```text
2 dense customer groups
53 noise users
4.42% noise
```

The low noise percentage indicates that most users belong to identifiable behavioral groups.

---

# ⚖️ Detailed Model Comparison

| Metric | K-Means | DBSCAN | Better |
|---|---:|---:|---|
| Silhouette Score | 0.3674 | **0.4346** | DBSCAN |
| Davies-Bouldin Index | 1.0053 | **0.7313** | DBSCAN |
| Calinski-Harabasz Score | **491.2388** | 389.8068 | K-Means |
| Inertia | 4415.4664 | N/A | K-Means only |
| Number of clusters | 3 | 2 | Depends on use case |
| Final Score | 0.56687 | **0.5995253816** | DBSCAN |
| Noise Count | N/A | 53 | K-Means has no noise class |
| Noise Percentage | N/A | 4.42% | DBSCAN detects noise |
| eps | N/A | 1.5185721582 | DBSCAN only |
| min_samples | N/A | 10 | DBSCAN only |

---

# 🏆 Best Offline Model

```text
DBSCAN
```

DBSCAN achieved the best offline score:

```text
DBSCAN Final Score = 0.5995
KMeans Final Score = 0.5669
```

This means DBSCAN discovered a better natural density-based structure in the existing dataset.

---

# 🏭 Final Production Model

```text
K-Means
```

Even though DBSCAN is the best offline model, **K-Means is selected as the production model**.

---

# ❗ Why K-Means Was Selected for Production

DBSCAN does not provide a native deterministic `.predict()` method for unseen users.

This is a major limitation for backend deployment because new users need to be segmented after registration, purchase, or activity updates.

K-Means was selected for production because it supports:

- deterministic inference
- prediction for unseen users
- stable backend API integration
- scalable real-time segmentation
- simple model persistence and reuse

DBSCAN remains useful for:

- offline analytics
- exploratory clustering
- anomaly detection
- understanding dense customer groups

---

# 📊 Final Segment Distribution

The final production segmentation generated **3 business-oriented customer groups**:

| Segment | Users |
|---|---:|
| VIP Customers | 859 |
| Inactive Customers | 239 |
| Loyal Buyers | 102 |

Total:

```text
1200 users
```

---

# 📌 Business Interpretation

## VIP Customers

Users with stronger commercial value, typically showing:

- higher spending activity
- stronger purchase behavior
- better engagement

Count:

```text
859 users
```

---

## Loyal Buyers

Users with stable purchasing behavior, typically showing:

- repeated purchases
- medium-to-high retention
- consistent engagement

Count:

```text
102 users
```

---

## Inactive Customers

Users with weaker recent activity, typically showing:

- low engagement
- low recency activity
- weaker purchasing behavior

Count:

```text
239 users
```

---

# ⚠️ Business Labeling Note

The segment names are business labels generated after clustering.

They should be validated using cluster profiling, for example:

```text
average_total_spent
average_order_count
average_recency
average_frequency
average_order_value
average_engagement
```

Important note:

- `VIP Customers = 859 users` is a large share of the dataset.
- This may be valid if the dataset contains many active/high-value users.
- However, it should be reviewed with business rules to ensure the label "VIP" is not too broad.

---

# 📈 Generated Visualizations

| File | Description |
|---|---|
| `kmeans_elbow.png` | Elbow method for selecting K |
| `kmeans_silhouette.png` | Silhouette analysis for K-Means |
| `dbscan_k_distance.png` | K-distance plot for DBSCAN eps estimation |
| `kmeans_vs_dbscan_comparison.png` | Model comparison chart |
| `final_best_model_segments.png` | Final production segment distribution |

---

# 📁 Output Artifacts

## Models

```text
ml/artifacts/customer_segmentation/model/kmeans_model.pkl
ml/artifacts/customer_segmentation/model/dbscan_model.pkl
```

---

## Preprocessing Artifacts

```text
ml/artifacts/customer_segmentation/model/winsorization_bounds.json
ml/artifacts/customer_segmentation/model/scaler.pkl
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

Automatic K-Means optimization using:

- Silhouette Score
- Elbow Method
- Inertia/WCSS analysis

---

## ✅ Dynamic DBSCAN Tuning

Automatic DBSCAN configuration using:

- K-distance plot
- eps estimation
- min_samples tuning
- density-based evaluation

---

## ✅ Model Comparison

The pipeline compares models using:

- Silhouette Score
- Davies-Bouldin Index
- Calinski-Harabasz Score
- Final normalized model score
- Noise percentage for DBSCAN

---

## ✅ Production-Ready Artifacts

Saved components include:

- trained K-Means model
- trained DBSCAN model
- preprocessing artifacts
- segment mapping
- processed labeled users
- plots
- model comparison report

---

# ⚠️ Current Limitations

## DBSCAN

- Cannot predict unseen users directly
- Less convenient for real-time backend inference
- Better suited for offline analysis

---

## K-Means

- Assumes roughly spherical clusters
- Sensitive to feature scaling
- Does not detect noise or anomalies automatically

---

## Business Labels

Cluster names require business validation.

The model identifies mathematical groups, but the business labels must be checked using customer behavior statistics.

---

# 🔮 Future Improvements

- Add PCA dimensionality reduction before DBSCAN
- Add HDBSCAN for better density-based clustering
- Add automatic cluster profiling report
- Add MLflow experiment tracking
- Add FastAPI inference endpoint
- Add drift monitoring
- Add automated retraining
- Add business-rule validation for segment names

---

# ✅ Final Verdict

The pipeline is:

- modular
- production-oriented
- statistically coherent
- scalable
- backend compatible

Final conclusion:

```text
DBSCAN is the best offline clustering model.
K-Means is the selected production model.
K-Means uses k = 3.
DBSCAN found 2 clusters and 53 noise users.
```

The system successfully performs customer segmentation using advanced preprocessing, automated clustering evaluation, and production-ready model persistence.
