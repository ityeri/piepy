FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY . ./
RUN uv build && uv pip install --system dist/*.whl

CMD ["python", "-m", "piepy"]
