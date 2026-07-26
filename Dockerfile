FROM python:3.11-slim

WORKDIR /app

RUN apt update
RUN apt install -y ffmpeg
RUN apt install -y git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir poetry

COPY . ./
RUN poetry build
RUN pip install --no-cache-dir dist/*.whl

CMD ["python", "-m", "piepy"]