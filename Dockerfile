FROM python:3.13.5-bookworm
WORKDIR /app
RUN curl -sSL https://install.python-poetry.org | python3 -
COPY . ./
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"
RUN poetry install --without=dev
EXPOSE 8080
HEALTHCHECK --interval=1m --timeout=10s \
  CMD poetry run python3 -m app.metrics.healthcheck_client http://localhost:8080/health
CMD poetry run python3 /app/app/main.py
