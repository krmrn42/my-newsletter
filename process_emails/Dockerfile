FROM python:3.12-slim

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
WORKDIR /app
COPY . ./

RUN pip install --upgrade pip

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for the function name
ENV FUNCTION_TARGET=process_emails

# Run the web service on container startup using functions-framework
CMD functions-framework --target=${FUNCTION_TARGET} --port=${PORT:-8080} 