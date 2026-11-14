"""Explain every SheetDefaults.json field and check it against Fusion-made drawings.

Each row gets a basis and a note. The basis says why Kit may write the value:
spec (a public DWG specification defines it), empty (the field's none, off or null
state), identity (a unit scale, the world normal or the origin), version (a record or
class version), vocabulary (a name in Fusion's drawing schema), template (a setting of
the ISO drawing template), choice (a neutral value Kit picks), tested (Fusion was asked
in object-level grafts; the note lists the values it opened, reported as damaged, or
stopped answering on), or observed (no meaning is known; the value is only the same in
every instance Kit has read).

The evidence columns count the instances of each class in the given Fusion drawings
and how many hold the default. Only counts and SHA-256 digests are written, never
values or names from the drawings.
"""

import argparse
import collections
import functools
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[4] / 'src'))

import GenerateDefaults  # noqa: E402

ROOT = HERE.parents[4]
DEFAULTS = ROOT / 'src/convert/formats/Fusion/DrawingCodec/Dwg/Author/Standard/SheetDefaults.json'
GRAFTS = HERE.parent / 'Rules' / 'GraftRoundUnknowns.json'
DIMENSIONS = ('DIMENSION_ALIGNED', 'DIMENSION_DIAMETER', 'DIMENSION_LINEAR', 'DIMENSION_RADIUS')
OUTCOMES = (('opened', 'Fusion opens the drawing with'), ('damaged', 'Fusion reports the drawing as damaged with'), ('stalled', 'Fusion stops answering while it opens the drawing with'))
ODA = 'ODA Open Design Specification for .dwg files'
LIBRE = 'LibreDWG'

ENTITY = {
    'HasGraphics': ('spec', f'{ODA} 20.4.1 graphic present flag; 1 only where an empty graphics header follows'),
    'GraphicSize': ('spec', f'{ODA} 20.4.1 graphics size; 8 is the bare proxy graphics header'),
    'Graphics': ('spec', f'{ODA} 29: an 8-byte header whose first word equals the length and whose second is 0; no primitive chunk follows'),
    'EntityMode': ('spec', f'{ODA} 20.4.1 entmode: 0 owner handle follows, 1 paper space'),
    'ReactorCount': ('spec', 'Number of reactor handles; it equals the length of Reactors'),
    'Reactors': ('spec', 'Reactor handles; the owning dictionary or none'),
    'NoXdic': ('spec', f'{ODA} 20.4.1 no extension dictionary flag'),
    'HasDsData': ('spec', f'{LIBRE} common_entity_data.spec has_ds_data: 0 means no data store record'),
    'ColorIndex': ('spec', f'{LIBRE} ENC colour: 256 ByLayer; 8192 is flag 0x2000 (transparency follows) with index 0, ByBlock'),
    'Transparency': ('spec', f'{LIBRE} ENC transparency: high byte 1 is ByBlock'),
    'LtypeScale': ('identity', 'Linetype scale 1'),
    'LtypeFlags': ('spec', f'{LIBRE} ltype_flags: 0 ByLayer, 3 linetype handle follows'),
    'MaterialFlags': ('spec', f'{LIBRE} material_flags: 0 ByLayer'),
    'PlotFlags': ('spec', f'{LIBRE} plotstyle_flags: 0 ByLayer'),
    'ShadowFlags': ('spec', f'{LIBRE} shadow_flags: 0 casts and receives shadows'),
    'HasFullStyle': ('empty', 'No full visual style handle'),
    'HasFaceStyle': ('empty', 'No face visual style handle'),
    'HasEdgeStyle': ('empty', 'No edge visual style handle'),
    'Invisible': ('spec', f'{LIBRE} invisible bit 0: 0 visible'),
    'LineWeight': ('spec', f'{LIBRE} linewt: 29 ByLayer'),
    'Layer': ('vocabulary', 'A layer of the Fusion drawing template: 0, Defpoints, FD_Dimensions or TITLEBLOCK'),
    'Ltype': ('vocabulary', 'The view border linetype of the Fusion drawing template'),
    'Owner': ('vocabulary', 'The owning control or named dictionary entry'),
    'Thickness': ('empty', 'No extrusion thickness'),
    'Extrusion': ('identity', 'World Z normal'),
    'Elevation': ('identity', 'Zero elevation'),
}

