"""Research preparation: grip moves around the tied face-line crossings of the mixed band cages.

Usage: PreparePartition.py <Round>
Writes Kit TSM variants to LocalOracle/FormDocuments/Partition/tmp/<Round>/ (ignored), the plan to
LocalOracle/FormDocuments/Partition/<Round>/Preparation.json and points tmp/Plan.txt at the round.
Run with /opt/homebrew/bin/python3.14 -I.
"""

import hashlib
import json
import random
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/Partition'
SOURCES = {name: ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil' / (name + '.tsm') for name in ('Mixed56', 'Mixed78')}


def shifted(surface, moves):
    grips = list(surface.Grips)
    for index, (dx, dy, dz) in moves.items():
        grip = grips[index]
        grips[index] = replace(grip, CoordX=grip.CoordX + dx, CoordY=grip.CoordY + dy, CoordZ=grip.CoordZ + dz)
    return replace(surface, Grips=tuple(grips))


def axis_moves(index, steps, axes='xyz'):
    rows = []
    for axis in axes:
        for step in steps:
            move = tuple(step if axis == name else 0.0 for name in 'xyz')
            rows.append(('%s%d_%s%g' % (axis.upper(), index, 'p' if step > 0 else 'm', abs(step)), {index: move}))
    return rows


def round_one():
    rows = [('Base', {})]
    rows += axis_moves(33, (-0.5, -0.25, -0.125, -0.0625, 0.03125, 0.0625, 0.09375, 0.125, 0.1875, 0.25, 0.5), 'x')
    rows += axis_moves(33, (-0.25, -0.125, 0.125, 0.25), 'yz')
    for index in (32, 34, 6, 5, 35, 13, 18):
        rows += axis_moves(index, (-0.25, 0.25))
    return {'Mixed56': rows}


def signed(index, axis, steps):
    return [('%s%d_%s%s' % (axis.upper(), index, 'p' if step > 0 else 'm', repr(abs(step))), {index: tuple(step if axis == name else 0.0 for name in 'xyz')}) for step in steps]


def round_two():
    rows = [('Base', {})]
    rows += signed(33, 'x', (0.1, 0.11, 0.115, 0.12))
    for index, axis, sign in ((33, 'y', 1), (32, 'x', -1), (34, 'x', 1), (34, 'z', -1), (6, 'x', 1), (6, 'y', 1), (6, 'z', -1), (35, 'y', -1), (13, 'z', -1)):
        rows += signed(index, axis, tuple(sign * step for step in (0.0625, 0.125, 0.1875)))
    for index, axes in ((5, 'xyz'), (35, 'xz'), (18, 'xyz'), (33, 'z'), (32, 'yz'), (34, 'y'), (13, 'xy'), (12, 'xyz'), (7, 'xyz')):
        for axis in axes:
            rows += signed(index, axis, (-0.5, 0.5))
    rows += signed(13, 'z', (0.5,))
    return {'Mixed56': rows}


def round_three():
    rows = [('Base', {})]
    rows += signed(33, 'x', (0.121, 0.122, 0.123, 0.124, 0.1245, 0.1249, 0.12499, 0.12501, 0.1251, 0.126, 0.13))
    for index, axis, sign in ((6, 'y', 1), (34, 'z', -1), (35, 'y', -1), (13, 'z', -1)):
        rows += signed(index, axis, tuple(sign * step for step in (0.140625, 0.15625, 0.171875)))
    for index, axis, sign in ((33, 'y', 1), (32, 'x', -1), (34, 'x', 1), (6, 'x', 1), (6, 'z', -1)):
        rows += signed(index, axis, tuple(sign * step for step in (0.203125, 0.21875, 0.234375)))
    return {'Mixed56': rows}


def round_four():
    rows = [('Base', {})]
    rows += signed(33, 'x', (0.124995, 0.124999, 0.1249999, 0.12499999, 0.124999999, 0.125, 0.125000001))
    rows += signed(33, 'y', (0.205, 0.21, 0.215))
    return {'Mixed56': rows}


def transformed(surface, scale, shift):
    grips = tuple(replace(grip, CoordX=grip.CoordX * scale + shift[0], CoordY=grip.CoordY * scale + shift[1], CoordZ=grip.CoordZ * scale + shift[2]) for grip in surface.Grips)
    return replace(surface, Grips=grips)


def round_five():
    rows = []
    for name, scale, shift in (('Shift', 1.0, (0.3, -0.2, 0.1)), ('ShiftFar', 1.0, (5.0, 3.0, -2.0)), ('Double', 2.0, (0.0, 0.0, 0.0))):
        rows.append((name + '_Base', {}, scale, shift))
        for step in (0.12, 0.124995, 0.124999, 0.125, 0.13):
            rows.append((name + '_X33_p' + repr(step), {33: (step * scale, 0.0, 0.0)}, scale, shift))
    return {'Mixed56': rows}


ROUNDS = {'RoundOne': round_one, 'RoundTwo': round_two, 'RoundThree': round_three, 'RoundFour': round_four, 'RoundFive': round_five}


def main():
    name = sys.argv[1]
    folder = TARGET / 'tmp' / name
    folder.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'Grip moves of the mixed band cages around tied face-line crossings', 'round': name, 'python': sys.version.split()[0], 'variants': []}
    for cage, rows in ROUNDS[name]().items():
        data = SOURCES[cage].read_bytes()
        surface = ReadTspline(data)
        for row in rows:
            label, moves = row[0], row[1]
            start = transformed(surface, row[2], row[3]) if len(row) > 2 else surface
            text = EmitTspline(shifted(start, moves))
            path = folder / (cage + '_' + label + '.tsm')
            if not path.exists() or path.read_bytes() != text:
                path.write_bytes(text)
            report['variants'].append({'variant': cage + '_' + label, 'cage': cage, 'source_sha256': hashlib.sha256(data).hexdigest(), 'tsm_file': str(path.relative_to(ROOT)), 'tsm_sha256': hashlib.sha256(text).hexdigest(), 'moves': {str(index): list(move) for index, move in moves.items()}, **({'scale': row[2], 'shift': list(row[3])} if len(row) > 2 else {})})
    (TARGET / name).mkdir(parents=True, exist_ok=True)
    (TARGET / name / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')
    (TARGET / 'tmp' / 'Plan.txt').write_text(name + '\n')
    print(name, len(report['variants']), 'variants')


if __name__ == '__main__':
    main()
