"""Build DWG removal variants of the A1 control for native requirement experiments.

Each variant reads the A1 DWG into the typed model, removes one group of objects or sections,
re-plans the pages with fresh compression and packages the result like BuildVariants.py.
"""

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / 'Dwg'))

import BuildVariants  # noqa: E402
from PruneDwg import Graph, field, prune, target  # noqa: E402

from convert.formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EmitDwgFile, EncodeContents  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.Image.PlanImages import ReplanFile  # noqa: E402
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgFile import ReadDwgFile  # noqa: E402

ACM_PREFIXES = ('ACAMG', 'ACM', 'AMDT', 'AMG', 'AMIMASTER', 'ACGREF', 'ACIM', 'Acm')
OPTIONAL_SECTIONS = ('AcDb:Preview', 'AcDb:RevHistory', 'AcDb:AppInfoHistory', 'AcDb:AcDsPrototype_1b')


def block_name(graph, handle):
    return field(graph.objects[handle].ClassData, 'EntryName', '') if graph.names.get(handle) == 'BLOCK_HEADER' else ''


def curves_in(graph, prefix, kinds):
    rows = set()
    for handle, obj in graph.objects.items():
        if graph.names[handle] == 'BLOCK_HEADER' and block_name(graph, handle).startswith(prefix):
            for ref in field(obj.ClassData, 'Owned', ()):
                child = target(handle, ref)
                if graph.names.get(child) in kinds:
                    rows.add(child)
    return rows


def acm_objects(graph):
    return {handle for handle, name in graph.names.items() if name.startswith(ACM_PREFIXES)}


def unused_blocks(graph):
    rows = set()
    for handle, name in graph.names.items():
        if name != 'BLOCK_HEADER':
            continue
        inside = graph.closure({handle})
        callers = {other for other in graph.incoming.get(handle, ()) if other not in inside and graph.names.get(other) != 'BLOCK_CONTROL'}
        if not callers:
            rows.add(handle)
    return rows


def without_sections(dwg, names):
    infos = tuple(info for info in dwg.SectionInfos if info.SectionName not in names)
    raw = tuple((name, value) for name, value in dwg.RawSections if name not in names)
    typed = tuple((name, value) for name, value in dwg.SectionVars if name not in names)
    return replace(dwg, SectionInfos=infos, RawSections=raw, SectionVars=typed)


def emit_fresh(dwg):
    replanned = ReplanFile(dwg, EncodeContents(dwg))
    data = EmitDwgFile(replanned)
    again = ReadDwgFile(data)
    if EmitDwgFile(again) != data or len(again.DwgObjects) != len(dwg.DwgObjects):
        raise ValueError('variant does not read back')
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--with-dimension', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    out = BuildVariants.OUT
    out.mkdir(parents=True, exist_ok=True)
    drawing = Path(args.with_dimension).read_bytes()
    source = Path(args.source).read_bytes()
    base = ReadDwgFile(BuildVariants.database(drawing))
    graph = Graph(base)
    kills = {
        'D2NoViewCurves': curves_in(graph, '*S', {'LINE', 'CIRCLE', 'ARC'}),
        'D3NoAnnotationBlocks': curves_in(graph, '*D', {'LINE', 'SOLID', 'MTEXT', 'POINT'}) | curves_in(graph, '*U', {'LINE', 'CIRCLE', 'ARC'}),
        'D4NoAcm': acm_objects(graph),
        'D5NoUnusedBlocks': unused_blocks(graph),
    }
    kills['D6Minimal'] = set().union(*kills.values())
    plan = {'base_objects': len(base.DwgObjects), 'variants': []}
    rows = [('D1FreshLayout', base, {}, {})]
    for label, kill in kills.items():
        pruned, removed, dangling = prune(base, kill)
        if label == 'D6Minimal':
            pruned = without_sections(pruned, OPTIONAL_SECTIONS)
        rows.append((label, pruned, removed, dangling))
    rows.append(('D7NoOptionalSections', without_sections(base, OPTIONAL_SECTIONS), {}, {}))
    for label, dwg, removed, dangling in rows:
        data = emit_fresh(dwg)
        bundle = BuildVariants.opaque_bundle(BuildVariants.without_database(drawing, data), source, label)
        path = out / (label + '.f3z')
        path.write_bytes(bundle)
        plan['variants'].append({
            'label': label, 'file': path.name, 'bytes': len(bundle), 'sha256': hashlib.sha256(bundle).hexdigest(),
            'dwg_bytes': len(data), 'dwg_sha256': hashlib.sha256(data).hexdigest(), 'objects': len(dwg.DwgObjects),
            'sections': [info.SectionName for info in dwg.SectionInfos if info.SectionName],
            'removed': dict(sorted(removed.items())), 'nulled_references': dict(sorted(dangling.items())),
        })
    (out / 'Plan.json').write_text(json.dumps(plan, indent=1) + '\n')
    print(json.dumps(plan, indent=1))


if __name__ == '__main__':
    main()
