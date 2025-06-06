format:
	poetry run isort app tests
	poetry run black app tests
	poetry run toml-sort pyproject.toml poetry.lock -i -a

lint:
	poetry run mypy app tests
	poetry run flake8 app tests
	poetry run pylint app tests

dev: format lint

test:
	poetry run pytest -v --cov=app --cov-report=term-missing

run:
	PYTHONPATH=. poetry run python3 ./app/main.py
