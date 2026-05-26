.PHONY: serve sync test lint login push

TRMNLP := ./bin/trmnlp
UV := uv

serve:
	$(TRMNLP) serve

sync:
	python3 scripts/sync_characters.py

test:
	$(UV) run pytest

lint:
	$(TRMNLP) lint

login:
	$(TRMNLP) login

push:
	$(TRMNLP) push
