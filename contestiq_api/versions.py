"""Version identifiers shared by every analysis-related API response.

Bump these deliberately:
- ANALYSIS_VERSION: the analysis/scoring pipeline (mirrors MODEL_VERSION).
- TAXONOMY_VERSION: the skill taxonomy / tag mapping tables.
- PROBLEM_CATALOG_VERSION: the normalized Codeforces problem catalog.
"""

from contestiq_api import MODEL_VERSION

ANALYSIS_VERSION = MODEL_VERSION
TAXONOMY_VERSION = "taxonomy_v1"
PROBLEM_CATALOG_VERSION = "cf_problemset_v1"
