# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# This is AWS Content subject to the terms of the Customer Agreement
# ----------------------------------------------------------------------
# File content:
#       Docker image of the streamlit container
FROM --platform=linux/amd64 python:3.9-slim
WORKDIR /app

RUN apt-get update -y && apt-get install -y --no-install-recommends\
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app
COPY .streamlit/ /app/.streamlit/

RUN pip3 --no-cache-dir install -U pip
RUN pip3 --no-cache-dir install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --only main

COPY src/ /app/src

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "src/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
