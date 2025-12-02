# Use the official Playwright Python image (includes Chromium)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set the working directory
WORKDIR /app

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Just to be safe, though base image usually has them)
RUN playwright install chromium

# Copy the script
COPY main.py .

# Define the command to run the application
CMD ["python", "main.py"]