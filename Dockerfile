# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8501

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port (Render will override this, but good for documentation)
EXPOSE 8501

# Entrypoint: Run Streamlit (which auto-launches the API backend)
# Using sh -c to ensure the $PORT environment variable is expanded
CMD ["sh", "-c", "streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0"]
