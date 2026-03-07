"""Shopping router — mock grocery list for MVP demo."""
import json
import time
from pathlib import Path

from fastapi import APIRouter
from loguru import logger

router = APIRouter(prefix="/shopping-list", tags=["Grocery (Mock)"])

_MOCK_FILE = Path(__file__).parent.parent / "mocks" / "shopping.json"


@router.get("")
@router.get("/mock")
async def get_shopping_list():
    """Return mock grocery list (hardcoded demo data)."""
    logger.debug("mock:get_shopping_list | file={}", _MOCK_FILE.name)
    t0 = time.perf_counter()
    data = json.loads(_MOCK_FILE.read_text(encoding="utf-8"))
    items = data.get("items", data) if isinstance(data, dict) else data
    item_count = len(items) if isinstance(items, list) else "?"
    logger.info(
        "mock:get_shopping_list | source=file items_count={} latency={}ms",
        item_count, round((time.perf_counter() - t0) * 1000, 1),
    )
    return data
