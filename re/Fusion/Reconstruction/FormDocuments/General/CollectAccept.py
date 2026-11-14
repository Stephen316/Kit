"""Research step after AcceptGeneral: keep Fusion's own conversion of each accepted cage.

Usage:
  CollectAccept.py copy   copies tmp/Oracle<Case>Converted.f3d of each accepted case to Accept/Fusion/<Case>.f3d
  CollectAccept.py cases  writes tests/.../Form/GeneralCases.py from the kept saves and the Kit TSM files

Run ScrubSaved.py over the copied saves between the two steps, so the digests are the scrubbed ones.
The saves are Fusion's conversion before any edit. GeneralAcceptTests compares ConvertForm of each TSM
with the body read from the save.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
ACCEPT = ROOT / 're/Fusion/LocalOracle/FormDocuments/General/Accept'
KEPT = ACCEPT / 'Fusion'
CASES = ROOT / 'tests/convert/formats/FusionCodec/Documents/Form/GeneralCases.py'


def accepted():
    report = json.loads((ACCEPT / 'GeneralAcceptance.json').read_text())
    return [(case['case'], case['group']) for case in report['cases'] if case.get('status') == 'accepted']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy():
    KEPT.mkdir(exist_ok=True)
    for name, _ in accepted():
        shutil.copyfile(ACCEPT / 'tmp' / ('Oracle' + name + 'Converted.f3d'), KEPT / (name + '.f3d'))
        print(name)


def cases():
    lines = ['KGeneralCases: tuple[tuple[str, str, str, str, str], ...] = (']
    for name, group in accepted():
        tsm, save = ACCEPT / (name + '.tsm'), KEPT / (name + '.f3d')
        lines.append('    (')
        lines.append(f'        "{name}",')
        lines.append(f'        "{tsm.relative_to(ROOT)}",')
        lines.append(f'        "{digest(tsm)}",')
        lines.append(f'        "{save.relative_to(ROOT)}",')
        lines.append(f'        "{digest(save)}",')
        lines.append('    ),')
    lines.append(')')
    CASES.write_text('\n'.join(lines) + '\n')
    print(len(lines))


if __name__ == '__main__':
    {'copy': copy, 'cases': cases}[sys.argv[1]]()
