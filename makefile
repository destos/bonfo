sources = bonfo
prun = poetry run

.PHONY: test format lint unittest coverage pre-commit clean docs
test: format lint unittest

format:
	${prun} isort $(sources) tests
	${prun} black $(sources) tests
	# ${prun} autoflake8 -r -i --ignore-init-module-imports $(sources) tests

lint:
	${prun} flake8 $(sources) tests
	${prun} mypy $(sources) tests

unittest:
	${prun} pytest

coverage:
	${prun} pytest --cov=$(sources) --cov-branch --cov-report=term-missing tests

pre-commit:
	pre-commit run --all-files

clean:
	rm -rf .mypy_cache .pytest_cache
	rm -rf *.egg-info
	rm -rf .tox dist site
	rm -rf coverage.xml .coverage

docs:
	${prun} mkdocs build

docs-test:
	${prun} mkdocs serve
