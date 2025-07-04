from typing import Optional
import threading

_pytest_context = threading.local()


def get_current_test_nodeid() -> Optional[str]:
    item = getattr(_pytest_context, "current_item", None)
    return item.nodeid if item is not None else None
