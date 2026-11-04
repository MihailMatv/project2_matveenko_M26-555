.PHONY: install run lint format build check

install:
	uv sync

run:
	uv run project

lint:
	uv run ruff check .

format:
	uv run ruff format .

build:
	uv build

check: lint build
	uvx twine check dist/*
