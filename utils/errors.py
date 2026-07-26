"""Centralized error handling helpers for SO!SB!Y!."""
from __future__ import annotations
import functools
import traceback
from typing import Any, Callable, Optional, Tuple, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def safe_call(fn: Callable[..., Any], *args, default: Any = None, **kwargs) -> Tuple[Any, Optional[str]]:
    """Execute fn; return (result, None) or (default, error_message)."""
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        return default, f"{type(e).__name__}: {e}"


def ui_guard(label: str = "Section"):
    """Decorator for Streamlit tab bodies — never crash the whole app."""
    def deco(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                try:
                    import streamlit as st
                    st.warning(f"{label} hit a snag and recovered.")
                    if st.session_state.get("show_sources"):
                        st.code(traceback.format_exc())
                    else:
                        st.caption(str(e))
                except Exception:
                    pass
                return None
        return wrapper  # type: ignore
    return deco


class FeedError(Exception):
    """Raised when all live feed sources fail."""


def format_feed_status(source: str, err: Optional[str] = None) -> str:
    if err:
        return f"feed:{source} · error:{err[:80]}"
    return f"feed:{source} · ok"
