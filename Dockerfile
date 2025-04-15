FROM python:3.9-slim

WORKDIR /app

# Set pip and setuptools versions
RUN pip install --no-cache-dir --upgrade pip>=23.3.1 setuptools>=70.0.0

# Install app dependencies
RUN pip install --no-cache-dir requests

# Copy application file
COPY main.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]
