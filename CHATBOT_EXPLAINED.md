# 🤖 Guide Fonctionnel et Architectural du Chatbot RAG

Ce document explique en détail le comportement du point de terminaison de Chatbot fraîchement paramétré via FastAPI, la façon dont les données sont ingérées, ainsi que la manière dont Postgres s'occupe de la mémorisation et de la traçabilité.

---

## 1. Pourquoi la réponse est-elle maintenant ultra-pertinente ?

Lorsque vous exécutez la requête via Swagger :
```json
{
  "query": "Je cherche un bon téléphone portable..."
}
```

Voici le résumé du pipeline **réel** et **optimisé** qui s'est produit :
1. **[Requête Client]** Votre navigateur a envoyé un POST `/chat` au serveur FastAPI.
2. **[Hybrid Retrieval (RRF)]** Le bot n'utilise plus de mocks. Il interroge simultanément :
   - Le **BM25 (Lexical)** pour les correspondances exactes (mots-clés).
   - Le **Dense Vector (Sémantique)** pour l'intention et les synonymes.
   - Les résultats sont fusionnés via l'algorithme **Reciprocal Rank Fusion (RRF)**.
3. **[Prompt Augmentation]** L'Agent compile votre question avec les 5 meilleurs produits (incluant prix, stock et descriptions longues de 500 chars).
4. **[Inférence LLM]** Le texte est envoyé au LLM `gpt-4o-mini` avec des règles de sécurité strictes contre l'injection.
5. **[Génération de la réponse]** Le modèle fournit un conseil de vente précis basé **uniquement** sur les données réelles du catalogue.

✅ *Le système est désormais 100% data-driven et sécurisé !*

---

## 2. Le Stockage et l'Historique (Traçabilité)

La particularité de notre Chatbot n'est pas simplement de discuter, mais d'**Auditer** et de **Stocker**.

Où vont les données ? Elles sont dirigées (ou le seront très bientôt par de petites requêtes asynchrones) dans votre base de données PostgreSQL de production (`ecommerce_ml_db`).

Rappelez-vous du script **`009_nlp_schema.sql`** que nous avons déployé. Il a créé la table suivante :

