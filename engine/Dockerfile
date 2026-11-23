FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts
RUN pip install --no-cache-dir -e ".[test]"
# default: run the test suite; override with e.g.
#   docker run --rm -v $PWD/data:/data img python -m plant_ingest import /data/export.csv --mapping /data/tags.csv --out /data/out
CMD ["pytest", "-q"]
