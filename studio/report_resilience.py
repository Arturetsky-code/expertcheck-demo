from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def build_report_isolated(
    builder: Callable[[], T],
    on_error: Callable[[Exception], None],
) -> T | None:
    """Build one export without allowing its failure to break sibling exports."""
    try:
        return builder()
    except Exception as exc:
        on_error(exc)
        return None
