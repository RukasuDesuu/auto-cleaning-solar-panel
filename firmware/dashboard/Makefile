.PHONY: install run-backend run-frontend test lint format check help

# Variáveis
PYTHONPATH := .

help:
	@echo "Comandos disponíveis:"
	@echo "  make install       - Instala dependências e sincroniza o ambiente com uv"
	@echo "  make run-backend   - Inicia a API FastAPI (Backend)"
	@echo "  make run-frontend  - Inicia o Dashboard Streamlit (Frontend)"
	@echo "  make test          - Executa a suíte de testes unitários"
	@echo "  make lint          - Executa o Ruff para verificar erros de estilo"
	@echo "  make format        - Formata o código automaticamente com Ruff"
	@echo "  make type-check    - Executa o Pyright para checagem de tipos"
	@echo "  make check         - Roda todas as verificações (lint, format, type-check, test)"

install:
	uv sync

run-backend:
	uv run python -m backend.main

run-frontend:
	uv run streamlit run frontend/app.py

test:
	PYTHONPATH=$(PYTHONPATH) uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

type-check:
	uv run pyright .

check: format lint type-check test
