#!/bin/bash
cd /home/kavia/workspace/code-generation/cyclist-connect-325111-325120/bike_connect_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

