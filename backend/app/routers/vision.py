"""Vision router — ingredient recognition via Gemini Vision."""
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger

from app.core.config import settings
from app.core.security import get_current_user_id
from app.services.llm import llm_provider

router = APIRouter(prefix="/ingredients", tags=["Vision"])

_ALLOWED = {f"image/{ext}" for ext in ["jpeg", "jpg", "png", "webp"]}


def _validate_image(image: UploadFile) -> None:
    if not image.content_type or image.content_type not in _ALLOWED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (jpeg/png/webp)",
        )


@router.post("/recognize")
async def recognize_ingredients(
    image: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """Recognize food ingredients from an uploaded photo using Gemini Vision."""
    _validate_image(image)
    image_bytes = await image.read()
    image_kb = round(len(image_bytes) / 1024, 1)

    logger.info(
        "router:recognize_ingredients | filename={} content_type={} size={}KB",
        image.filename, image.content_type, image_kb,
    )

    if len(image_bytes) > settings.max_upload_size:
        logger.warning(
            "router:recognize_ingredients | rejected size={}KB max={}KB",
            image_kb, settings.max_upload_size // 1024,
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image too large (max 10MB)",
        )

    t0 = time.perf_counter()
    try:
        result = await llm_provider.recognize_ingredients(image_bytes)
        found = result.get("ingredients", [])
        logger.info(
            "router:recognize_ingredients | ok found={} latency={}ms",
            len(found), round((time.perf_counter() - t0) * 1000, 1),
        )
        return result
    except Exception as e:
        logger.error(
            "router:recognize_ingredients | error={} latency={}ms",
            str(e)[:200], round((time.perf_counter() - t0) * 1000, 1),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}",
        )