NAMED = {
    'AppId': ('empty', 'Null application id handle'),
    'AttachPoint': ('spec', f'{LIBRE} MTEXT ignore_attachment, a copy of the attachment'),
    'Attachment': ('choice', 'Middle centre text attachment (5), a neutral Kit choice'),
    'AttribFlags': ('empty', 'No attribute flags set'),
    'AttribType': ('spec', f'{LIBRE} mtext_type 1, single line'),
    'AttribVersion': ('version', 'Attribute record version 0'),
    'AxisAngle': ('identity', 'Zero point display angle'),
    'BackClip': ('empty', 'No back clip distance'),
    'BackFlags': ('empty', 'MTEXT background fill off'),
    'Background': ('empty', 'Null background handle'),
    'BasePoint': ('identity', 'Block base point at the origin'),
    'BaseUcs': ('empty', 'Null base UCS handle'),
    'BlockScaling': ('spec', 'DXF 281 block scaling 0, any scale'),
    'BottomMargin': ('choice', 'Zero plot margin, a neutral Kit choice'),
    'Brightness': ('empty', 'Zero viewport brightness offset'),
    'CircleZoom': ('template', 'Circle zoom percent 20000 of the Fusion template viewport'),
    'Cloning': ('spec', 'DXF 281 duplicate record cloning 1, keep existing'),
    'ColumnType': ('empty', 'No MTEXT columns'),
    'Contrast': ('empty', 'Zero viewport contrast offset'),
    'DefaultFlag': ('spec', f'{LIBRE} MTEXT default_flag; 1 is its default'),
    'DefaultLights': ('spec', 'DXF 292 use default lights'),
    'Description': ('empty', 'No block description'),
    'DimFlags': ('observed', f'Dimension flags 11. {ODA} explains bits 0 and 1: text at its default place, block for this dimension only. Bit 3 is set in every Fusion dimension and is not documented'),
    'DimVersion': ('version', 'Dimension record version 0'),
    'DrawDirection': ('spec', 'DXF 72 drawing direction 1, left to right'),
    'DrawingUnits': ('identity', 'One drawing unit per paper unit'),
    'Explodable': ('spec', 'DXF 280 explodability 1'),
    'ExtRotation': ('identity', 'Zero extension line rotation'),
    'FieldLength': ('empty', 'No attribute field length'),
    'FlagBit': ('spec', f'{ODA} table entry 64-flag, bit 64 of group 70: the entry is referenced'),
    'FlipFirst': ('empty', 'First arrow not flipped'),
    'FlipSecond': ('empty', 'Second arrow not flipped'),
    'FrontClip': ('empty', 'No front clip distance'),
    'GridMajor': ('template', 'Major grid line every 5 minor lines'),
    'GridSpacing': ('template', 'ISO template grid spacing of 10 mm'),
    'HasAttribs': ('empty', 'No attributes'),
    'HorizDirection': ('identity', 'Zero horizontal direction'),
    'ImageOrigin': ('identity', 'Image origin at zero'),
    'InsertBase': ('identity', 'Insertion base at the origin'),
    'InsertRotation': ('identity', 'Zero insertion rotation'),
    'InsertScale': ('identity', 'Unit insertion scale'),
    'InsertUnits': ('empty', 'Unitless block insertion'),
    'IsOverlay': ('empty', 'Not an overlay'),
    'IsXref': ('empty', 'Not an external reference'),
    'LayoutFlags': ('spec', 'DXF 70 layout flag 1, PSLTSCALE'),
    'LeftMargin': ('choice', 'Zero plot margin, a neutral Kit choice'),
    'LensLength': ('template', 'Default 50 mm viewport lens length'),
    'LightingType': ('spec', 'DXF 282 default lighting type 1, two distant lights'),
    'Loaded': ('empty', 'No unloaded external reference'),
    'LockPosition': ('spec', f'{LIBRE} lock_position_flag; Fusion title block fields are locked'),
    'NamedUcs': ('empty', 'Null named UCS handle'),
    'NotAnnotative': ('spec', f'{LIBRE} MTEXT is_not_annotative; the context data follows'),
    'OrthoType': ('empty', 'UCS is not orthographic'),
    'PageName': ('empty', 'No page setup name'),
    'PaperUnits': ('spec', 'DXF 72 plot paper units 1, millimetres'),
    'PlotOrigin': ('identity', 'Plot origin at zero'),
    'PlotRotation': ('identity', 'No plot rotation'),
    'PlotType': ('spec', 'DXF 74 plot type 5, layout information'),
    'PlotView': ('empty', 'Null plot view handle'),
    'PointTwelve': ('identity', 'Unused dimension point at zero'),
    'Preview': ('choice', 'No block preview image, a neutral Kit choice'),
    'PreviewSize': ('choice', 'No block preview image, a neutral Kit choice'),
    'PrinterName': ('choice', 'No plot device, a neutral Kit choice'),
    'RealUnits': ('identity', 'One real-world unit per paper unit'),
    'RenderMode': ('spec', 'DXF 281 render mode 0, 2D optimised'),
    'RightMargin': ('choice', 'Zero plot margin, a neutral Kit choice'),
    'Rotation': ('identity', 'Zero rotation'),
    'ScaleFactor': ('identity', 'Plot scale factor 1'),
    'ScaleFlags': ('spec', f'{ODA} INSERT data flags 3: scale is 1, 1, 1'),
    'ScaleType': ('spec', 'DXF 75 standard scale type 16, 1:1'),
    'Schema': ('version', 'Variable dictionary schema 0'),
    'ShadeDpi': ('template', 'Shade plot resolution 300 dpi'),
    'ShadeMode': ('spec', 'DXF 76 shade plot mode 0, as displayed'),
    'ShadePlot': ('spec', 'Viewport shade plot 0, as displayed'),
    'ShadePlotId': ('empty', 'Null shade plot handle'),
    'ShadeQuality': ('spec', 'DXF 77 shade plot resolution 2, normal'),
    'Shadow': ('empty', 'Null shadow handle'),
    'SnapAngle': ('identity', 'Zero snap angle'),
    'SnapBase': ('identity', 'Snap base at zero'),
    'SnapSpacing': ('template', 'ISO template snap spacing of 10 mm'),
    'SpacingFactor': ('identity', 'Line spacing factor 1'),
    'SpacingStyle': ('spec', f'{LIBRE} linespace_style 1, at least'),
    'StyleSheet': ('empty', 'No plot style table'),
    'SunHandle': ('empty', 'Null sun handle'),
    'TextRotation': ('identity', 'Zero text rotation'),
    'TopMargin': ('choice', 'Zero plot margin, a neutral Kit choice'),
    'UcsElevation': ('identity', 'Zero UCS elevation'),
    'UcsOrigin': ('identity', 'UCS origin at zero'),
    'UcsOrtho': ('empty', 'UCS is not orthographic'),
    'UcsPerViewport': ('spec', 'DXF 71 UCS per viewport 1, the viewport keeps its UCS'),
    'UcsXAxis': ('identity', 'World X axis'),
    'UcsYAxis': ('identity', 'World Y axis'),
    'UserText': ('empty', 'No dimension text override'),
    'VertAlign': ('spec', 'DXF 74 vertical alignment 3, top'),
    'VisualStyle': ('empty', 'Null visual style handle'),
    'XrefBlock': ('empty', 'Null external reference block handle'),
    'XrefDependent': ('empty', 'Not dependent on an external reference'),
    'XrefPath': ('empty', 'No external reference path'),
    'Unknown': ('observed', 'Dimension bit after the measurement; 0 in every instance'),
    'UnknownBit': ('observed', f'MTEXT bit before the background flags; {LIBRE} names it unknown_b0; 0 in every instance'),
    'RealSix': ('observed', 'DRAWINGVIEW real after the view scale; 0 in every instance'),
    'AmbientFlags': ('empty', 'Ambient colour flags; plain colour'),
    'AmbientIndex': ('empty', 'Ambient colour index 0'),
    'AmbientRgb': ('template', 'Ambient light colour of the default viewport'),
    'ClipBoundary': ('empty', 'Null clip boundary handle'),
    'Frozen': ('empty', 'No frozen layers'),
    'FrozenCount': ('empty', 'No frozen layers'),
    'Refs': ('empty', 'No record references'),
    'TextOne': ('vocabulary', 'Reference data tag HOLE_DATA, the hole table data key'),
    'TextFive': ('observed', 'Fifth reference data text; empty in every instance'),
}

