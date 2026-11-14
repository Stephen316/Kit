"""Build H1NoAcm: the D5 base without its AutoCAD Mechanical objects.

D5NoUnusedBlocks is the smallest pruned control that Fusion has opened with all views and the
dimension. D4NoAcm removed the same mechanical objects from the full control. H1NoAcm combines both
removals, because Kit's typed standard cannot carry the untyped mechanical objects. The variant is
refused when any handle, typed or numeric, names an absent object.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'Dwg'))

import BuildPruned  # noqa: E402
import BuildPruned2  # noqa: E402
import BuildPruned4  # noqa: E402
import BuildVariants  # noqa: E402
from PruneDwg import Graph, prune  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-dimension', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    out = BuildVariants.OUT
    drawing = Path(args.with_dimension).read_bytes()
    source = Path(args.source).read_bytes()
    base = ReadDwgFile(BuildVariants.database(drawing))
    base, _, _ = prune(base, BuildPruned.unused_blocks(Graph(base)))
    graph = Graph(base)
    kill = BuildPruned.acm_objects(graph)
    dead = graph.closure(kill)
    pruned, removed, _ = prune(base, kill | BuildPruned4.recompose_records(graph, dead))
    left = BuildPruned4.dangling(pruned)
    if left:
        raise ValueError(f'H1NoAcm still names absent objects: {left[:5]}')
    data = BuildPruned.emit_fresh(pruned)
    bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, 'H1NoAcm')
    plan = {'base_objects': len(base.DwgObjects), 'variants': [BuildPruned2.record(out, 'H1NoAcm', bundle, data, pruned, dict(removed))]}
    (out / 'Plan5.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()
