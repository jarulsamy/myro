PHONY: help lint init

.DEFAULT: help
help:
	@echo "make prepare-dev"
	@echo "       prepare development environment, use only once"
	@echo "make test"
	@echo "       run tests"
	@echo "make lint"
	@echo "       run pylint and mypy"

lint:
	python -m pylint myro
	python -m mypy myro

init:
	pip install -r requirements.txt
