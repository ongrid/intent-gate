format:
	poetry run isort app tests
	poetry run black app tests
	poetry run toml-sort pyproject.toml poetry.lock -i -a

format-check:
	poetry run isort --check-only app tests
	poetry run black --check app tests
	poetry run toml-sort --check pyproject.toml poetry.lock -i -a

lint:
	poetry run mypy app tests
	poetry run flake8 app tests
	poetry run pylint app tests

dev: format lint

test:
	poetry run pytest -v --cov=app --cov-report=term-missing

run:
	PYTHONPATH=. poetry run python3 ./app/main.py
