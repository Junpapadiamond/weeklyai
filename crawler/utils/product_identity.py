"""Use the same project identity rules as the deployed backend."""
import sys
from pathlib import Path

_BACKEND = str(Path(__file__).resolve().parents[2] / 'backend')
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from product_identity import (  # noqa: E402,F401
    SHARED_PRODUCT_HOSTS, catalog_url_key, hosted_project_key, is_shared_host,
    is_verified_hosted_product, product_identity_key,
)
