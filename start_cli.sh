#!/bin/bash
cd "$(dirname "$0")"
source ultrastar_env/bin/activate
python ultrastar_generator.py "$@"
