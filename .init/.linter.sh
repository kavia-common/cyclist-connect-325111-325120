#!/bin/bash
set -euo pipefail

cd /home/kavia/workspace/code-generation/cyclist-connect-325111-325120/bike_connect_backend

# CI robustness:
# - Do not assume a local venv exists.
# - Run flake8 via python -m so it works as long as flake8 is installed in the environment.
python -m flake8 .
