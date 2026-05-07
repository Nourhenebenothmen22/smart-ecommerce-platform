# 🚀 Machine Learning Project Workspace

Ce dossier contient l'ensemble des modules d'Intelligence Artificielle de la plateforme.

## 📦 Installation des dépendances
Avant de lancer les scripts, assurez-vous d'avoir installé les bibliothèques nécessaires :
```powershell
pip install -r requirements.txt
```

## 🎯 Segmentation Client (Customer Segmentation)
Ce module analyse le comportement des utilisateurs pour créer des segments marketing.

### Commande d'exécution
Pour lancer l'entraînement complet (Nettoyage + Preprocessing + Modèles + Graphiques) :
```powershell
python -m ml.customer_segmentation.run_pipeline
```

### Localisation des Dossiers
*   **Code Source** : `ml/customer_segmentation/`
*   **Résultats (CSVs, Plots)** : `ml/artifacts/customer_segmentation/`

## 🛠️ Maintenance & Nettoyage
Le script `run_pipeline.py` est configuré pour **nettoyer automatiquement** les anciens résultats à chaque lancement. Vous n'avez pas besoin de supprimer manuellement les anciens fichiers.
