from setuptools import setup, find_packages

setup(
    name="smartreader",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pydantic",
        "databases",
        "alembic",
        "EbookLib",
        "beautifulsoup4",
        "spacy"
    ],
    entry_points={
        "console_scripts": [
            "smartreader = smartreader.main:run_app",
        ]
    },
)
