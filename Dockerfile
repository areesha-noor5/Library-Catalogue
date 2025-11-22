FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# system deps
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# copy requirements first to leverage Docker cache
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install -r /app/requirements.txt

# Copy app
COPY . /app

# Pre-download NLTK data used by the app
RUN python -c "import nltk; nltk.download('stopwords')"

# Expose the port (Render/Heroku will provide $PORT at runtime)
EXPOSE 5001

# Default command. Use $PORT if provided by host; fallback to 5001
CMD exec gunicorn app:app --bind 0.0.0.0:${PORT:-5001} --workers 2 --threads 2
