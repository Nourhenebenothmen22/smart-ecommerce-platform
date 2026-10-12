"""
ml/tests/__init__.py — Test package root.
Ensures project root and ml directory are on sys.path for all domain tests.
"""

import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_ML_ROOT = os.path.dirname(_TESTS_DIR)
_PROJECT_ROOT = os.path.dirname(_ML_ROOT)

for _p in (_PROJECT_ROOT, _ML_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
