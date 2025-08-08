"""
Centralized memory management utilities.

Safe operations only: works even if optional backends are absent.
"""

import gc
import logging
import threading
from typing import Optional


_logger = logging.getLogger(__name__)
_lock = threading.Lock()


def free_memory(context: Optional[str] = None) -> None:
    """Force memory cleanup across backends.

    - Python GC
    - Torch CUDA cache (if available)
    - Best-effort MLX cache hints (no-op if not available)
    """
    with _lock:
        try:
            # Python objects
            gc.collect()
        except Exception as e:
            _logger.debug(f"GC error: {e}")

        # PyTorch GPU cache (safe on CPU-only systems)
        try:
            import torch  # noqa: WPS433
            cuda_attr = getattr(torch, "cuda", None)
            is_avail = getattr(cuda_attr, "is_available", None)
            empty_cache = getattr(cuda_attr, "empty_cache", None)
            if callable(is_avail) and callable(empty_cache) and is_avail():
                empty_cache()
        except Exception as e:  # pragma: no cover
            _logger.debug(f"Torch cleanup skipped: {e}")

        # MLX best-effort hint (no official global empty cache API)
        # Keep silent if not present.
        try:  # pragma: no cover
            import mlx.core as mx  # type: ignore
            _ = mx.array([0])
            del _
        except Exception:
            pass


def log_process_memory(note: str = "") -> None:
    """Log process memory usage if OS APIs are available (best effort)."""
    try:
        import resource  # Unix only

        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss_kb = getattr(usage, "ru_maxrss", 0)
        rss_mb = rss_kb / 1024.0
        if note:
            _logger.info(f"Memory usage ~{rss_mb:.1f} MB ({note})")
        else:
            _logger.info(f"Memory usage ~{rss_mb:.1f} MB")
    except Exception:
        # Avoid any dependency here; logging memory is optional
        pass


