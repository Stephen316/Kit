import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from DecodeControls import NAMES
from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.DocumentCodec.Records.DocumentCatalog import DocumentCatalog
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

CONTROLS = REPO / "re/Fusion/LocalOracle/FeatureAuthoring/Controls"
SOURCES = tuple(sys.argv[1:]) or ("Combine", "SplitBody")
TARGET = REPO / "src/convert/formats/Fusion/DocumentCodec/PartFeatures/Vocabulary"
ROOT = "98542EB9-A4F2-4137-A808-DBB5B3CD6159"

# Defaults are schema-neutral: null for references and optionals, zero, false,
# the empty string, or the empty container. Nothing is copied from a control.
NEUTRAL = {"bool": False, "u8": 0, "u16": 0, "u32": 0, "u64": 0, "i32": 0, "f64": 0.0, "utf16": ""}
EMPTY_KINDS = {"sequence", "set", "map"}
NULL_KINDS = {"ref", "optional"}

# Geometry (struct), transforms (matrix) and nested value objects never get a
# default. Every writer must supply them.
REQUIRED_KINDS = {"struct", "matrix", "object"}

# Further required fields: ids, id maps, recipes and the mode codes each writer
# declares for the feature it emits. A missing one raises in ConvertFields or
# DraftGroups instead of falling back to a value.
REQUIRED = {
    "ASMRecipe": {"m_Recipe"},
    "DRBody": {"operIdTypeMap"},
    "DRPoint": {"refType"},
    "DRVector": {"axisTrackType", "refType"},
    "DcChamferData": {"bIsComputeChain", "chamferType", "selIndex"},
    "DcChamferFeature": {"cornerType", "isTangentPropagation", "primaryIDRowIndexMap"},
    "DcCombineFeature": {"booleanOperation", "occDR2FeatIdMap"},
    "DcDraftFeature": {
        "MovingPartingLineDraftAngleType",
        "draftType",
        "m_bTangentPropagation",
        "m_directionType",
        "m_fixedPlaneDraftAngleMode",
    },
    "DcFilletEdgeData": {"bConstantRadius", "bIsComputeChain"},
    "DcFilletEdgeFeature": {"isRollingBallCorners", "isTangentPropagation"},
    "DcHoleFeature": {"bInside1", "bInside2", "extendFaceOption"},
    "DcIntParameter": {"isRoundToNearestInt", "value"},
    "DcLoftFeature": {
        "IsEndTangencyFlippedDirection",
        "IsStartTangencyFlippedDirection",
        "bChainOption",
        "bMergeCurves",
        "booleanOperation",
        "endRailsTakeOffIndex",
        "isSolidOperation",
        "startRailsTakeOffIndex",
    },
    "DcLoftSectionData": {"sectionType"},
    "DcMoveMatrix": {"moveMethodType", "point2PositionCSType"},
    "DcPatternBaseData": {"computeOption", "computeType", "countUMax", "occOperationIdsMap"},
    "DcPatternOccurrence": {"occTagId"},
    "DcPatternSource": {"caches"},
    "DcRectangularPatternData": {"countVMax"},
    "DcRevolveFeature": {"booleanOperation", "extendFaceOption", "isSolidOperation"},
    "DcSplitFeature": {"isExtendTool", "occDR2FeatIdMap"},
    "DcSweepFeature": {
        "booleanOperation",
        "chainPropagation",
        "isAlongDirectionSameAsProfileNormal",
        "isSolidOperation",
        "isXScale",
        "isYScale",
        "sweepType",
    },
    "DcSweepToolBody": {"isAlongDistanceParameterValid"},
    "DcWorkAxis": {"creationType"},
    "DcWorkGeometry": {"isVisibleBeforeRollback"},
    "DcWorkPlane": {"chainPropagation", "isProportionalParam"},
    "DcWorkPoint": {"chainPropagation"},
    "SketchCurveEntityRecipe": {"secondaryTag"},
    "SketchEntityRecipe": {"sketchId", "tag"},
}


