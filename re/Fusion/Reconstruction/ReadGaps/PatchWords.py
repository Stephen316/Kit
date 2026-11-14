import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

import convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadPatches as Module
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

FILES = (
    're/Fusion/LocalOracle/FormDocuments/Intervals/Plane4x4/Half.f3d',
    're/Fusion/LocalOracle/FormDocuments/Intervals/Plane4x4/ColumnRow.f3d',
    're/Fusion/LocalOracle/FormDocuments/Intervals/Plane4x4/Single.f3d',
    're/Fusion/LocalOracle/FormDocuments/Intervals/Box/Single.f3d',
)


def main():
    seen = []

    def spy(text):
        seen.append(text)
        raise ValueError('stop')

    Module.ReadPatchRow = spy
    rows = []
    for name in FILES:
        seen.clear()
        try:
            ReadDocument((ROOT / name).read_bytes())
        except ValueError:
            pass
        words = [word for text in seen for word in text.split(' ') if word]
        odd = sorted({word for word in words if not re.fullmatch(r'-?\d+', word)}, key=float)
        shortest = all(repr(float(word)) == word or format(float(word), '.17g') == word for word in odd)
        rows.append({'file': name, 'first_row_words': len(seen[0].split(' ')) if seen else 0, 'non_integer_words': len(odd), 'samples': odd[:8], 'shortest_or_17g': shortest})
    print(json.dumps(rows, indent=1))


if __name__ == '__main__':
    main()
