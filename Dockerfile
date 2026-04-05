# Use a lightweight Python base image
FROM python:3.11-slim

# Set environment variables for non-interactive installs and timezone
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Montreal

# Install cron and tzdata (to handle timezone correctly)
RUN apt-get update && apt-get install -y cron tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and configuration
COPY gaz_saver.py .
COPY stations.yaml .
COPY cron.txt /etc/cron.d/gaz-cron

# Give execution rights to the cron job and the script
RUN chmod 0644 /etc/cron.d/gaz-cron && \
    chmod +x /app/gaz_saver.py

# Apply the cron job
RUN crontab /etc/cron.d/gaz-cron

# Create the log file to be able to run tail (if needed, but we redirect to stdout)
RUN touch /var/log/cron.log

# Run cron in the foreground
CMD ["cron", "-f"]
