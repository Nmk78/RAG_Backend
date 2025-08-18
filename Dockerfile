# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies
# RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y wget xz-utils \
    && wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    && tar -xf ffmpeg-release-amd64-static.tar.xz \
    && mv ffmpeg-*-amd64-static/ffmpeg /usr/local/bin/ \
    && mv ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ \
    && rm -rf ffmpeg-*-amd64-static ffmpeg-release-amd64-static.tar.xz \
    && apt-get remove -y wget xz-utils && apt-get autoremove -y


# Set the working directory in the container
WORKDIR /app

# COPY wheelhouse ./wheelhouse

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --timeout 200 -r requirements.txt
 

# COPY wheelhouse ./wheelhouse
# RUN pip install --find-links=./wheelhouse -r requirements.txt


# RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install --no-cache-dir --no-index \
#     --find-links=./wheelhouse \
#     -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose the port your app runs on (change if needed)
EXPOSE 8000

# Command to run your app (adjust as needed)
# For FastAPI: uvicorn main:app --host 0.0.0.0 --port 8000
# For Flask: python app.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]