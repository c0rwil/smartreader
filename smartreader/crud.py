from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from . import models, schemas


def get_book(db: Session, book_id: int) -> models.Book:
    try:
        return db.query(models.Book).filter(models.Book.id == book_id).first()
    except SQLAlchemyError as e:
        print(f"Error retrieving book with ID {book_id}: {e}")
        return None


def get_books(db: Session, skip: int = 0, limit: int = 10) -> list[models.Book]:
    try:
        return db.query(models.Book).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        print(f"Error retrieving books: {e}")
        return []


def create_book(db: Session, title: str, author: str, description: str, content: str, page_count: int) -> models.Book:
    try:
        db_book = models.Book(title=title, author=author, description=description, content=content,
                              page_count=page_count)
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        return db_book
    except SQLAlchemyError as e:
        db.rollback()  # Rollback in case of an error
        print(f"Error creating book: {e}")
        return None


def get_user_progress(db: Session, user_id: int, book_id: int) -> models.UserProgress:
    try:
        return db.query(models.UserProgress).filter(models.UserProgress.user_id == user_id,
                                                    models.UserProgress.book_id == book_id).first()
    except SQLAlchemyError as e:
        print(f"Error retrieving user progress for user {user_id} and book {book_id}: {e}")
        return None


def create_or_update_user_progress(db: Session, user_id: int, book_id: int, current_page: int) -> models.UserProgress:
    try:
        user_progress = get_user_progress(db, user_id, book_id)
        if user_progress:
            user_progress.current_page = current_page
        else:
            user_progress = models.UserProgress(user_id=user_id, book_id=book_id, current_page=current_page)
            db.add(user_progress)

        db.commit()
        db.refresh(user_progress)
        return user_progress
    except SQLAlchemyError as e:
        db.rollback()  # Rollback in case of an error
        print(f"Error creating or updating user progress: {e}")
        return None