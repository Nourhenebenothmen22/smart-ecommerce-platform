# 🚀 E-Commerce Intelligent Platform (Backend & Machine Learning Hybride)

Bienvenue dans l'architecture Backend et Intelligence Artificielle de la plateforme e-commerce. Ce projet est un environnement **hybride** mêlant logique métier stricte (Node.js) et pipeline de requêtes sémantiques ou génératives (Python FastAPI / LLMs / Algorithmes).

---

## 🏗️ Architecture du Projet

Le système s'articule autour de 3 piliers majeurs :

### 1. Backend API (Node.js / Express) dans `backend/`
- **`src/sql/`** : Source de vérité du schéma (001-010). Idempotent, contenant des configurations avancées et des tables spécifiques (`product_embeddings`, `chatbot_interactions`).
- **`src/services/`** : Logique métier (Commandes, Avis, etc.) dissociée des contrôleurs.
- **Sécurité et Scalabilité** : Zod pour la validation, JWT, Bcrypt, Helmet, et Rate Limiting centralisés.

### 2. Service NLP & APIs ML (Python / FastAPI) dans `ml/`
- **`api/main.py`** : Serveur d'inférence (FastAPI) écoutant sur le port 8000. Point d'entrée pour le Chatbot documentaire (endpoint `/chat`).
- **`nlp/chatbot/`** : Agent **RAG (Retrieval-Augmented Generation)** qui synthétise les recommandations produits en interrogeant la LLM (OpenAI par défaut). 
- **`nlp/retrieval/`** : Moteurs d'extraction hybride configurés pour interroger la base :
  - *DenseVectoreRetriever* : Recherche Sémantique par similarité Cosinus (via l'extension PostgreSQL `pgvector`).
  - *BM25Retriever* : Recherche Lexicale exacte.
- **`nlp_experiments/`** : Scripts d'automatisation des tests et benchmarks QA des modèles (Performance, Non-Regression, Overfitting).

### 3. Base de Données Hybride (PostgreSQL)
Fournie via Docker (`ecommerce_postgres`), la base intègre l'extension **pgvector** (`pgvector/pgvector:pg16`). Elle assure à la fois du transactionnel classique (Orders) et du stockage de vecteurs (Embeddings de 384 dimensions).

---

## 🎯 Schéma Relationnel & Traçabilité RAG

Cette architecture ne se contente pas de stocker des ventes, elle capture tout le processus décisionnel IA.

```mermaid
erDiagram
    USERS ||--o{ ORDERS : "places"
    USERS ||--o{ CHATBOT_INTERACTIONS : "chats"
    
    PRODUCTS ||--|| PRODUCT_EMBEDDINGS : "has_vector_for_search"
    
    CHATBOT_INTERACTIONS ||--o{ NLP_SIMILARITY_METRICS : "evaluated_by"
    
    API_NODEJS ||--o{ API_FASTAPI : "proxies /chat"
```
_Note: `chatbot_interactions` permet de retracer le contexte fourni par `pgvector` à l'IA, sécurisant et auditable (Traçabilité complète des hallucination)._

---

## 💾 Guide d'Exécution & Déploiement Local

### Étape 1 : Infrastructure
Démarrez la base de données (qui inclut nativement `pgvector`) :
```bash
cd backend/infra/docker
docker-compose up -d
```

### Étape 2 : Initialisation du Backend (Environnement Transactionnel)
```bash
cd backend
npm install
npm run db:init # ⚠️ Force-refresh : Réinstalle les 10 schémas SQL incluant les tables IA !
npm run dev     # Lance le backend Node.js (ex: http://localhost:5000)
```
_Astuce : Exécutez `npm run ml:seed:reset` depuis le package.json pour la génération automatisée initiale du catalogue._

### Étape 3 : Initialisation du Service ML (FastAPI & Agent)
```bash
cd ml
# Recommandé: Créez un Virtual Environnement
pip install -r requirements.txt
```

**⚠️ Configuration IA (Variable d'Environnement) :**
Pour que le Chatbot puisse répondre, configurez la clé OpenAI :
- **Windows PowerShell :** `$env:OPENAI_API_KEY="sk-votre-cle"`
- **Linux/Mac :** `export OPENAI_API_KEY="sk-votre-cle"`
*(Si la clé est absente, l'API passera en mode DÉMO sécurisé sans crasher).*

```bash
# Lancement de l'API ML
python api/main.py
```

---

## 🛡️ Audit de Qualité & Remédiation (Avril 2026)

Le système a subi un audit expert complet et une phase de remédiation technique pour garantir sa fiabilité en production :
1. **Node.js** : Utilisation stricte de Middlewares défensifs (compression, helmet, xss protection).
2. **Pydantic (Python)** : Validation stricte des entrées pour rejeter les injections SQL et anomalies de payload.
3. **Pipeline RAG Optimisé** : 
   - **Précision Lexicale** : Passage à une logique `AND` pour le BM25 afin d'éliminer le bruit sémantique.
   - **Richesse du Contexte** : Augmentation de la fenêtre contextuelle (descriptions de 500 caractères) pour des réponses techniques précises.
   - **Sécurité Agent** : Protection avancée contre le prompt injection et les tentatives de détournement de personnalité.
4. **Cohérence de Données** : Alignement complet des schémas de recherche BM25 et Vectoriels, garantissant l'affichage systématique des prix, marques et stocks.

---

## 🧪 Maintenance, Tests & Évaluation

Pour garantir la qualité continue du service ML, utilisez les commandes suivantes depuis la racine du projet :

### 1. Exécution du Service
```bash
# Lancer l'API FastAPI (Inférence Chatbot)
python ml/api/main.py
```

### 2. Tests QA & Validation
```bash
# Lancer la suite de tests complète (Pydantic, Injections, Scénarios)
pytest ml/test_chat.py -v

# Lancer l'outil d'évaluation QA automatisé
python ml/nlp_experiments/chatbot_qa_tester.py
```

### 3. Gestion des Données & Embeddings
```bash
# Vérifier l'état de la base de données et des extensions (pgvector)
python ml/scripts/health_check_db.py

# (Re)Générer les embeddings vectoriels pour tout le catalogue
python ml/scripts/generate_embeddings.py

# Reset complet et seeding du catalogue (Node.js)
npm run ml:seed:reset
```

> [!TIP]
> Avant de déployer une modification sur le `System Prompt`, exécutez systématiquement `pytest ml/test_chat.py` pour vérifier que les garde-fous contre les injections sont toujours actifs.

---

> [!NOTE]
> Pour des questions pointues concernant le stockage vectoriel ou les expérimentations algorithmiques, consultez le dossier expérimental `ml/nlp_experiments/`.
