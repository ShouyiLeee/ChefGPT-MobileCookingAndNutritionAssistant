"""Social router — mock data for MVP demo."""
import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/posts", tags=["Social (Mock)"])

_MOCK_FILE = Path(__file__).parent.parent / "mocks" / "posts.json"


@router.get("")
@router.get("/mock")
async def get_posts():
    """Return mock social feed (hardcoded demo data)."""
    posts = json.loads(_MOCK_FILE.read_text(encoding="utf-8"))
    return {"posts": posts}
