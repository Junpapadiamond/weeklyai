# Services package
#
# This package provides product-related services for the WeeklyAI backend.
#
# Module structure:
# - product_service.py: High-level business logic (main API)
# - product_repository.py: Data loading, file I/O, caching
# - product_filters.py: Filtering and validation logic
# - product_sorting.py: Sorting and diversification utilities
#
# For backward compatibility, import ProductService from this package:
#   from app.services import ProductService
# or:
#   from app.services.product_service import ProductService

from .product_service import ProductService
from .product_repository import ProductRepository
from . import product_filters
from . import product_sorting

__all__ = [
    'ProductService',
    'ProductRepository',
    'product_filters',
    'product_sorting',
]
