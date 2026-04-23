import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "ecommerce_ml_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASS = os.environ.get("DB_PASS", "postgres")

def get_connection():
    # Try typical ports
    ports_to_try = [os.environ.get("DB_PORT", "5432"), "5433", "5432"]
    for p in ports_to_try:
        try:
            conn = psycopg2.connect(host=DB_HOST, port=p, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
            return conn
        except Exception:
            pass
    raise Exception("Impossible de se connecter à la base de données PostgreSQL locale.")

def run_deep_audit():
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        audit_results = {
            "1_ETAT_DES_TABLES": {},
            "2_NLP_ET_EMBEDDINGS": {},
            "3_CHATBOT_INTERACTIONS": {},
            "4_COHERENCE_DONNEES": {}
        }

        # ---------------------------------------------------------
        # 1. Vérification des tables principales
        # ---------------------------------------------------------
        tables = ['users', 'products', 'reviews', 'orders', 'user_features', 'product_embeddings', 'chatbot_interactions', 'nlp_similarity_metrics']
        
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) as count FROM {table};")
                audit_results["1_ETAT_DES_TABLES"][table] = cur.fetchone()['count']
            except psycopg2.errors.UndefinedTable:
                conn.rollback() # Reset transaction after error
                audit_results["1_ETAT_DES_TABLES"][table] = "[ERREUR] TABLE INEXISTANTE"

        # ---------------------------------------------------------
        # 2. Audit NLP & VECTEURS (pgvector)
        # ---------------------------------------------------------
        # Check pgvector extension
        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        ext = cur.fetchone()
        audit_results["2_NLP_ET_EMBEDDINGS"]["pgvector_installe"] = "[OK] OUI" if ext else "[ERREUR] NON"

        if audit_results["1_ETAT_DES_TABLES"].get("product_embeddings") not in [None, "[ERREUR] TABLE INEXISTANTE"]:
            # Check products without embeddings
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM products p 
                LEFT JOIN product_embeddings pe ON p.id = pe.product_id 
                WHERE pe.product_id IS NULL;
            """)
            missing = cur.fetchone()['count']
            audit_results["2_NLP_ET_EMBEDDINGS"]["produits_sans_embeddings"] = missing
            if missing > 0:
                audit_results["2_NLP_ET_EMBEDDINGS"]["coherence_vecteurs"] = f"[ERREUR] {missing} produits n'ont pas d'embeddings!"
            else:
               audit_results["2_NLP_ET_EMBEDDINGS"]["coherence_vecteurs"] = "[OK] Tous les produits ont un embedding."

        # ---------------------------------------------------------
        # 3. Audit CHATBOT
        # ---------------------------------------------------------
        if audit_results["1_ETAT_DES_TABLES"].get("chatbot_interactions") != "[ERREUR] TABLE INEXISTANTE":
            count_chatbot = audit_results["1_ETAT_DES_TABLES"].get("chatbot_interactions", 0)
            if count_chatbot == 0:
                audit_results["3_CHATBOT_INTERACTIONS"]["historique_conversations"] = "[ATTENTION] AUCUNE INTERACTION. La table est complètement vide."
            else:
                cur.execute("SELECT COUNT(*) as count FROM chatbot_interactions WHERE llm_response IS NULL OR llm_response = '';")
                empty_responses = cur.fetchone()['count']
                audit_results["3_CHATBOT_INTERACTIONS"]["reponses_llm_vides"] = empty_responses
                
                cur.execute("SELECT COUNT(DISTINCT retrieval_algorithm) as count FROM chatbot_interactions;")
                algos = cur.fetchone()['count']
                audit_results["3_CHATBOT_INTERACTIONS"]["algorithmes_utilises"] = algos

        # ---------------------------------------------------------
        # 4. Audit de Cohérence Générale
        # ---------------------------------------------------------
        # Check orphaned reviews
        cur.execute("SELECT COUNT(*) as count FROM reviews WHERE product_id NOT IN (SELECT id FROM products);")
        audit_results["4_COHERENCE_DONNEES"]["avis_orphelins_produits_inexistants"] = cur.fetchone()['count']
        
        # Display the report
        print("====== RÉSULTAT DE L'AUDIT DE LA BASE DE DONNÉES ======\n")
        print(json.dumps(audit_results, indent=3))
        print("\n=======================================================")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"ERREUR CRITIQUE PENDANT L'AUDIT: {e}")

if __name__ == "__main__":
    run_deep_audit()
