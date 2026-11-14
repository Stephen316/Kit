import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProbeFailures import entities
from Shapes import corpus


def survey(kind, slots, family=None):
    found = collections.Counter()
    for path, name, payload in corpus():
        try:
            table = entities(payload, name.endswith('.smbh'))
        except Exception:
            continue
        for record in table:
            if record.Name != kind:
                continue
            if family is not None and (len(record.Tokens) <= 5 or record.Tokens[5] != (7, family)):
                continue
            found[tuple(record.Tokens[slot] if slot < len(record.Tokens) else None for slot in slots)] += 1
    return found


if __name__ == '__main__':
    kind = sys.argv[1]
    slots = [int(value) for value in sys.argv[2].split(',')]
    family = sys.argv[3] if len(sys.argv) > 3 else None
    for key, count in survey(kind, slots, family).most_common(40):
        print(count, key)
