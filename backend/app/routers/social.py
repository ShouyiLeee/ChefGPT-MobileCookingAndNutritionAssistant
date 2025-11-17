"""Social router for posts and community features."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List
from app.core.database import get_session
from app.core.security import get_current_user_id
from app.schemas.social import PostCreate, PostResponse, CommentCreate, CommentResponse
from app.models.social import Post, Comment, Like

router = APIRouter(prefix="/posts", tags=["Social"])


@router.get("", response_model=List[PostResponse])
async def get_posts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> List[PostResponse]:
    """Get public posts."""
    skip = (page - 1) * limit

    statement = (
        select(Post)
        .where(Post.is_public == True)
        .order_by(Post.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await session.execute(statement)
    posts = result.scalars().all()

    # TODO: Add author info and is_liked_by_me logic
    return [
        PostResponse(
            id=post.id,
            author_id=post.author_id,
            content=post.content,
            image_urls=post.image_urls.split(",") if post.image_urls else None,
            video_url=post.video_url,
            recipe_id=post.recipe_id,
            like_count=post.like_count,
            comment_count=post.comment_count,
            is_liked_by_me=False,  # TODO: Check if current user liked
            created_at=post.created_at,
        )
        for post in posts
    ]


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> PostResponse:
    """Create a new post."""
    image_urls_str = ",".join(post_data.image_urls) if post_data.image_urls else None

    post = Post(
        author_id=user_id,
        content=post_data.content,
        image_urls=image_urls_str,
        video_url=post_data.video_url,
        recipe_id=post_data.recipe_id,
    )

    session.add(post)
    await session.commit()
    await session.refresh(post)

    return PostResponse(
        id=post.id,
        author_id=post.author_id,
        content=post.content,
        image_urls=post_data.image_urls,
        video_url=post.video_url,
        recipe_id=post.recipe_id,
        like_count=0,
        comment_count=0,
        is_liked_by_me=False,
        created_at=post.created_at,
    )


@router.post("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_post(
    post_id: int,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Like a post."""
    # Check if post exists
    post_statement = select(Post).where(Post.id == post_id)
    post_result = await session.execute(post_statement)
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    # Check if already liked
    like_statement = select(Like).where(
        Like.post_id == post_id,
        Like.user_id == user_id,
    )
    like_result = await session.execute(like_statement)
    existing_like = like_result.scalar_one_or_none()

    if existing_like:
        # Unlike
        await session.delete(existing_like)
        post.like_count = max(0, post.like_count - 1)
    else:
        # Like
        like = Like(user_id=user_id, post_id=post_id)
        session.add(like)
        post.like_count += 1

    await session.commit()


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    post_id: int,
    session: AsyncSession = Depends(get_session),
) -> List[CommentResponse]:
    """Get comments for a post."""
    statement = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.desc())
    )

    result = await session.execute(statement)
    comments = result.scalars().all()

    # TODO: Add user info
    return [
        CommentResponse(
            id=comment.id,
            user_id=comment.user_id,
            content=comment.content,
            like_count=comment.like_count,
            parent_id=comment.parent_id,
            created_at=comment.created_at,
        )
        for comment in comments
    ]


@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> CommentResponse:
    """Create a comment on a post."""
    # Check if post exists
    post_statement = select(Post).where(Post.id == post_id)
    post_result = await session.execute(post_statement)
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    comment = Comment(
        post_id=post_id,
        user_id=user_id,
        content=comment_data.content,
        parent_id=comment_data.parent_id,
    )

    session.add(comment)
    post.comment_count += 1

    await session.commit()
    await session.refresh(comment)

    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        content=comment.content,
        like_count=0,
        parent_id=comment.parent_id,
        created_at=comment.created_at,
    )
