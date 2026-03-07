"""Social router — real social feed with posts, likes, and comments."""
import json
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import get_current_user_id
from app.models.social import Comment, Like, Post
from app.models.user import Profile
from app.schemas.social import CommentCreate, CommentResponse, PostCreate, PostResponse

router = APIRouter(prefix="/posts", tags=["Social"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _build_post_response(
    post: Post, current_user_id: str, session: AsyncSession
) -> PostResponse:
    """Build PostResponse with author info and liked-by-me status."""
    profile_q = select(Profile).where(Profile.user_id == post.author_id)
    profile = (await session.execute(profile_q)).scalar_one_or_none()

    like_q = select(Like).where(
        Like.user_id == current_user_id, Like.post_id == post.id
    )
    is_liked = (await session.execute(like_q)).scalar_one_or_none() is not None

    image_urls = None
    if post.image_urls:
        try:
            image_urls = json.loads(post.image_urls)
        except Exception:
            pass

    return PostResponse(
        id=post.id,
        author_id=post.author_id,
        author_name=profile.name if profile else "ChefGPT User",
        author_avatar=profile.avatar_url if profile else None,
        content=post.content,
        image_urls=image_urls,
        like_count=post.like_count,
        comment_count=post.comment_count,
        is_liked_by_me=is_liked,
        created_at=post.created_at,
    )


# ── Feed ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=dict)
async def get_posts(
    page: int = 1,
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Get paginated social feed (newest first)."""
    logger.debug("db:get_posts | page={} limit={}", page, limit)
    t0 = time.perf_counter()
    offset = (page - 1) * limit
    q = (
        select(Post)
        .where(Post.is_public == True)  # noqa: E712
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    posts = (await session.execute(q)).scalars().all()

    responses = []
    for p in posts:
        r = await _build_post_response(p, current_user_id, session)
        responses.append(r.model_dump())

    logger.info(
        "db:get_posts | page={} posts_returned={} has_more={} latency={}ms",
        page, len(posts), len(posts) == limit,
        round((time.perf_counter() - t0) * 1000, 1),
    )
    return {"posts": responses, "page": page, "has_more": len(posts) == limit}


# ── Create post ───────────────────────────────────────────────────────────────

@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: PostCreate,
    current_user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Create a new post."""
    logger.info(
        "db:create_post | content_len={} image_count={}",
        len(body.content), len(body.image_urls or []),
    )
    t0 = time.perf_counter()
    image_json = json.dumps(body.image_urls) if body.image_urls else None
    post = Post(
        author_id=current_user_id,
        content=body.content,
        image_urls=image_json,
        created_at=datetime.utcnow(),
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    logger.info(
        "db:create_post | ok post_id={} latency={}ms",
        post.id, round((time.perf_counter() - t0) * 1000, 1),
    )
    return await _build_post_response(post, current_user_id, session)


# ── Delete post ───────────────────────────────────────────────────────────────

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Delete own post (author only)."""
    logger.info("db:delete_post | post_id={}", post_id)
    t0 = time.perf_counter()
    q = select(Post).where(Post.id == post_id, Post.author_id == current_user_id)
    post = (await session.execute(q)).scalar_one_or_none()
    if not post:
        logger.warning("db:delete_post | not_found_or_forbidden post_id={}", post_id)
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    await session.delete(post)
    await session.commit()
    logger.info(
        "db:delete_post | ok post_id={} latency={}ms",
        post_id, round((time.perf_counter() - t0) * 1000, 1),
    )


# ── Like / unlike ─────────────────────────────────────────────────────────────

@router.post("/{post_id}/like", response_model=dict)
async def toggle_like(
    post_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Toggle like on a post. Returns {liked: bool, like_count: int}."""
    t0 = time.perf_counter()
    post = (await session.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    like_q = select(Like).where(Like.user_id == current_user_id, Like.post_id == post_id)
    existing = (await session.execute(like_q)).scalar_one_or_none()

    if existing:
        await session.delete(existing)
        post.like_count = max(0, post.like_count - 1)
        liked = False
    else:
        session.add(Like(user_id=current_user_id, post_id=post_id))
        post.like_count += 1
        liked = True

    session.add(post)
    await session.commit()

    logger.info(
        "db:toggle_like | post_id={} action={} new_like_count={} latency={}ms",
        post_id, "liked" if liked else "unliked", post.like_count,
        round((time.perf_counter() - t0) * 1000, 1),
    )
    return {"liked": liked, "like_count": post.like_count}


# ── Comments ──────────────────────────────────────────────────────────────────

@router.get("/{post_id}/comments", response_model=dict)
async def get_comments(
    post_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Get top-level comments for a post."""
    logger.debug("db:get_comments | post_id={}", post_id)
    t0 = time.perf_counter()
    q = (
        select(Comment)
        .where(Comment.post_id == post_id, Comment.parent_id == None)  # noqa: E711
        .order_by(Comment.created_at.asc())
    )
    comments = (await session.execute(q)).scalars().all()

    result = []
    for c in comments:
        profile_q = select(Profile).where(Profile.user_id == c.user_id)
        profile = (await session.execute(profile_q)).scalar_one_or_none()
        result.append(
            CommentResponse(
                id=c.id,
                user_id=c.user_id,
                user_name=profile.name if profile else "ChefGPT User",
                user_avatar=profile.avatar_url if profile else None,
                content=c.content,
                like_count=c.like_count,
                parent_id=c.parent_id,
                created_at=c.created_at,
            ).model_dump()
        )

    logger.info(
        "db:get_comments | post_id={} count={} latency={}ms",
        post_id, len(result), round((time.perf_counter() - t0) * 1000, 1),
    )
    return {"comments": result}


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: int,
    body: CommentCreate,
    current_user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """Add a comment to a post."""
    logger.info(
        "db:create_comment | post_id={} content_len={} parent_id={}",
        post_id, len(body.content), body.parent_id,
    )
    t0 = time.perf_counter()
    post = (await session.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment(
        post_id=post_id,
        user_id=current_user_id,
        content=body.content,
        parent_id=body.parent_id,
        created_at=datetime.utcnow(),
    )
    session.add(comment)
    post.comment_count += 1
    session.add(post)
    await session.commit()
    await session.refresh(comment)

    profile_q = select(Profile).where(Profile.user_id == current_user_id)
    profile = (await session.execute(profile_q)).scalar_one_or_none()

    logger.info(
        "db:create_comment | ok comment_id={} post_id={} latency={}ms",
        comment.id, post_id, round((time.perf_counter() - t0) * 1000, 1),
    )
    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        user_name=profile.name if profile else "ChefGPT User",
        user_avatar=profile.avatar_url if profile else None,
        content=comment.content,
        like_count=0,
        parent_id=comment.parent_id,
        created_at=comment.created_at,
    )
