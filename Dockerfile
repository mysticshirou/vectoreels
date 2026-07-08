FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "vectoreels.web:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