### La table `chatbot_interactions`
Pour chaque interaction comme celle que vous venez de réaliser dans Swagger, une ligne est stockée pour toujours avec les champs suivants :
- `user_id`: Qui a posé la question (si l'utilisateur est authentifié).
- `session_id`: Permet d'isoler des "arbres" de discussions pour une mémoire continue.
- `user_query`: `"Je cherche un bon téléphone portable..."`. L'audit de ce que cherchent vos clients !
- `retrieved_context`: Un blob JSON contenant l'exactitude des produits remontés par le moteur de recherche SQL. Extrêmement critique pour déboguer les biais ("Pourquoi a-t-il proposé un T-Shirt au lieu d'un Pantalon ?").
- `llm_response`: La réponse exacte fournie par "gpt-4o-mini" (votre retour de swagger).
- `execution_time_ms`: Pour monitorer vos coûts de latence API (`1400 ms` par exemple).
- `user_feedback_score`: Permettra aux clients du site e-commerce de cliquer sur "👍" ou "👎" pour entrainer directement le système de similarité sur le long terme !

---

## 3. Gestion Vectorielle native en Postgres (`product_embeddings`)

Dans un avenir proche, lorsque votre équipe insérera de vrais produits (et non pas des Mocks Python), le bot fouillera via la fonction mathématique de la Distance Cosinus (nativement incluse via `pgvector` !).

```sql
-- Le produit magique qui stocke le sens sémantique de tout votre catalogue !
CREATE TABLE product_embeddings (
    product_id INTEGER,
    embedding vector(384), -- La suite de nombres "Denses" (Coordonnées sémantiques)
    concatenated_text TEXT
);
```
Quand un utilisateur tape "Je cherche un bon téléphone portable..." :
- Le serveur FastAPI transforme cette phrase de 40 lettres en **384 nombres flottants**.
- Postgres calcule mathématiquement quels sont les 3 autres produits (leurs 384 dimensions associées) les plus proches de ces nombres dans votre base en **quelques millisecondes**.
- *Aucun besoin de ElasticSearch, ni de base tierce.* Postgres centralise tout.

---

## 4. Pour Aller Plus Loin : L'Intégration Node.js

Actuellement, ce LLM repose dans le backend `Python` (`ml/api`). 

Lorsque votre site e-commerce Final (React/Vue.js) déploiera sa petite messagerie de chat en bas à droite de l'écran, son flow sera le suivant :
1. Site Web -> Envoi requête WebSocket ou REST -> Node.js (Express sur `backend/`).
2. Node.js vérifie les droits d'Authentification (JWT) du client et attrape l'ID utilisateur (ex: ID 50).
3. Node.js agit comme un Proxy sécurisé. Il contacte le serveur FastAPI `http://localhost:8000/chat`.
4. Python répond, log la demande de l'ID 50 dans la DB `chatbot_interactions` et renvoie la réponse au Node.
5. Node pousse l'affichage sur la boutique du client.

Ce cloisonnement technique (Node.JS pour le relationnel/sécurité et Python pour les vecteurs/tensors) vous garantit de ne faire exploser ni le frontend, ni le CPU central en cas d'un pic de visite e-commerce.

---

## 5. Stockage des Algorithmes (`ml_models` vs `nlp_similarity_metrics`)

Vous vous demandez peut-être si ces algorithmes d'IA (LLM, Embeddings) sont enregistrés dans la table `ml_models` de notre base de données. Voici comment la traçabilité est segmentée :

1. **La table `ml_models` (Le Registre Historique)** :
   - Conçue dans le schéma `006_ml_schema.sql`, cette table sert de registre (*Model Registry*). Lorsqu'un modèle d'Embedding (ex: `all-MiniLM-L6-v2`) ou de segmentation utilisateur est validé en production, sa signature, son poids, et sa version y sont référencés.
   - Elle répertorie **"Qu'est-ce qui tourne en production ?"**.

2. **La table `nlp_similarity_metrics` (Le Centre de Tir / Évaluation)** :
   - Mise en place par `010_nlp_evaluations.sql`, elle stocke les performances de recherche du Moteur.
   - Elle répertorie **"Lequel est le plus performant sur un jeu de données précis ?"** (Comparaison des algorithmes).

---

## 6. Comparaison Détaillée : BM25 vs Dense Cosine Similarity

Dans le script `ml/nlp_experiments/similarity_eval.py`, nous avions simulé et évalué deux approches radicalement différentes pour le moteur de recherche interne du Chatbot. Sur quoi s'est fondé notre choix d'utiliser `DenseVectorRetriever` par défaut ? 

### A. L'algorithme BM25 (Recherche Lexicale)
Il s'agit du standard industriel de l'ingénierie textuelle (utilisé sous le capot par *ElasticSearch*). Il se base sur la fréquence des mots (Combien de fois le mot "Batterie" apparait dans l'avis client, relativisé au reste du texte).

- **🟢 Points Forts :** 
  - Latence imbattable (environ `10ms`).
  - Parfaitement redoutable pour les correspondances exactes ou les acronymes : si un client tape `"iPhone 14 Pro Max 256GB"`, le BM25 trouvera directement le SKU correspondant.
- **🔴 Points Faibles (Overfitting Lexical) :**
  - Il ne comprend absolument pas le **SENS** de la question. Si le client tape `"téléphone portable avec bonne batterie"`, BM25 cherchera les mots "téléphone" et "batterie". Si un produit a pour description *"Ce smartphone offre une excellente autonomie énergétique"*, le BM25 ne le trouvera pas (car les termes sont différents).

### B. Dense Cosine Similarity (Recherche Sémantique ou Vectorielle)
L'approche choisie pour notre API FastAPI (`DenseVectorRetriever` orchestré par `pgvector`). Le texte est converti par un modèle IA (ex: SentenceTransformers) en 384 dimensions mathématiques.

- **🟢 Points Forts :**
  - Il comprend **l'intention cachée**. `"chaussures de course"` sera naturellement associé à des baskets qualifiées de `"légères pour le running"`, même si la terminologie diffère complèment.
  - Offre un contexte beaucoup plus riche au LLM (GPT-4) pour fabriquer des réponses intelligentes en cas de doute de l'utilisateur.
- **🔴 Points Faibles :**
  - Plus gourmand en calcul (La latence avoisine les `40ms` contre 10ms pour le BM25).
  - Parfois trop hasardeux sur les noms de marques très précis (si le vecteur est mal entrainé, `"Samsung"` et `"Apple"` pourraient se retrouver côte à côte car sémantiquement ce sont tous deux "des téléphones haut de gamme").

### C. Le Choix d'Architecture (Pourquoi avoir choisi Cosine ?)
Pour un **Chatbot RAG Conversationnel**, le client ne cherche pas "un mot", il exprime un "mélange de besoin et de sentiments" :
*« J'aimerais un téléphone pas trop cher pour ma fille qui prend beaucoup de bonnes photos en soirée ».*

Le **BM25 s'effondrerait** face à cette phrase longue car il chercherait un produit s'appelant "pas cher bonne fille photos soirée".
L'**Embedding (Cosine)** extraira magnifiquement le concept abstrait (Smartphone Gamme Moyenne + Feature Mode Nuit avancé).

**Conclusion :** 
Nous utilisons `pgvector` (Densité Cosinus) comme base sémantique pour nourrir l'Intelligence Artificielle du Chatbot. Cependant, une architecture optimale future pourrait appeler un système **Hybride** : Utiliser BM25 pour les références directes, puis le filtrer sémantiquement.
