# Use official Python 3.12 image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (git, curl, build tools if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv

# Copy only dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (respect lockfile)
RUN uv sync --frozen --no-dev

# Copy the rest of the project
COPY . .

# Download required NLTK resources at build time
# so the container doesn't need internet on first run
RUN uv run python -c "import nltk; [nltk.download(p, quiet=True) for p in ['punkt','stopwords','wordnet','punkt_tab']]"

# Expose Streamlit default port
EXPOSE 8501

# Default command to run the Streamlit app
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]