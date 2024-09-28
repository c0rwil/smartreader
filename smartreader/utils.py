from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
import spacy
from spacy.tokens import Doc
from spacy.lang.en.stop_words import STOP_WORDS
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

# Load spaCy English model (using a larger model for improved accuracy)
nlp = spacy.load("en_core_web_md")

# Define a function to extract metadata from an ePub file
def extract_metadata(file_path: str) -> dict:
    """
    Extract metadata (title, author, description) from an ePub file.
    """
    if file_path.endswith(".epub"):
        return extract_epub_metadata(file_path)
    # You can add more format handlers (e.g., PDFs) here
    return {}

# Extract metadata from an ePub file
def extract_epub_metadata(file_path: str) -> dict:
    book = epub.read_epub(file_path)
    metadata = {
        "title": book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Unknown Title",
        "author": book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown Author",
        "description": book.get_metadata('DC', 'description')[0][0] if book.get_metadata('DC', 'description') else ""
    }
    return metadata

# Extract book content based on its format
def extract_content(file_path: str) -> tuple:
    """
    Extract the content from an ePub file or other book format.
    Returns the content and an estimated page count.
    """
    if file_path.endswith(".epub"):
        content = extract_epub_content(file_path)
        print(f"Extracted Content: {content[:500]}...")  # Debug: Print the first 500 characters for verification

        # Estimate page count
        word_count = len(content.split())
        words_per_page = 300  # Assume an average of 300 words per page
        page_count = max(1, word_count // words_per_page)  # Ensure at least 1 page

        return content, page_count
    return "", 0

# Helper function to process each ePub item in a separate thread
def process_epub_item(item) -> str:
    """
    Extract the text content from an ePub item using BeautifulSoup.
    """
    soup = BeautifulSoup(item.get_body_content(), 'html.parser')
    return soup.get_text().strip()  # Use .strip() to remove leading/trailing whitespace

# Extract content from an ePub file with multithreading
def extract_epub_content(file_path: str) -> str:
    """
    Extract content from an ePub file using multithreading to improve performance.
    Assumes 3 cores are available for concurrent processing.
    """
    book = epub.read_epub(file_path)
    items = list(book.get_items_of_type(ITEM_DOCUMENT))

    # Use ThreadPoolExecutor with 3 workers to parallelize extraction
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(process_epub_item, items))

    # Combine all extracted content into a single string
    return "\n\n".join(results)

# Extract entities such as characters, locations, and events from the content

def extract_entities(content: str, author_name: str) -> dict:
    """
    Extract named entities (characters, locations, events, and groups) from the book content using spaCy.
    Apply custom filtering to remove irrelevant or duplicate entities, including dynamically filtering out the author's name.
    """
    characters = []
    groups = set()
    locations = []
    events = []

    # List of pronouns and common irrelevant words to filter out
    pronouns = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves",
                "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself",
                "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
                "theirs", "themselves"}

    # Convert author's name to lowercase for consistent comparison and split it to remove both first and last name
    author_name_parts = set(author_name.lower().split())

    # Collect all entity mentions for frequency analysis
    all_entities = []

    for paragraph in content.split('\n\n'):
        doc: Doc = nlp(paragraph)
        for ent in doc.ents:
            # Normalize entity text
            entity_text = ent.text.strip()
            entity_text_lower = entity_text.lower()

            # Filter out irrelevant entities based on stop words, pronouns, and author name
            if (
                entity_text_lower not in STOP_WORDS
                and entity_text_lower not in pronouns
                and entity_text_lower not in author_name_parts
                and len(entity_text_lower) > 1  # Ignore single characters
            ):
                # Collect entities based on their type
                if ent.label_ == "PERSON" or ent.label_ == "NORP":
                    all_entities.append(entity_text)
                elif ent.label_ in ["ORG", "GPE", "LOC", "FAC"]:
                    locations.append(entity_text)
                elif ent.label_ == "EVENT":
                    events.append(entity_text)

        # Manually add entities that are not recognized correctly but are capitalized and used frequently
        for token in doc:
            if (
                token.text[0].isupper()
                and token.text.lower() not in STOP_WORDS
                and token.text.lower() not in pronouns
                and token.text.lower() not in author_name_parts
                and len(token.text) > 1  # Ignore single-character entities
                and token.pos_ == "PROPN"  # Only consider proper nouns
            ):
                all_entities.append(token.text)

    # Count entity occurrences
    entity_counts = Counter(all_entities)

    # Set a lower frequency threshold to capture important entities
    frequency_threshold = 3
    filtered_entities = [entity for entity, count in entity_counts.items() if count >= frequency_threshold]

    # Split entities into characters, groups, and remove from locations if needed
    for entity in filtered_entities:
        entity_doc = nlp(entity)

        # Ensure entity is not the author's name or a stop word
        if entity.lower() in author_name_parts or any(token.text.lower() in STOP_WORDS for token in entity_doc):
            continue

        # Filter out likely irrelevant entities for characters based on POS tagging
        if len(entity_doc) == 1 and entity_doc[0].pos_ not in ["PROPN"]:
            continue
        if entity_doc[0].text.lower() in pronouns:
            continue

        # Classify groups and characters based on context and frequency
        if len(entity_doc) > 1 and entity_doc[0].text.lower() == "the":
            groups.add(entity)  # Classify entities that start with "the" as groups
        elif any(token.pos_ == "PROPN" for token in entity_doc):
            characters.append(entity)

    # Remove incorrectly placed locations
    locations = [loc for loc in locations if loc not in characters]

    # Normalize and deduplicate entities
    def normalize_entities(entities):
        normalized = set()
        for entity in entities:
            # Remove redundant prefixes like "the"
            normalized.add(entity.lower().replace("the ", "").capitalize())
        return list(normalized)

    return {
        "characters": normalize_entities(characters),
        "groups": normalize_entities(groups),
        "locations": normalize_entities(locations),
        "events": normalize_entities(events)
    }



