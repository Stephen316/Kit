#!/bin/sh
set -u
cd "$(dirname "$0")/../../../.."
FILES=$(git status --porcelain -uall -- src tests | awk '{print $NF}' | grep '\.py$')
[ -n "$FILES" ] || { echo "no changed Python files"; exit 0; }
STATUS=0
TEMP=$(mktemp -d)
uv run --no-sync ruff check $FILES > /dev/null 2>&1 || { echo "ruff failed"; uv run --no-sync ruff check $FILES | tail -20; STATUS=1; }
uv run --no-sync black --check $FILES > /dev/null 2>&1 || { echo "black failed"; uv run --no-sync black --check $FILES 2>&1 | tail -5; STATUS=1; }
uv run --no-sync mypy $FILES > $TEMP/mypy.txt 2>&1 || { echo "mypy failed"; tail -20 $TEMP/mypy.txt; STATUS=1; }
uv run --no-sync pyright $FILES > $TEMP/pyright.txt 2>&1 || { echo "pyright failed"; tail -20 $TEMP/pyright.txt; STATUS=1; }
{ git ls-files -z -- '*.py'; git ls-files -z --others --exclude-standard -- 'src/*.py' 'tests/*.py'; } | xargs -0 uv run --no-sync python -m tools.steering.SteeringCompliance --baseline-file tools/steering/SteeringBaseline.txt > $TEMP/steer.txt 2>&1 || { echo "steering failed"; tail -20 $TEMP/steer.txt; STATUS=1; }
echo "static checks exit $STATUS"
exit $STATUS
