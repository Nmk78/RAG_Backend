# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Expose the port your app runs on (change if needed)
EXPOSE 8000

# Command to run your app (adjust as needed)
# For FastAPI: uvicorn main:app --host 0.0.0.0 --port 8000
# For Flask: python app.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]