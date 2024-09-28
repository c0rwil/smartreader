from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from smartreader import crud, models, schemas
from smartreader.database import get_db
from smartreader.utils import extract_metadata, extract_content, extract_entities
import os
import shutil


router = APIRouter()
UPLOAD_DIR = "./uploads"

# Route to upload a book
@router.post("/books/upload/", response_model=schemas.Book)
async def upload_book(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Create upload directory if it doesn't exist
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        # Save the uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract metadata and process the book
        metadata = extract_metadata(file_path)
        content, page_count = extract_content(file_path)

        # Store in the database
        book = crud.create_book(
            db=db, title=metadata["title"], author=metadata["author"], description=metadata.get("description", ""),
            content=content, page_count=page_count
        )

        return book

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to get knowledge up to user's current progress in a book
# books.py
@router.get("/books/{book_id}/knowledge", response_model=schemas.Book)
def get_book_knowledge(book_id: int, user_id: int = Query(...), db: Session = Depends(get_db)):
    db_book = crud.get_book(db=db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Get user progress to limit content to their current page
    user_progress = crud.get_user_progress(db=db, user_id=user_id, book_id=book_id)
    if user_progress is None:
        raise HTTPException(status_code=404, detail="User progress not found")

    # Extract the relevant content up to the user's current page
    pages = db_book.content.split("\n\n")  # Assuming '\n\n' indicates page breaks
    limited_content = "\n\n".join(pages[:user_progress.current_page])

    # Extract entities based on limited content, using the author name from the book metadata
    entities = extract_entities(limited_content, db_book.author)

    return {
        "id": db_book.id,
        "title": db_book.title,
        "author": db_book.author,
        "description": db_book.description,
        "page_count": db_book.page_count,
        "characters": entities["characters"],
        "locations": entities["locations"],
        "events": entities["events"],
        "groups": entities.get("groups", [])  # Include groups if present
    }



# Route to read a book's basic details
@router.get("/books/{book_id}", response_model=schemas.Book)
def read_book(book_id: int, db: Session = Depends(get_db)):
    db_book = crud.get_book(db=db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return db_book

# Route to list books with pagination
@router.get("/books/", response_model=list[schemas.Book])
def read_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_books(db=db, skip=skip, limit=limit)

# Route to update the user's current progress in a book
@router.post("/user-progress/", response_model=schemas.UserProgress)
def update_user_progress(user_id: int = Form(...), book_id: int = Form(...), current_page: int = Form(...), db: Session = Depends(get_db)):
    return crud.create_or_update_user_progress(db=db, user_id=user_id, book_id=book_id, current_page=current_page)

# Route to get a recap of the last pages read up to the user's current progress
@router.get("/books/{book_id}/recap", response_model=dict)
def get_recap(book_id: int, user_id: int, db: Session = Depends(get_db)):
    db_book = crud.get_book(db=db, book_id=book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    user_progress = crud.get_user_progress(db=db, user_id=user_id, book_id=book_id)
    if user_progress is None:
        raise HTTPException(status_code=404, detail="User progress not found")

    # Get content up to the user's current chapter or page
    pages = db_book.content.split("\n\n")
    recap_content = "\n\n".join(pages[max(0, user_progress.current_page - 5):user_progress.current_page])  # Last 5 pages as a recap

    return {"recap": recap_content}
