"""
ml/scripts/generate_embeddings.py — CLI Runner for Product Embeddings.
Invokes the unified embedding pipeline in ml.rag.embeddings.
"""

import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ML_ROOT = _SCRIPT_DIR
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
for _p in (_PROJECT_ROOT, _SCRIPT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

try:
    from ml.rag.embeddings import generate_product_embeddings
except ImportError:
    from rag.embeddings import generate_product_embeddings


def run():
    batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))
    count = generate_product_embeddings(batch_size=batch_size)
    print(f"✅ Succès : {count} embeddings de produits enregistrés dans PostgreSQL (table product_embeddings).")


if __name__ == "__main__":
    run()
