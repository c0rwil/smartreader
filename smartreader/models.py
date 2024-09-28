from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    description = Column(String)
    content = Column(Text)  # Store book content
    page_count = Column(Integer)  # New attribute to store estimated page count

    # Relationships if there are linked tables
    # characters = relationship("Character", back_populates="book")
class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # Assuming user authentication in the future
    book_id = Column(Integer, ForeignKey("books.id"))
    current_page = Column(Integer, default=1)

    book = relationship("Book")