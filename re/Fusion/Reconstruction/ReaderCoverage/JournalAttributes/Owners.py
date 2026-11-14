import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProbeFailures import entities
from Shapes import corpus


def survey(kinds, family=None):
    found = collections.defaultdict(collections.Counter)
    for path, name, payload in corpus():
        try:
            table = entities(payload, name.endswith('.smbh'))
        except Exception:
            continue
        for record in table:
            if record.Name not in kinds:
                continue
            if family is not None and (len(record.Tokens) <= 5 or record.Tokens[5] != (7, family)):
                continue
            for slot, (tag, value) in enumerate(record.Tokens):
                if tag == 12:
                    target = 'null' if value == -1 else (table[value].Name if 0 <= value < len(table) else 'out-of-range')
                    found[(record.Name, slot)][target] += 1
    return found


if __name__ == '__main__':
    family = sys.argv[2] if len(sys.argv) > 2 else None
    for key, counter in sorted(survey(set(sys.argv[1].split(',')), family).items()):
        print(key, dict(counter))
