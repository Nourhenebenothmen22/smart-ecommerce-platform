# 🛒 Customer Segmentation ML Pipeline

This production-ready pipeline implements an advanced, dynamic customer segmentation system for the Smart E-Commerce Platform. It automatically identifies behavioral patterns in your user base to drive personalized marketing strategies.

## 🚀 Quick Start
To execute the entire pipeline on your live database data:
```powershell
python -m ml.customer_segmentation.run_pipeline
```

## 📂 Module Overview

| Module | Purpose |
| :--- | :--- |
| **`data_loader.py`** | Extracts raw features from the `v_user_behavior_features` database view. |
| **`preprocessing.py`** | Handles missing data, log-transformation, and robust scaling for high-performance clustering. |
| **`train_kmeans.py`** | Automates $k$-selection using Elbow and Silhouette analysis. |
| **`train_dbscan.py`** | Performs **Dynamic Parameter Estimation** (Adaptive Epsilon) based on live data density. |
| **`compare_models.py`** | Benchmarks models using a composite score (Stability vs. Cohesion vs. Business Validity). |
| **`business_interpretation.py`** | Translates numeric Cluster IDs into actionable marketing segments (VIP, At-Risk, etc.). |
| **`plots.py`** | Generates 5 standardized visualizations for auditing and reporting. |

## 📊 Business Segments Defined

The pipeline automatically labels your users into 5 high-impact categories:

1. **💎 VIP Champions**: Your most valuable users. High spenders, frequent orders, and very active. 
   *   *Strategy*: Exclusive concierge service and loyalty rewards.
2. **💛 Loyal Buyers**: Consistent and reliable customers.
   *   *Strategy*: Recurring subscription offers and cross-sell campaigns.
3. **🛒 Cart Abandoners**: High intent (many "add to carts") but low purchase conversion.
   *   *Strategy*: Urgent retargeting and time-limited discounts.
4. **👀 Window Shoppers**: High activity (views/clicks) but zero purchases.
   *   *Strategy*: Personalized recommendations based on their view history.
5. **💤 At-Risk Big Spenders**: High historical value but have not returned in a long time.
   *   *Strategy*: Aggressive win-back campaigns and "We miss you" personalized emails.

## 📈 Technical Metrics & Plots

The pipeline produces the following outputs in the `reports/` and `plots/` directories:
*   **`kmeans_elbow.png`**: Optimal cluster count verification.
*   **`dbscan_k_distance.png`**: Data density audit for noise detection.
*   **`model_comparison.csv`**: Head-to-head metrics comparison.
*   **`best_model_users_labelled.csv`**: The final export file for your marketing team.

## 🛠️ Performance & Scalability
*   **Dynamic Tuning**: The DBSCAN model automatically adapts its search range to your data's actual density.
*   **Type Safety**: Fully audited with explicit type-casting for zero runtime errors.
*   **Optimization**: Uses NumPy vectorization and Scikit-Learn C-extensions for processing thousands of users in seconds.
