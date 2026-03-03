#!/bin/bash
set -e
cd /home/dehnert/github/nl2cad/packages/nl2cad-core
PYTHONPATH=src uv run pytest tests/test_file_input_handler.py tests/test_massen_handler.py -v --tb=short 2>&1
