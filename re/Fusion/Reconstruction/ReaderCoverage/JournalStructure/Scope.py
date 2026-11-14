import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CAUSES = (
    'Missing required Fusion topology reference',
    'Fusion journal active bodies disagree with its root count',
    'Unsupported Fusion history stream variant',
    'Oversized Fusion bulletin board',
    'Oversized Fusion ASM record',
    'Fusion geometry bodies disagree with its root count',
    'Fusion round carriers require positive finite radii',
    'Unsupported Fusion nonmanifold edge-use count',
)


def scope(report):
    rows = json.loads(Path(report).read_text())['rows']
    return {row['file']: cause for row in rows for cause in CAUSES if cause in row.get('error', '')}


if __name__ == '__main__':
    for name, cause in sorted(scope(sys.argv[1]).items(), key=lambda item: (item[1], item[0])):
        print(cause[:40], '|', name)
