# Use an official Python runtime as a parent image
#FROM python:3.9-slim
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# # Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install typecheck dependencies
RUN pip install mypy pandas-stubs types-Pygments types-colorama types-decorator types-jsonschema types-openpyxl 

# Copy typecheck configuration
COPY mypy.ini mypy.ini

# Copy the rest of the application code
COPY app.py app.py

#RUN pip freeze > requirements.txt

# Typecheck
RUN mypy --config-file mypy.ini app.py

# Specify the command to run your application
CMD ["python", "app.py"]
