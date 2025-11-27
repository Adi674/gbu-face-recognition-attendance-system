# 1. Use the official lightweight Python 3.12 image
FROM python:3.12-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install SYSTEM dependencies (The "Linux" graphics drivers)
# This fixes the "libGL.so.1" error automatically on the server
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements and install Python dependencies
# We copy this first to leverage Docker caching (speeds up re-builds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code
COPY . .

# 6. Expose the port that FastAPI runs on
EXPOSE 8000

# 7. The command to start your application
CMD ["python", "run.py"]