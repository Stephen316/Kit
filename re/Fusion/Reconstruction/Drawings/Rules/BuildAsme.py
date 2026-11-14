"""Graft Kit's ASME sheets into the A3 control (route a) and record the variants.

Each variant is T3Sheet on another paper: L4Core with the layout and overall viewport resized to the paper, Kit's
tables and standard objects, and the control's sheet block filled with Kit's ASME border for that paper. The
control keeps its block name (ISO_A3_SHEET) and its header; only the objects change.

* S1AsmeB: B Landscape (4 x 2 zones).
* S2AsmeD: D Landscape (8 x 4 zones).
* S3AsmeA: A Portrait (2 x 2 zones).

Each variant goes to Variants/<label>.f3z with a row in Variants/PlanAsme.json for BisectRound.py.
Run: python3.14 -I BuildAsme.py --bundle $TMPDIR/KitFusionDrawings/Variants/P0Control.f3z
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / 'Dwg'))
sys.path.insert(0, str(HERE.parent / 'Authoring'))

import BuildBisect  # noqa: E402
import BuildGrafts  # noqa: E402
import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildTransplant as T  # noqa: E402
import BuildVariants  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import SheetSize  # noqa: E402

PLAN = 'PlanAsme.json'
PAPERS = {'S1AsmeB': 'B Landscape', 'S2AsmeD': 'D Landscape', 'S3AsmeA': 'A Portrait'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', required=True)
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing, source = BuildGrafts.bundle_parts(args.bundle)
    q1, _ = BuildBisect.bases(drawing)
    lean_dwg, _ = BuildGrafts.lean(q1)
    plan = {'variants': [], 'transplants': {}}
    for label, paper in PAPERS.items():
        sized, changes = BuildGrafts.ruled(lean_dwg, paper)
        core_dwg, _ = BuildGrafts.core(sized)
        kit = T.kit_dwg(paper)
        dwg, changed, misses = T.transplant(core_dwg, kit, T.TABLE_KINDS + T.STANDARD_KINDS, True)
        border = f'{SheetSize(paper).StandardName}_{SheetSize(paper).FormatName}_SHEET'
        dwg, notes = T.sheet_blocks(dwg, kit, (('ISO_A3_SHEET', border), 'ISO_TITLEBLOCK'))
        plan['transplants'][label] = {'paper': paper, 'layout': changes['layout'], 'changed': changed,
                                      'unmapped_links': misses, 'sheet_blocks': notes}
        data = BuildPruned.emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        plan['variants'].append(BuildPruned2.record(out, label, bundle, data, dwg, {}))
    (out / PLAN).write_text(json.dumps(plan, indent=1, default=str) + '\n')
    print(json.dumps({label: {'paper': row['paper'], 'unmapped': row['unmapped_links'],
                              'blocks': row['sheet_blocks']['blocks']} for label, row in plan['transplants'].items()}))


if __name__ == '__main__':
    main()
