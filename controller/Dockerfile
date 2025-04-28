FROM python:3.10-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    build-essential \
    wine64 \
    wine32 \
    mingw-w64 \
    zip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install flask pyinstaller

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Expose port
EXPOSE 5000

# Run Controller app
CMD ["python", "app.py"]
