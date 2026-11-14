"""Prepare native acceptance inputs for the lifted whole-member boundaries.

Every SMB and SMBH member of each source archive is read and re-emitted by the
production typed codec, and the archive is rewritten with the source compression
methods and timestamps. The script records what each member holds that the
boundary pass made readable: FDM thread attributes, no-merge attributes, wire
records, wire shells, degenerate edges, helix subtypes and the largest record
and bulletin board.
Run with /opt/homebrew/bin/python3.14 -I (ZIP method 93 needs Python 3.14).
"""

import collections
import hashlib
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

import AsmScan  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import FeatureAttrib  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NoMergeAttrib import NoMergeAttrib  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Geometry.WireNode import WireNode  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry  # noqa: E402

OUT = ROOT / "re/Fusion/LocalOracle/ComplexGeometry/Bounds"
STUDY = "re/Fusion/Study/"
CASES = (
    ("ModeledThread", "threadmodes-d51d2ae60564/modeled_full.f3d", "helix_int_cur, helix_spl_line, FDM thread attributes", "d1", 1.5, 1.0),
    ("TappedHole", "tappedholes-409e96788503/modeled_full.f3d", "helix_int_cur, helix_spl_line, FDM thread attributes, degenerate edge", "d7", 0.8, -0.2),
    ("AlongVector", "splitfacemodes-4fc4adf2a868/along_vector.f3d", "wire, wire shell, no-merge attribute", None, None, None),
    ("ClosestPoint", "splitfacemodes-4fc4adf2a868/closest_point.f3d", "wire, wire shell, no-merge attribute", None, None, None),
    ("SketchLine", "surfacetrimtools-ca26d21e7ad9/sketch_line.f3d", "wire, wire shell", None, None, None),
    ("OffsetPositive", "surfacetrimtools-650ca09579b1/sketch_line_offset_positive.f3d", "wire, wire shell", None, None, None),
    ("ReversedNegative", "surfacetrimtools-650ca09579b1/sketch_line_reversed_negative.f3d", "wire, wire shell", None, None, None),
    ("TwoTexts", "embosstext-cd769aa41cdf/two_texts.f3d", "history record above 4096 tokens", None, None, None),
    ("MultipleBodies", "rectsymholdouts-cf85ce4a0382/multiple_bodies.f3d", "largest record and bulletin board in the corpus", None, None, None),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def largest_board(records):
    largest = 0
    for record in records:
        if record["name"] != "delta_state":
            continue
        tokens = [tuple(token) for token in record["tokens"]]
        index = 10 if tokens[8][0] == 10 else 9
        while tokens[index] == (4, 1):
            index += 3
            changes = 0
            while tokens[index] == (4, 1):
                changes += 1
                index += 3
            largest = max(largest, changes)
            index += 1
    return largest


def typed_summary(entities, records):
    kinds = collections.Counter()
    for value in entities:
        if isinstance(value, FeatureAttrib):
            kinds["FeatureAttrib:" + value.DataName] += 1
        elif isinstance(value, (NoMergeAttrib, WireNode)):
            kinds[type(value).__name__] += 1
        elif isinstance(value, ShellNode) and value.FirstWire != -1:
            kinds["WireShell"] += 1
    for record in records:
        tokens = [tuple(token) if isinstance(token, list) else token for token in record["tokens"]]
        if record["name"] in ("edge", "tedge-edge") and tokens[8] == (12, -1) and tokens[3] == tokens[5]:
            kinds["DegenerateEdge"] += 1
        for tag, value in tokens:
            if tag in (7, 13, 14) and isinstance(value, str) and value.startswith("helix"):
                kinds["Subtype:" + value] += 1
    features = sorted({(value.DataName, value.FeatureTag, value.Flags, value.TypeCode, value.TailCode) for value in entities if isinstance(value, FeatureAttrib)}, key=repr)
    return dict(sorted(kinds.items())), [dict(dataName=a, featureTag=b, flags=c, typeCode=d, tailCode=e) for a, b, c, d, e in features]


def prepare(label, relative, scope, parameter, factor, expected):
    source = ROOT / STUDY / relative
    target = OUT / (label + "History.f3d")
    members = []
    with zipfile.ZipFile(source) as archive, zipfile.ZipFile(target, "w") as output:
        for entry in archive.infolist():
            data = archive.read(entry)
            item = None
            if entry.filename.endswith(".smbh"):
                model = ReadJournal(data)
                emitted = EmitJournal(model)
                item = dict(member=entry.filename, kind="history", records=len(model.Entities), activeRecords=model.ActiveCount, states=len(model.States))
                entities = model.Entities
            elif entry.filename.endswith(".smb"):
                model = ReadGeometry(data)
                emitted = EmitGeometry(model)
                item = dict(member=entry.filename, kind="snapshot", records=len(model.Entities))
                entities = model.Entities
            else:
                emitted = data
            if item is not None:
                _, _, records = AsmScan.records(data)
                item.update(sha256=digest(data), emittedSha256=digest(emitted), byteExact=emitted == data, largestRecordTokens=max(len(record["tokens"]) for record in records), largestBoardChanges=largest_board(records))
                item["typed"], item["featureAttributes"] = typed_summary(entities, records)
                members.append(item)
            info = zipfile.ZipInfo(entry.filename, date_time=entry.date_time)
            info.external_attr = entry.external_attr
            output.writestr(info, emitted, compress_type=entry.compress_type)
    if not members or not all(item["byteExact"] for item in members):
        raise RuntimeError(label + " members are not byte exact")
    case = dict(label=label, scope=scope, source=str(source.relative_to(ROOT)), sourceSha256=digest(source.read_bytes()), target=str(target.relative_to(ROOT)), targetSha256=digest(target.read_bytes()), members=members, boundary="Every SMB and SMBH member replaced by typed ReadJournal/EmitJournal or ReadGeometry/EmitGeometry output; other members copied; source compression methods and timestamps kept")
    if parameter is not None:
        case.update(parameter=parameter, factor=factor, expectedThreadExtentChangeCm=expected)
    print(label, case["targetSha256"], flush=True)
    return case


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = dict(schema="FusionComplexBoundsPreparation/1", status="preparing", cases=[])
    for case in CASES:
        report["cases"].append(prepare(*case))
    report["status"] = "prepared"
    (OUT / "Preparation.json").write_text(json.dumps(report, indent=1) + "\n")


if __name__ == "__main__":
    main()
