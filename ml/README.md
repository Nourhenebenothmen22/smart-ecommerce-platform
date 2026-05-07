# 🚀 Machine Learning Project Workspace

Ce dossier contient l'ensemble des modules d'Intelligence Artificielle de la plateforme Smart E-Commerce.

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

---

## 🤖 Chatbot & Assistant Intelligent
Ce module gère l'assistant virtuel basé sur le NLP et la recherche sémantique.

### 1. Préparation des Données (Seeding)
Pour insérer les données de base (FAQ, produits) dans la base de données :
```powershell
python -m ml.seeder.seed
```

### 2. Génération des Embeddings (RAG)
Pour générer les vecteurs sémantiques nécessaires à la recherche :
```powershell
python -m ml.scripts.generate_embeddings
```

### 3. Test du Chatbot
Pour tester l'agent conversationnel directement en ligne de commande :
```powershell
python -m ml.test_chat
```

---

## 🛠️ Maintenance & Santé
*   **Nettoyage Auto** : Le pipeline de segmentation nettoie ses propres fichiers à chaque lancement.
*   **Vérification DB** : Pour vérifier la connexion et l'état des tables ML :
    ```powershell
    python -m ml.scripts.health_check_db
    ```

## 📁 Localisation des Dossiers
*   **Segmentation** : `ml/customer_segmentation/`
*   **NLP / Chatbot** : `ml/nlp/chatbot/`
*   **Résultats (Artifacts)** : `ml/artifacts/`
