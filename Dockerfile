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
  CMD curl -s -w ", http_code:%{http_code}\n" http://localhost:8080/health || exit 1
CMD poetry run python /app/app/main.py
