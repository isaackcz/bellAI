# PepperAI - Bell Pepper Detection & Quality Assessment System
# Multi-stage build for optimized production image

# Stage 1: Base image with Python and system dependencies
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libopenblas-dev \
    gfortran \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base AS dependencies

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Production image
FROM dependencies AS production

# Create non-root user for security
RUN groupadd -r pepperai && useradd -r -g pepperai pepperai

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=pepperai:pepperai app.py .
COPY --chown=pepperai:pepperai models.py .
COPY --chown=pepperai:pepperai validation_pipeline.py .
COPY --chown=pepperai:pepperai python_modules/ ./python_modules/
COPY --chown=pepperai:pepperai disease_detection/ ./disease_detection/
COPY --chown=pepperai:pepperai static/ ./static/
COPY --chown=pepperai:pepperai templates/ ./templates/
COPY --chown=pepperai:pepperai routes/ ./routes/

# Copy model files
COPY --chown=pepperai:pepperai models/ ./models/
COPY --chown=pepperai:pepperai models_extra/ ./models_extra/

# Create necessary directories with proper permissions
RUN mkdir -p uploads results instance && \
    chown -R pepperai:pepperai uploads results instance

# Switch to non-root user
USER pepperai

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "app.py"]
