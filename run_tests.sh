#!/bin/bash
cd /home/dehnert/github/nl2cad
uv run pytest packages/nl2cad-core/tests/test_file_input_handler.py packages/nl2cad-core/tests/test_massen_handler.py -v --tb=short 2>&1
