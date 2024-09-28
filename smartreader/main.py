from fastapi import FastAPI
from smartreader.database import engine, Base
from smartreader.routers import books

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include routers
app.include_router(books.router, prefix="/api/v1", tags=["books"])

def run_app():
    import uvicorn
    uvicorn.run("smartreader.main:app", host="127.0.0.1", port=8000, reload=True)