def known_guids():
    result = set()
    for vocab in (REPO / "src/convert/formats/Fusion/DocumentCodec").rglob("*Classes.json"):
        if "PartFeatures" in vocab.parts:
            continue
        for entry in json.loads(vocab.read_text()):
            result.add(entry["ClassGuid"].upper())
    return result


def wire_json(shape):
    result = {"KindValue": shape.KindValue}
    if shape.Arguments:
        result["Arguments"] = [wire_json(a) for a in shape.Arguments]
    if shape.Members:
        result["Members"] = [field_json(m) for m in shape.Members]
    if shape.ClassGuid:
        result["ClassGuid"] = shape.ClassGuid
    if shape.FixedCount:
        result["FixedCount"] = shape.FixedCount
    if shape.AllowedInts:
        result["AllowedInts"] = list(shape.AllowedInts)
    if shape.HasMatrixRows:
        result["HasMatrixRows"] = True
    return result


def field_json(member):
    return {"FieldName": member.FieldName, "ValueType": wire_json(member.ValueType), "IsSaved": member.IsSaved}


def class_name(guid, is_value):
    name = NAMES[guid.upper()]
    if is_value and name.endswith("MetaType"):
        name = name[: -len("MetaType")]
    return name


def neutral_value(owner, field, shape):
    kind = shape["KindValue"]
    if kind in NULL_KINDS:
        return None
    if kind in EMPTY_KINDS:
        return []
    if kind not in NEUTRAL:
        raise ValueError("no neutral value for " + owner + "." + field + " of kind " + kind)
    value = NEUTRAL[kind]
    if shape.get("AllowedInts") and value not in shape["AllowedInts"]:
        raise ValueError(owner + "." + field + " has no neutral member; list it in REQUIRED")
    return value


def neutral_defaults(vocabulary, required=REQUIRED):
    names = {entry["NameValue"] for entry in vocabulary}
    unknown = sorted(set(required) - names)
    if unknown:
        raise ValueError("REQUIRED names unknown classes " + repr(unknown))
    result = {}
    for entry in vocabulary:
        if entry["IsValue"]:
            continue
        owner = entry["NameValue"]
        saved = {m["FieldName"]: m["ValueType"] for m in entry["Members"] if m["IsSaved"]}
        stale = sorted(required.get(owner, set()) - set(saved))
        if stale:
            raise ValueError("REQUIRED names unknown fields " + owner + repr(stale))
        result[owner] = {
            field: neutral_value(owner, field, shape)
            for field, shape in saved.items()
            if shape["KindValue"] not in REQUIRED_KINDS and field not in required.get(owner, set())
        }
    return {name: result[name] for name in sorted(result)}


def main():
    existing = json.loads((TARGET / "FeatureClasses.json").read_text())
    known = known_guids() | {entry["ClassGuid"].upper() for entry in existing}
    catalog = DocumentCatalog(ReadDocSchemas())
    selected = {}
    spaces = {}
    for source in SOURCES:
        with OpenFusionZip((CONTROLS / (source + ".f3d")).read_bytes()) as archive:
            members = [m.Name for m in archive.Members]
            meta_name = next(n for n in members if n.endswith("MetaStream.dat") and "FusionDesignSegmentType" in n)
            meta_bytes = archive.ReadMember(meta_name, 1 << 26)
        metadata = ReadMetaWire(meta_bytes)
        for row in metadata.Classes:
            guid = row.ClassGuid.upper()
            if guid in known or guid in selected:
                continue
            selected[guid] = next(s for s in catalog.Classes[guid] if s.SchemaVersion == row.SchemaVersion)
            spaces[guid] = row.ClassSpace
    missing = [g for g, s in selected.items() if s.BaseGuid.upper() not in known and s.BaseGuid.upper() not in selected and s.BaseGuid.upper() != ROOT and s.BaseGuid]
    if missing:
        raise ValueError("lineage gap " + repr(missing))
    vocabulary = list(existing)
    for guid in sorted(selected):
        schema = selected[guid]
        name = class_name(guid, schema.IsValue)
        vocabulary.append({"ClassGuid": schema.ClassGuid, "BaseGuid": schema.BaseGuid, "SchemaVersion": schema.SchemaVersion, "Members": [field_json(m) for m in schema.Members], "IsValue": schema.IsValue, "NameValue": name, "ClassSpace": spaces[guid]})
    vocabulary.sort(key=lambda entry: entry["ClassGuid"].upper())
    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "FeatureClasses.json").write_text(json.dumps(vocabulary, indent=2) + "\n")
    defaults = neutral_defaults(vocabulary)
    (TARGET / "FeatureDefaults.json").write_text(json.dumps(defaults, indent=2, sort_keys=True) + "\n")
    print(len(vocabulary), "classes", len(defaults), "defaults")