ASSOC = {
    'ClassVersion': ('version', f'{LIBRE} class_version'),
    'GeometryStatus': ('spec', f'{LIBRE} geometry_status: 0 well defined'),
    'ActionBody': ('empty', 'Null action body handle'),
    'ActionLongOne': ('spec', f'{LIBRE} AcDbAssocAction writes this word as a fixed 0 before the owned parameter count'),
    'ActionLongTwo': ('spec', f'{LIBRE} AcDbAssocAction writes this word as a fixed 0 before the value count'),
    'OwnedParamCount': ('empty', 'No owned parameters'),
    'OwnedParams': ('empty', 'No owned parameters'),
    'ValueParamCount': ('empty', 'No value parameters'),
    'ValueParams': ('empty', 'No value parameters'),
    'DependencyCount': ('empty', 'No dependencies'),
    'Dependencies': ('empty', 'No dependencies'),
    'MaxDependencyIndex': ('empty', 'No dependency index used'),
    'NetworkVersion': ('version', f'{LIBRE} network_version'),
    'ErasedCount': ('empty', 'No erased actions'),
    'DependencyStatus': ('spec', f'{LIBRE} status: 0 up to date'),
    'IsReadDependency': ('spec', f'{LIBRE} is_read_dep'),
    'IsWriteDependency': ('spec', f'{LIBRE} is_write_dep'),
    'FlagThree': ('spec', f'{LIBRE} is_attached_to_object'),
    'FlagFour': ('spec', f'{LIBRE} is_delegating_to_owning_action'),
    'HasCompoundId': ('spec', 'Compound object id present for geometry dependencies only'),
    'CompoundClass': ('vocabulary', 'Compound id class name AcDbImpBlockRefPathObjectId'),
    'CompoundVersion': ('version', 'Compound id version 0'),
    'DependencyBody': ('empty', 'Null dependency body handle'),
    'GeomVersion': ('version', f'{LIBRE} AcDbAssocGeomDependency class_version 0'),
    'GeomLongTwo': ('spec', f'{LIBRE} reads these two bits as enabled 1 and has_classname 0 of AcDbAssocPersSubentId; Kit reads the same bits as a BL 0'),
    'GeomLongThree': ('spec', f'{LIBRE} AcDbAssocPersSubentId class_code; Fusion geometry dependencies use code 4'),
    'GeomLongFour': ('observed', 'Geometry dependency word; 0 in every instance'),
    'GeomFlag': ('observed', f'Geometry dependency bit; 0 in every instance; {LIBRE} has dependent_on_compound_object here'),
    'ParamVersion': ('spec', f'{LIBRE} AcDbAssocActionParam is_r2013: 1 for R2013 and later files'),
    'ParamLong': ('version', f'{LIBRE} AcDbAssocActionParam aap_version 0'),
    'ParamName': ('vocabulary', 'Action parameter name of the Fusion view network'),
    'SingleVersion': ('version', f'{LIBRE} AcDbAssocSingleDependencyActionParam class version 0'),
    'ObjectVersion': ('version', f'{LIBRE} AcDbAssocObjectActionParam class version 0'),
    'BorderVersion': ('version', 'View border parameter version 1'),
    'ViewVersion': ('version', 'View representation parameter version 1'),
    'BodyVersion': ('version', 'View representation action body version 1'),
    'ManagerVersion': ('version', 'Manager version 0'),
    'ManagerLongTwo': ('observed', 'Hatch manager word; 0 in every instance'),
    'ManagerLongThree': ('observed', 'Hatch manager word; 0 in every instance'),
    'ManagerLongFour': ('observed', 'Hatch manager word; 0 in every instance'),
    'ManagerLongFive': ('observed', 'Hatch manager word; 0 in every instance'),
    'ManagerFlag': ('observed', 'Inventor subentity manager bit; 1 in every instance'),
    'ManagerLong': ('observed', 'Inventor subentity manager word; 64 in every instance'),
    'ManagerRaw': ('observed', 'Inventor subentity manager raw word; 0 in every instance'),
    'ManagerCount': ('empty', 'No managed subentities'),
    'SourceMappingCount': ('empty', 'No source mappings'),
    'LayerMappingCount': ('vocabulary', 'Two edge category to layer mappings'),
    'LayerMappings': ('vocabulary', 'Visible and hidden edge categories mapped to template layers'),
    'ContextVersion': ('version', f'{LIBRE} MTEXT context class_version 4'),
    'FlagOne': ('observed', 'Reference data bit; 0 in every instance'),
    'FlagTwo': ('observed', 'Reference data bit; 0 in every instance'),
    'LongOne': ('observed', 'Reference data word; 2 in every instance'),
    'LongTwo': ('observed', 'Reference data word; 1 in every instance'),
    'LongThree': ('observed', 'Reference data word; 1 in every instance'),
    'PlotFlagsLayout': ('choice', 'Plot flags 688, a neutral Kit choice'),
    'Style': ('vocabulary', 'A text style of the Fusion drawing template'),
}

