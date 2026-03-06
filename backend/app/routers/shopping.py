"""Shopping router — mock grocery list for MVP demo."""
import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/shopping-list", tags=["Grocery (Mock)"])

_MOCK_FILE = Path(__file__).parent.parent / "mocks" / "shopping.json"


@router.get("")
@router.get("/mock")
async def get_shopping_list():
    """Return mock grocery list (hardcoded demo data)."""
    return json.loads(_MOCK_FILE.read_text(encoding="utf-8"))
