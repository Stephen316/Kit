import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import Probe

if __name__ == '__main__':
    name, member, start, length = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    Probe.show(Probe.members(name)[member], start, 0, length)