# Copy and paste body classes go to their own vocabulary. AuthorSchemas adds
# it only to documents that paste a body, so other documents keep their class
# table. Catalogued classes come from the shipped catalog; the two classes the
# catalog lacks come from PasteSchemas.json, which records their black-box
# derivation. Names come from the public schema dump recorded there.
PASTE = HERE / "PasteSchemas.json"
PASTE_REQUIRED = {
    "BodyUuidProgenitor": {"bodyUuid", "outBodyUuid"},
    "DcBaseFeature": {"AssoctedPIDMap", "isAssociative"},
}


def author_guids():
    result = set()
    for name in ("DesignClasses.json", "RectangleClasses.json"):
        for entry in json.loads((REPO / "src/convert/formats/Fusion/DocumentCodec/Vocabulary" / name).read_text()):
            result.add(entry["ClassGuid"].upper())
    for entry in json.loads((TARGET / "FeatureClasses.json").read_text()):
        result.add(entry["ClassGuid"].upper())
    return result


def design_classes(source):
    with OpenFusionZip((CONTROLS / (source + ".f3d")).read_bytes()) as archive:
        members = [m.Name for m in archive.Members]
        meta_name = next(n for n in members if n.endswith("MetaStream.dat") and "FusionDesignSegmentType" in n)
        return ReadMetaWire(archive.ReadMember(meta_name, 1 << 26)).Classes


def paste_main(sources):
    research = json.loads(PASTE.read_text())
    names = {guid.upper(): name for guid, name in research["names"].items()}
    derived = {entry["ClassGuid"].upper(): entry for entry in research["derived"]}
    known = author_guids()
    catalog = DocumentCatalog(ReadDocSchemas())
    selected = {}
    for source in sources:
        for row in design_classes(source):
            guid = row.ClassGuid.upper()
            if guid in known or guid in selected:
                continue
            if guid in derived:
                entry = dict(derived[guid])
            else:
                schema = next(s for s in catalog.Classes[guid] if s.SchemaVersion == row.SchemaVersion)
                entry = {"ClassGuid": schema.ClassGuid, "BaseGuid": schema.BaseGuid, "SchemaVersion": schema.SchemaVersion, "Members": [field_json(m) for m in schema.Members], "IsValue": schema.IsValue}
            if entry["SchemaVersion"] != row.SchemaVersion:
                raise ValueError("schema version differs for " + guid)
            entry["NameValue"] = names[guid]
            entry["ClassSpace"] = row.ClassSpace
            selected[guid] = entry
    missing = [g for g, e in selected.items() if e["BaseGuid"].upper() not in known | set(selected) | {ROOT}]
    if missing:
        raise ValueError("lineage gap " + repr(missing))
    vocabulary = sorted(selected.values(), key=lambda entry: entry["ClassGuid"].upper())
    (TARGET / "PasteClasses.json").write_text(json.dumps(vocabulary, indent=2) + "\n")
    defaults = neutral_defaults(vocabulary, PASTE_REQUIRED)
    (TARGET / "PasteDefaults.json").write_text(json.dumps(defaults, indent=2, sort_keys=True) + "\n")
    print(len(vocabulary), "paste classes", len(defaults), "defaults")


if __name__ == "__main__":
    if SOURCES and SOURCES[0] == "--paste":
        paste_main(SOURCES[1:] or ("PastePlain",))
    else:
        main()
