"""Pagination helpers shared across list endpoints."""

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams:
    """Common ``?page=`` & ``?page_size=`` query parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="1-based page number"),
        page_size: int = Query(20, ge=1, le=100, description="items per page"),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.limit = page_size
        self.offset = (page - 1) * page_size


class Page(BaseModel, Generic[T]):
    """A single page of results plus paging metadata."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int
