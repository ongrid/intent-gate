FROM python:3.13.5-bookworm
WORKDIR /app
RUN curl -sSL https://install.python-poetry.org | python3 -
COPY . ./
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"
RUN poetry install --no-dev
EXPOSE 8080
CMD poetry run python /app/app/main.py
