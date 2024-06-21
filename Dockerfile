# Use the official Ubuntu 22.04 base image
FROM ubuntu:22.04

# Set environment variables to prevent Python from writing .pyc files and to buffer stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    python3 \
    python3-pip



RUN pip3 install --upgrade pip

# Set the working directory in the container
WORKDIR /app

# # Clone the dlib repository
# RUN git clone https://github.com/davisking/dlib.git

# # Build the main dlib library
# RUN cd dlib && mkdir build && cd build && cmake .. && cmake --build . && cd ..

# # Build and install the Python extensions for dlib
# RUN cd dlib && python3 setup.py install

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the dependencies from requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the application code to the working directory
COPY . .

# Expose the port that the app runs on
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
