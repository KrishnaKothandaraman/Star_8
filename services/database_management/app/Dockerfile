# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9.16-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /
WORKDIR $APP_HOME
COPY . ./
RUN pwd
RUN ls -lrt
RUN ls services/database_management
ENV PYTHONPATH=$APP_HOME

# Install production dependencies.
RUN pip install --no-cache-dir -r services/database_management/requirements.txt

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.


CMD exec gunicorn --bind :$PORT --workers 1 --threads 2 --timeout 0 services.database_management.app.app:app