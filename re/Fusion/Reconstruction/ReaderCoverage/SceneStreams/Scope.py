import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/ReaderCoverage'))

import Census

FILES = (
    're/Fusion/examples/.f3d/example2.f3d',
    're/Fusion/Study/timeline-5867579925b5/grouped.f3d',
    're/Fusion/Study/timeline-5867579925b5/reordered_b.f3d',
    're/Fusion/Study/timeline-5867579925b5/rolled_back.f3d',
    're/Fusion/Study/timeline-5867579925b5/suppressed_b.f3d',
    're/Fusion/Study/timeline-72406b67a839/reordered_b.f3d',
    're/Fusion/Study/timeline-72406b67a839/suppressed_b.f3d',
    're/Fusion/Study/timeline-expanded-2396e32f2574/expanded.f3d',
    're/Fusion/Study/timeline-fee448f6a592/suppressed_b.f3d',
    're/Fusion/examples/.f3z/example1.f3z',
    're/Fusion/LocalOracle/Bundles/kit_production_example1.f3z',
)


def short(row):
    keep = {key: row[key] for key in ('status', 'error', 'where', 'model_equal', 'differing', 'bundle_equal') if key in row}
    if 'children' in row:
        keep['children'] = [short(child) | {'member': child['member'][:8]} for child in row['children']]
    return keep


if __name__ == '__main__':
    names = sys.argv[1:] or FILES
    for name in names:
        row = Census.verify(ROOT / name)
        print(name, json.dumps(short(row), indent=1))
