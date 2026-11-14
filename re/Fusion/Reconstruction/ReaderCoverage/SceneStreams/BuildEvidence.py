import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

LAYOUT = {
    'body_lod': [
        'NodeData payload',
        'HasLODs u32: zero or one set bit',
        'when HasLODs != 0 and render geometry exists: DisplayItemType u32',
        'DisplayItemType 0: RenderGeom link (flag, class text, object)',
        'DisplayItemType 6: OgsEnhancedEdge Props u32[4]',
        'DisplayItemType 7: OgsEnhancedFace Props u32[6], EdgeNum u32, Props u32[EdgeNum]',
        'WorldBox f64[6]',
        'UseClosestLOD u8',
    ],
    'enhanced_edge_props': ['stream index', 'byte offset', 'position float count (3 per vertex)', 'normal float count (equals position count)'],
    'enhanced_edge_stream': 'per vertex f32 px py pz nx ny nz at Fusion_mesh_%03d[offset]',
    'enhanced_face_props': ['stream index', 'byte offset', 'position float count', 'normal float count', 'texture float count (2 per vertex, rounded even)', 'index count'],
    'enhanced_face_stream': 'per vertex f32 px py pz nx ny nz u v, then u32 triangle indices, at Fusion_mesh_%03d[offset]',
    'enhanced_face_edges': 'EdgeNum then one u32 per edge: the body-local serialization ordinal of an earlier OgsEnhancedEdge in the same body map',
    'stream_advance': 'the writer adds the written bytes to the offset and moves to the next stream index with offset 0 after a size limit; from earlier binary inspection, not confirmed by a black-box experiment',
    'stream_family': 'Fusion_mesh_NNN holds enhanced mesh data and is distinct from stream_mesh_NNN used by OgsSimpleMesh buffers',
    'object_identity': 'GroupNode and other graphics object ids are %p text: 0x-prefixed lowercase on macOS saves, 16 uppercase hex digits on Windows saves',
    'billboard_v1': 'BillBoardAttribute version 1 carries Style, Anchor, Axis, Compensation; version 2 adds FlipVisibility u32; field names from earlier binary inspection',
}


def lines(name):
    return [json.loads(line) for line in (Path(sys.argv[2]) / name).read_text().splitlines() if line.strip()]


if __name__ == '__main__':
    acceptance = json.loads(Path(sys.argv[1]).read_text())
    evidence = {
        'status': 'captured',
        'layout': LAYOUT,
        'saved_observation': {
            'grouped.f3d first enhanced edge': 'type 6 Props (0, 0, 180, 180), 60 vertices, 1440 bytes',
            'grouped.f3d first enhanced face': 'type 7 Props (0, 2880, 177, 177, 118, 171), EdgeNum 1, edges (0)',
            'grouped.f3d Fusion_mesh_000': 'last face ends at 32464 + 102 * 32 + 300 * 4 = 36928 bytes, the full member',
        },
        'acceptance': acceptance,
        'census': {'baseline': {'pass': 903, 'read': 169}, 'branch': {'pass': 912, 'read': 160}, 'regressions': 0, 'new_differing_members': 0},
        'bundles': {
            're/Fusion/examples/.f3z/example1.f3z': 'Fusion-saved outer archive: deflate members with save timestamps',
            're/Fusion/LocalOracle/Bundles/kit_production_example1.f3z': 'Kit-made outer archive: stored members, 1980 timestamps, reordered; every inner document is byte-identical to the Fusion-saved bundle',
        },
        'remaining': {
            'class_gaps_example1': lines('gaps-example1.jsonl'),
            'class_gaps_example2': lines('gaps-example2.jsonl'),
            'scene_gaps': {
                'example1 member 0': 'FProteinEffectAttribute: EffectAttribute base plus AssetReference text, not modelled',
                'example1 member 1': 'OverrideTransformAttribute: TransformAttribute plus a linked object, not modelled',
                'example1 member 2': 'globals lack GraphicsBlobFeatures and carry F360InstanceNode version 0',
                'example1 member 4': 'Fusion_mesh_000 world references 64048 of 128096 bytes, the tail is unreferenced mesh data',
                'example1 member 7': 'stream_mesh_000 references 35460 of 91620 bytes and Fusion_mesh_000 57680 of 706104 bytes',
            },
        },
    }
    (HERE / 'SceneStreams.json').write_text(json.dumps(evidence, indent=1, default=str) + '\n')
