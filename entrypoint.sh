#!/bin/bash
if [[ "$1" == "ui" ]]; then
    shift
    agenteer ui "$@"
elif [[ "$1" == "api" ]]; then
    shift
    uvicorn agenteer.api.app:app --host 0.0.0.0 --port 8000
elif [[ "$1" == "init" ]]; then
    shift
    agenteer init "$@"
elif [[ "$1" == "preload-docs" ]]; then
    shift
    python -m agenteer.cli.main preload-docs "$@"
else
    agenteer "$@"
fi