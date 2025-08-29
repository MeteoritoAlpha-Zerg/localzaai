check:
	poetry run ruff check .
	poetry run mypy . --ignore-missing-imports

format:
	poetry run ruff format . & poetry run ruff check --fix --select I .

test:
	poetry run pytest tests --cov=connectors
