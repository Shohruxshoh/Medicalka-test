"""ORM models package.

Importing every model here ensures they are all registered on ``Base.metadata``,
which Alembic autogenerate relies on to detect the full schema.
"""

from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.models.verification_token import VerificationToken

__all__ = ["User", "Post", "Comment", "Like", "VerificationToken"]
