from pathlib import Path
from pydantic import BaseModel


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
CACHE_DIR = PROJECT_ROOT / ".cache" / "codeforces"

CODEFORCES_API_BASE = "https://codeforces.com/api"
DEFAULT_TIMEOUT_SECONDS = 20
MAX_RETRIES = 3
RATE_LIMIT_SECONDS = 2.0

DEFAULT_OVERALL_RATING = 1200


class ModelThresholds(BaseModel):
    likely_needs_work_confidence_threshold: float = 0.55
    likely_needs_work_n_eff_threshold: float = 6.0
    likely_needs_work_distinct_problem_threshold: int = 4
    repair_severity_threshold: float = 0.48
    repair_confidence_threshold: float = 0.55
    repair_n_eff_threshold: float = 6.0
    repair_distinct_problem_threshold: int = 4
    focused_practice_severity_threshold: float = 0.25
    focused_practice_confidence_threshold: float = 0.65
    focused_practice_n_eff_threshold: float = 6.0
    focused_practice_distinct_problem_threshold: int = 4
    focused_practice_min_avg_tag_reliability: float = 0.65


MODEL_THRESHOLDS = ModelThresholds()
