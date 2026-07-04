"""Feed assembly: users -> their posts -> the likes on each post.

Built to avoid N+1 queries: one query for the page of users, one for all their
posts, and one for all likes on those posts — then grouped in memory.
"""

import uuid

from app.models.post import Post
from app.repositories.like_repository import LikeRepository
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository
from app.schemas.feed import FeedPost, FeedUser
from app.schemas.pagination import Page, PaginationParams


class FeedService:
    def __init__(
        self,
        users: UserRepository,
        posts: PostRepository,
        likes: LikeRepository,
    ) -> None:
        self.users = users
        self.posts = posts
        self.likes = likes

    async def get_feed(self, pagination: PaginationParams) -> Page[FeedUser]:
        users = await self.users.list(limit=pagination.limit, offset=pagination.offset)
        total = await self.users.count()

        posts = await self.posts.list_for_authors([u.id for u in users])
        like_pairs = await self.likes.user_ids_for_posts([p.id for p in posts])

        # Group likes by post, and posts by author.
        likes_by_post: dict[uuid.UUID, list[uuid.UUID]] = {}
        for post_id, user_id in like_pairs:
            likes_by_post.setdefault(post_id, []).append(user_id)

        posts_by_author: dict[uuid.UUID, list[Post]] = {}
        for post in posts:
            posts_by_author.setdefault(post.author_id, []).append(post)

        items = [
            FeedUser(
                username=user.username,
                posts=[
                    FeedPost(
                        id=post.id,
                        title=post.title,
                        content=post.content,
                        likes=likes_by_post.get(post.id, []),
                    )
                    for post in posts_by_author.get(user.id, [])
                ],
            )
            for user in users
        ]

        pages = (total + pagination.page_size - 1) // pagination.page_size
        return Page[FeedUser](
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )
