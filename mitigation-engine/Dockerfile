# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This is done in a separate step to leverage Docker's layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make port 5001 available to the host
EXPOSE 5001

# Command to run the application
# We use flask run with --host=0.0.0.0 to make it accessible
# outside the container's network interface.
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
