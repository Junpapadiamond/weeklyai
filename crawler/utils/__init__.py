# Crawler utilities
#
# Keep these imports best-effort so lightweight tools (like data verification)
# can import `utils.*` without requiring every optional dependency to be present.

__all__ = []

try:
    from .image_utils import get_best_logo  # noqa: F401

    __all__.append("get_best_logo")
except Exception:
    # Optional in environments that don't run the crawler itself.
    pass

try:
    from .video_utils import enrich_product_with_video, get_video_thumbnail, search_youtube_video  # noqa: F401

    __all__.extend(["search_youtube_video", "get_video_thumbnail", "enrich_product_with_video"])
except Exception:
    # Optional in environments that don't run the crawler itself.
    pass
