import json
from flask import Flask, render_template, request
# We need these libraries for the "AI" part (smart search)
import nltk
from nltk.corpus import stopwords
import re

# Initialize the web app
app = Flask(__name__)

# --- AI/NLP Setup ---
# Set up NLTK stopwords (try download, but fall back to a small built-in list)
try:
    nltk.data.find('corpora/stopwords')
except Exception:
    try:
        nltk.download('stopwords', quiet=True)
    except Exception:
        pass
try:
    STOP_WORDS = set(stopwords.words('english'))
except Exception:
    STOP_WORDS = set(["the", "a", "an", "and", "or", "for", "on", "in", "of", "to", "by", "with", "from", "books", "book"])

def load_data():
    """Reads the book list from the JSON file."""
    # Try a couple of possible filenames (with/without .json)
    possible_paths = ['library_data.json', 'library_data']
    for path in possible_paths:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return []
    return []

def smart_search(query, catalog):
    """The function that makes the search intelligent."""
    if not query:
        return []

    raw = str(query).lower()
    # Tokens: words (letters/digits/_), filtered by stop words
    tokens = [w for w in re.findall(r"\w+", raw) if w not in STOP_WORDS]

    # Look for a Year (4 digits) and a possible Classification Code (preserve dots)
    year_match = re.search(r"\b\d{4}\b", raw)
    search_year = int(year_match.group(0)) if year_match else None
    class_match = re.search(r"\b[0-9]{1,4}(?:\.[0-9]+)?\b|\b[A-Za-z]{1,3}\d{1,4}(?:\.[0-9]+)?\b", raw)
    search_class = class_match.group(0) if class_match else None

    results = []
    for book in catalog:
        score = 0
        # Safely extract searchable fields
        title = str(book.get('Title', ''))
        author = str(book.get('Author', ''))
        subjects = book.get('Subject') or []
        if not isinstance(subjects, (list, tuple)):
            subjects = [str(subjects)]
        book_text = f"{title} {author} {' '.join(subjects)}".lower()

        # Keyword Match: Score +1 for every keyword found
        for token in tokens:
            if token in book_text:
                score += 1

        # Precise Match: Score +3 for matching the exact Year
        try:
            if search_year and int(book.get('Year', 0)) == search_year:
                score += 3
        except Exception:
            pass

        # Normalize classification codes for comparison (remove non-alphanum and lowercase)
        def _norm_code(s):
            return re.sub(r'[^a-z0-9]', '', str(s).lower())

        if search_class:
            norm_search = _norm_code(search_class)
            norm_book_class = _norm_code(book.get('Classification', ''))
            if norm_search and (norm_search == norm_book_class or norm_search in norm_book_class or norm_book_class in norm_search):
                score += 3

        # Only include books with a score greater than zero
        if score > 0:
            results.append((score, book))

    # Sort results to show the highest-scoring (most relevant) books first
    results.sort(key=lambda pair: pair[0], reverse=True)
    # Return just the book objects (preserve original dicts)
    return [pair[1] for pair in results]

# --- Web App Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    catalog = load_data()
    search_query = ""
    results = None

    if request.method == 'POST':
        search_query = request.form.get('query', '')
        results = smart_search(search_query, catalog)
    
    # Load the index.html file and show the results
    return render_template('index.html', results=results, search_query=search_query)

if __name__ == '__main__':
    # Gitpod usually needs port 8080 or 5000
    app.run(host='0.0.0.0', port=5001) # Run on port 5001 to avoid conflicts