ASSOC_REF_FLAGS = {('ACDBREFERENCEDATA', 'FlagThree'): ('observed', 'Reference data bit; 0 in every instance')}


def spoken(value):
    return json.dumps(value) if isinstance(value, str) else str(value)


def ordered(item):
    try:
        return (0, float(item[0]), item[0])
    except ValueError:
        return (1, 0.0, item[0])


@functools.cache
def grafted():
    if not GRAFTS.exists():
        return {}
    record = json.loads(GRAFTS.read_text())
    found = collections.defaultdict(lambda: collections.defaultdict(dict))
    for label, graft in record['grafts'].items():
        runs = [run['outcome'] for run in graft['runs']]
        if not runs:
            continue
        outcome = 'damaged' if 'damaged' in runs else 'opened' if 'opened' in runs else 'stalled'
        edits = graft['edits']
        if not edits:
            continue
        keys = {(edit['class'], edit['field']) for edit in edits}
        if outcome != 'opened' and len(keys) > 1:
            continue
        for edit in edits:
            cell = found[(edit['class'], edit['field'])]
            cell['opened'].setdefault(spoken(edit['old']), 'Y0Base')
            cell[outcome].setdefault(spoken(edit['new']), label)
    return found


def tested(class_name, field, value, known):
    key = (class_name, field)
    shared = class_name in DIMENSIONS and key not in grafted()
    if shared:
        key = ('DIMENSION_LINEAR', field)
    cell = grafted().get(key)
    if not cell or len(cell) == 1 and set(cell['opened']) == {spoken(value)}:
        return None
    parts = []
    for outcome, words in OUTCOMES:
        if cell.get(outcome):
            values = ', '.join(f'{shown} ({label})' for shown, label in sorted(cell[outcome].items(), key=ordered))
            parts.append(f'{words} {values}')
    prefix = known[1].split('; ')[0].rstrip('.') + '. '
    note = prefix + '; '.join(parts) + f'. Kit writes {spoken(value)}, the value of every Fusion save'
    if shared:
        note += '. The field is common dimension data; the graft changed it on DIMENSION_LINEAR'
    return ('tested', note)


