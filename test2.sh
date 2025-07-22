#!/bin/bash
cd integrated_platform
poetry lock --no-cache
poetry install
poetry run ruff check . --select F,E7,E902,F821,F823,F401 --ignore D100,D101,D102,D103,D104,D105,D106,D107 || exit 1
poetry run deptry . || exit 1
poetry run pytest tests/ignition_test.py || exit 1
poetry run pytest -m smoke || exit 1
