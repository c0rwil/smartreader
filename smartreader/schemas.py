from pydantic import BaseModel
from typing import List

class BookBase(BaseModel):
    title: str
    author: str
    description: str = None

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    page_count: int
    characters: List[str] = []
    locations: List[str] = []
    events: List[str] = []
    groups: List[str] = []  # Added groups to the schema

    class Config:
        from_attributes = True

class UserProgress(BaseModel):
    user_id: int
    book_id: int
    current_page: int

    class Config:
        from_attributes = True