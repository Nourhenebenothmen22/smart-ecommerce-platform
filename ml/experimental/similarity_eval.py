import time
import random

# Exemples de requêtes d'évaluation
TEST_QUERIES = [
    "téléphone portable avec bonne batterie",
    "iphone 12 pro max",
    "chaussures de course homme légères",
    "Samsung Galaxy S21"
]

def evaluate_bm25(query: str):
    """Simule une exécution BM25 et retourne une précision factice"""
    start = time.time()
    # Logique BM25 : fort sur les mots "iphone 12" ou "Samsung Galaxy", faible sur l'intention "bonne batterie"
    time.sleep(0.01) # Simule I/O
    precision = random.uniform(0.5, 0.9) if "12" in query or "21" in query else random.uniform(0.1, 0.4)
    return {
        "algorithm": "BM25",
        "latency_ms": (time.time() - start) * 1000,
        "precision_at_5": precision,
        "recall_at_5": precision + 0.1
    }

def evaluate_cosine(query: str):
    """Simule une exécution Embeddings (Dense Cohere/MiniLM) et retourne une précision factice"""
    start = time.time()
    # Logique Cosine : Fort sur le sens "téléphone bonne batterie" ou "légères"
    time.sleep(0.04) # Simule Model Inference + DB I/O
    precision = random.uniform(0.7, 0.95) if "batterie" in query or "course" in query else random.uniform(0.6, 0.8)
    return {
        "algorithm": "Dense_Cosine",
        "latency_ms": (time.time() - start) * 1000,
        "precision_at_5": precision,
        "recall_at_5": precision + 0.15
    }

def run_experiment(experiment_name: str):
    print(f"--- Démarrage de l'expérience: {experiment_name} ---")
    
    results = []
    for query in TEST_QUERIES:
        print(f"\nRequête: '{query}'")
        res_bm25 = evaluate_bm25(query)
        res_cos = evaluate_cosine(query)
        
        print(f"  BM25   -> Précision: {res_bm25['precision_at_5']:.2f} | Latence: {res_bm25['latency_ms']:.2f}ms")
        print(f"  Cosine -> Précision: {res_cos['precision_at_5']:.2f} | Latence: {res_cos['latency_ms']:.2f}ms")
        
        results.append(res_bm25)
        results.append(res_cos)
        
    print(f"\n--- Fin de l'expérience ---")
    print("Dans un environnement réel, ces résultats seraient insérés dans 'nlp_similarity_metrics'.")

if __name__ == "__main__":
    run_experiment("Search_Baseline_Evaluation_v1")
