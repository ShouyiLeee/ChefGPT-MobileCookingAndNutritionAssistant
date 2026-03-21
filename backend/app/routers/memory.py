"""Memory router — user's personal AI memory management."""
import time

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.memory import (
    AddMemoryRequest,
    DeleteAllResponse,
    MemoryListResponse,
    MemoryResponse,
    UpdateMemoryRequest,
)
from app.services.cache import cache_service
from app.services.memory_service import CATEGORY_CONFIG, memory_service

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.get("/me", response_model=MemoryListResponse)
async def get_my_memories(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> MemoryListResponse:
    """
    Trả về tất cả memories đang active của user, kèm preview của context block
    sẽ được inject vào LLM.
    """
    t0 = time.perf_counter()
    memories = await memory_service.get_all(user_id, session)

    # Build context preview (same format used in LLM injection)
    context = await memory_service.get_context_block(user_id, session, cache_service)

    logger.info(
        "router:memory:get | user_id={} count={} latency={}ms",
        user_id, len(memories), round((time.perf_counter() - t0) * 1000, 1),
    )
    return MemoryListResponse(
        memories=[
            MemoryResponse(
                id=m.id,
                category=m.category,
                key=m.key,
                value=m.value,
                confidence=m.confidence,
                source=m.source,
                created_at=m.created_at,
            )
            for m in memories
        ],
        total=len(memories),
        context_preview=context,
    )


@router.post("/me", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def add_memory(
    request: AddMemoryRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> MemoryResponse:
    """
    Thêm memory thủ công (source='explicit').
    Nếu entry (category, key, value) đã tồn tại → trả về 409.
    """
    t0 = time.perf_counter()
    try:
        mem = await memory_service.add_explicit(
            user_id,
            request.category,
            request.key,
            request.value,
            session,
            cache=cache_service,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    logger.info(
        "router:memory:add | user_id={} category={} key={} value={} latency={}ms",
        user_id, request.category, request.key, request.value,
        round((time.perf_counter() - t0) * 1000, 1),
    )
    return MemoryResponse(
        id=mem.id,
        category=mem.category,
        key=mem.key,
        value=mem.value,
        confidence=mem.confidence,
        source=mem.source,
        created_at=mem.created_at,
    )


@router.put("/me/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: int,
    request: UpdateMemoryRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> MemoryResponse:
    """Cập nhật giá trị của một memory entry theo ID."""
    t0 = time.perf_counter()
    mem = await memory_service.update(
        user_id, memory_id, request.value, session, cache=cache_service
    )
    if not mem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory entry not found",
        )
    logger.info(
        "router:memory:update | user_id={} memory_id={} value={!r} latency={}ms",
        user_id, memory_id, request.value[:50],
        round((time.perf_counter() - t0) * 1000, 1),
    )
    return MemoryResponse(
        id=mem.id,
        category=mem.category,
        key=mem.key,
        value=mem.value,
        confidence=mem.confidence,
        source=mem.source,
        created_at=mem.created_at,
    )


@router.delete("/me/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: int,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Xóa (soft-delete) một memory entry theo ID."""
    t0 = time.perf_counter()
    deleted = await memory_service.delete(user_id, memory_id, session, cache=cache_service)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory entry not found",
        )
    logger.info(
        "router:memory:delete | user_id={} memory_id={} latency={}ms",
        user_id, memory_id, round((time.perf_counter() - t0) * 1000, 1),
    )


@router.delete("/me", response_model=DeleteAllResponse)
async def clear_all_memories(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> DeleteAllResponse:
    """Xóa toàn bộ memories của user — ChefGPT sẽ 'quên' tất cả."""
    t0 = time.perf_counter()
    count = await memory_service.clear_all(user_id, session, cache=cache_service)
    logger.info(
        "router:memory:clear_all | user_id={} deleted={} latency={}ms",
        user_id, count, round((time.perf_counter() - t0) * 1000, 1),
    )
    return DeleteAllResponse(
        deleted=count,
        message=f"Đã xóa {count} memories. ChefGPT sẽ không còn nhớ thông tin cũ.",
    )


@router.get("/categories")
async def get_categories():
    """Trả về danh sách category + icon + label — dùng để render UI."""
    return [
        {"id": cat_id, "icon": cfg["icon"], "label": cfg["label"]}
        for cat_id, cfg in CATEGORY_CONFIG.items()
    ]
