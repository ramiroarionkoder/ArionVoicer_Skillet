FROM python:3.13

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PIP_NO_BINARY=:all: \
    UV_PIP_NO_CACHE_DIR=1


WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir uv

RUN uv lock

RUN uv sync

EXPOSE 8501

CMD ["streamlit", "run", "main_skilletz.py", "--server.port=8501", "--server.address=0.0.0.0"]