def reason(class_name, field, value):
    known = described(class_name, field)
    if known[0] == 'observed':
        return tested(class_name, field, value, known) or known
    return known


def described(class_name, field):
    if (class_name, field) in ASSOC_REF_FLAGS:
        return ASSOC_REF_FLAGS[(class_name, field)]
    if class_name == 'LAYOUT' and field == 'PlotFlags':
        return ASSOC['PlotFlagsLayout']
    if class_name == 'DRAWINGVIEW' and field == 'ClassVersion':
        return ('version', 'Drawing view class version 1')
    if class_name == 'DRAWINGVIEW' and field == 'LtypeScale':
        return ('vocabulary', 'View border linetype scale 0.25 of the Fusion drawing template')
    for table in (ENTITY, ASSOC, NAMED):
        if field in table:
            return table[field]
    return ('observed', 'No reason recorded')


def evidence(paths, defaults):
    stats = collections.defaultdict(lambda: [0, 0, set()])
    for index, path in enumerate(paths):
        for class_name, common, data, _keys in GenerateDefaults.sheet_rows(GenerateDefaults.load(path)):
            parts = {'Common': dict(common), 'Data': dict(data)}
            for part, rows in defaults.get(class_name, {}).items():
                for field, value in rows:
                    cell = stats[(class_name, part, field)]
                    cell[0] += 1
                    cell[2].add(index)
                    if field in parts[part] and json.dumps(parts[part][field], sort_keys=True) == json.dumps(value, sort_keys=True):
                        cell[1] += 1
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--drawings', nargs='+', required=True, help='Fusion-made f2d files')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    defaults = json.loads(DEFAULTS.read_text())
    stats = evidence(args.drawings, defaults)
    rows = []
    for class_name, parts in defaults.items():
        for part in ('Common', 'Data'):
            for field, value in parts[part]:
                basis, note = reason(class_name, field, value)
                instances, equal, saves = stats.get((class_name, part, field), [0, 0, set()])
                rows.append({'Class': class_name, 'Part': part, 'Field': field, 'Value': value, 'Basis': basis,
                             'Note': note, 'Instances': instances, 'Equal': equal, 'Drawings': len(saves)})
    count = collections.Counter(row['Basis'] for row in rows)
    report = {
        'schema': 'FusionSheetDefaultReasons/1',
        'defaults': str(DEFAULTS.relative_to(ROOT)),
        'defaultsSha256': hashlib.sha256(DEFAULTS.read_bytes()).hexdigest(),
        'drawings': [hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in args.drawings],
        'rows': len(rows),
        'basisCounts': dict(sorted(count.items())),
        'observedFields': sorted({f"{row['Class']}.{row['Field']}" for row in rows if row['Basis'] == 'observed'}),
        'rowsWithoutInstance': sum(row['Instances'] == 0 for row in rows),
        'rowsDiffering': sum(row['Equal'] < row['Instances'] for row in rows),
        'table': rows,
    }
    Path(args.out).write_text(json.dumps(report, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({key: report[key] for key in ('rows', 'basisCounts', 'rowsWithoutInstance', 'rowsDiffering')}))
    print('\n'.join(report['observedFields']))


if __name__ == '__main__':
    main()
