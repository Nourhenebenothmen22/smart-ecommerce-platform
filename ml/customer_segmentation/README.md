# 📊 Rapport Final de Segmentation Client

Ce document présente les résultats de l'audit et de l'exécution du pipeline de Machine Learning sur votre base de données e-commerce (1200 utilisateurs).

## 🏁 Résultat Final : k = 2
L'algorithme a déterminé que la structure la plus robuste de votre base de données actuelle comporte **2 segments**.

### Pourquoi ce choix ?
1. **Cohésion Maximale** : Le score de silhouette pour $k=2$ (0.2317) est supérieur à celui de $k=3$. Cela signifie que les groupes sont plus "purs" et mieux définis.
2. **Stabilité** : K-Means s'est avéré plus performant que DBSCAN sur vos données. DBSCAN a classé 12.65% de vos utilisateurs comme du "bruit" (points isolés), ce qui n'est pas idéal pour une stratégie marketing globale.
3. **Respect des Contraintes** : Ce choix respecte votre limite de maximum 3 clusters tout en utilisant une méthode déterministe (50 initialisations).

## 📈 Interprétation des Graphiques

| Graphique | Interprétation |
| :--- | :--- |
| **`kmeans_elbow.png`** | Montre la "méthode du coude". La cassure la plus nette se situe à $k=2$, indiquant que l'ajout d'un 3ème cluster n'apporte pas assez de précision supplémentaire par rapport à la complexité ajoutée. |
| **`kmeans_silhouette.png`** | Confirme que $k=2$ est le pic de performance mathématique. C'est là que la séparation entre les types de clients est la plus évidente. |
| **`dbscan_k_distance.png`** | Utilisé pour estimer la densité de votre base. Il montre que vos données ont des densités très variables, ce qui explique pourquoi DBSCAN a eu du mal à regrouper tout le monde sans créer de bruit. |
| **`kmeans_vs_dbscan_comparison.png`** | Comparaison directe des métriques. K-Means gagne sur la silhouette et la complétude des données traitées. |
| **`final_best_model_segments.png`** | Affiche la distribution finale. Vos 1200 utilisateurs sont répartis entre deux profils majeurs (ex: Clients à Forte Valeur vs Clients à Potentiel). |

## ⚖️ Comparaison des Modèles (Détails)

| Métrique | K-Means (Gagnant) | DBSCAN |
| :--- | :--- | :--- |
| **Nombre de Clusters** | **2** | 4 (Pénalisé) |
| **Score de Silhouette** | **0.2317** | 0.2039 |
| **Utilisateurs Ignorés** | **0%** | 12.65% (Bruit) |
| **Stabilité** | Maximale (50 init) | Variable (selon densité) |

## 📁 Localisation des Résultats
*   **Modèle Persistant** : `ml/artifacts/customer_segmentation/models/kmeans_model.pkl`
*   **Données Étiquetées** : `ml/artifacts/customer_segmentation/data/best_model_users_labelled.csv`
*   **Rapport Comparatif** : `ml/artifacts/customer_segmentation/reports/model_comparison.csv`
