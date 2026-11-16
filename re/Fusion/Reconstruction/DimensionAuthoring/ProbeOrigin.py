"""Generate and inspect a research-only Fusion rectangle with an origin coincidence."""

from argparse import ArgumentParser
from importlib import import_module
import json
from pathlib import Path
import struct
from subprocess import check_output
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re" / "automation")]

from FusionCutExtentEvidence import REVISION, design_members
from PairedCaptureIntake import GitSnapshot, require, sha256
from decode_sketch import attributes, reference
from fusion_metadata import design_records

from convert.adapters.Fusion.Projection.NativeIndex import MakeIndex
from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole
from convert.Formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Sketches.Dimensional.DimRecord import ReadDimRecord
from convert.Formats.Fusion.Sketches.Dimensional.DimSpec import KLinearDimension
from convert.Formats.Fusion.Sketches.Geometric.GeomRuleRecord import (
    KGeomRuleGuid,
    ReadGeomRule,
)
from convert.Formats.Fusion.Sketches.RulePrefix import ReadRulePrefix

CAPTURES = {
    "P01/fusion-5dc3245eb59c": (
        6,
        "88ca575b5176e61cd25d585c9cb6804d6ea2c1b3d3ef843ac2d2bcb43593a4db",
    ),
    "P03/fusion-8d53584027ff": (
        8,
        "f42a7e81b9ae108ba69d440ff411a8828dbc9ee0bbd54d6242c22370cf6560b8",
    ),
}
POINT_CLASS = "C2CEDAE7-1716-47C1-B7B1-07B70081D0FB"
FREE_FLAGS = (0,) * 8
ORIGIN_FLAGS = (0, 0, 0, 1, 1, 1, 0, 0)
DIMENSION_CODES = {0x400000, 0x800000}


def add_origin_coincidence(author):
    sketch = SketchRole(author)
    roles = ("sketch_origin", "corner_a")
    ref = author.Reference
    name = "rectangle_origin_coincidence"
    author.Change("corner_a", isFixed=False)
    author.Allocate(
        name,
        "SketchGeomConstraint",
        Subjects=list(roles),
        NamedPairs=MakeAttributes(EntityGenesis=author.Policy.SketchGeneration),
        Fields={
            "ParentNode": ref(sketch),
            "constraintType": 1,
            "geometries": [ref(role) for role in roles[::-1]],
            "isVisible": False,
        },
    )
    rules = author.FindEntity(sketch).FieldValues["constraints"]
    author.Change(sketch, constraints=[*rules, ref(name)])


def emit_rectangle():
    seam = import_module(
        "convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.ConstrainMut"
    )
    fixed_rectangle = seam.AddConstrMut

    def allocate_coincidence(author):
        fixed_rectangle(author)
        add_origin_coincidence(author)

    seam.AddConstrMut = allocate_coincidence
    try:
        return EmitDocument(
            DocumentSpec(
                "Origin coincidence research",
                "unused_length",
                31.25,
                ProfileKind="rectangle",
                WidthMm=17.75,
                DepthMm=24.125,
                SketchName="Origin Coincident Rectangle",
                ConstrainRectangle=True,
                WidthParamName="proof_width",
                DepthParamName="proof_height",
            )
        )
    finally:
        seam.AddConstrMut = fixed_rectangle


def point_row(raw, record):
    props, base = attributes(raw, 2)
    require(
        record.class_guid == POINT_CLASS
        and len(raw) - base == 99
        and props["EntityGenesis"] == 2,
        "origin relation must use typed sketch points",
    )
    return {
        "id": record.object_id,
        "flags": tuple(raw[base + 11 : base + 19]),
        "coordinates_cm": struct.unpack_from("<3d", raw, base + 19),
        "owner": reference(raw, len(raw) - 11),
    }


def native_records(content):
    streams, members = design_members(content)
    bulk = streams["BulkStream.dat"]
    records, _ = design_records(bulk, streams["MetaStream.dat"])
    primary = {row.object_id: row for row in records if row.is_primary}
    require(
        len(primary) == sum(row.is_primary for row in records),
        "duplicate native primary ID",
    )
    bodies = {key: bulk[row.body : row.end] for key, row in primary.items()}
    rules = {
        key: ReadGeomRule(bodies[key])
        for key, row in primary.items()
        if row.class_guid == KGeomRuleGuid
    }
    require(
        sorted(rule.CodeValue for rule in rules.values()) == [1, 64, 64, 128, 128],
        "expected one origin coincidence and four line rules",
    )
    identity = next(key for key, rule in rules.items() if rule.CodeValue == 1)
    rule = rules[identity]
    deps, slots, props = ReadRulePrefix(MetaCursor(bodies[identity]))
    require(
        len(rule.Arguments) == 2
        and rule.Arguments == deps[::-1]
        and slots == (0, 0)
        and props == {"EntityGenesis": 2},
        "coincidence dependencies, arguments or slots differ",
    )
    corner, origin = [point_row(bodies[key], primary[key]) for key in rule.Arguments]
    require(
        corner["id"] != origin["id"]
        and corner["owner"] == origin["owner"] == rule.OwnerId
        and corner["flags"] == FREE_FLAGS
        and origin["flags"] == ORIGIN_FLAGS
        and corner["coordinates_cm"] == origin["coordinates_cm"] == (0, 0, 0),
        "coincidence must bind a free corner to the distinct fixed origin",
    )
    anchor = {
        "id": identity,
        "owner": rule.OwnerId,
        "code": rule.CodeValue,
        "dependencies": deps,
        "ranks": slots,
        "arguments": rule.Arguments,
        "corner": corner,
        "origin": origin,
        "bulk_record_offset": primary[identity].start,
        "bulk_record_end": primary[identity].end,
    }
    dimensions = [
        row.object_id
        for row in sorted(primary.values(), key=lambda row: row.start)
        if row.class_guid.upper() == KLinearDimension.upper()
    ]
    require(len(dimensions) == 2, "expected two primary linear dimensions")
    return members, rules, anchor, {key: bodies[key] for key in dimensions}


def check_ranks(rows, anchor):
    corner = anchor["corner"]["id"]
    origin = anchor["origin"]["id"]
    require(
        {row["code"] for row in rows} == DIMENSION_CODES,
        "dimension direction codes differ",
    )
    for slot, row in enumerate(rows, start=1):
        deps = row["dependencies"]
        require(
            len(deps) == 2
            and corner in deps
            and origin not in deps
            and len(set(deps)) == 2,
            "dimension must bind the shared corner and a different perimeter point",
        )
        require(
            row["ranks"] == tuple(slot if key == corner else 0 for key in deps),
            "dimension observer rank does not follow the origin coincidence",
        )
        require(
            row["arguments"] == (deps if slot == 1 else deps[::-1]),
            "dimensions keep different dependency and argument orders",
        )


def inspect_generated(content):
    members, rules, anchor, bodies = native_records(content)
    model = ReadDocument(content)
    graph = MakeIndex(model)
    typed = {row.ObjectId: row for row in graph.Segment.Records if row.IsPrimary}
    (sketch,) = graph.Names["MSketch"]
    require(
        not model.Bodies
        and sketch == anchor["owner"]
        and len(graph.Names["Line3D"]) == 4
        and len(graph.Names["Point3D"]) == 5
        and {item.ObjectId for item in graph.Fields[sketch]["constraints"].Items}
        == rules.keys(),
        "generated sketch does not own the expected geometry and rules",
    )
    lines = [graph.Fields[key] for key in graph.Names["Line3D"]]
    endpoints = [
        row[name].ObjectId for row in lines for name in ("rStartPoint", "rEndPoint")
    ]
    require(
        endpoints.count(anchor["corner"]["id"]) == 2
        and anchor["origin"]["id"] not in endpoints,
        "only the corner participates in the rectangle perimeter",
    )

    def typed_subjects(key):
        return tuple(
            (item.Target.ObjectId, item.ObserverIndex)
            for item in typed[key].Frame.Subjects
        )

    require(
        typed_subjects(anchor["id"])
        == tuple(zip(anchor["dependencies"], anchor["ranks"], strict=True)),
        "typed coincidence subjects differ from the raw prefix",
    )
    (settings,) = graph.Names["CommonDataAssetSettings"]
    rows = []
    for key, raw in bodies.items():
        deps, ranks, props = ReadRulePrefix(MetaCursor(raw))
        require(
            len(deps) == 3
            and deps[0] == settings
            and props == {"EntityGenesis": 0}
            and typed_subjects(key) == tuple(zip(deps, ranks, strict=True)),
            "typed dimension subjects differ from the raw prefix",
        )
        fields = graph.Fields[key]
        rows.append(
            {
                "id": key,
                "code": fields["constraintType"],
                "dependencies": deps[1:],
                "ranks": ranks[1:],
                "settings_rank": ranks[0],
                "arguments": tuple(
                    item.ObjectId for item in fields["geometries"].Items
                ),
            }
        )
    check_ranks(rows, anchor)
    require(
        [row["settings_rank"] for row in rows] == [0, 1],
        "generated settings ranks differ",
    )
    return {
        "archive_sha256": sha256(content),
        "archive_bytes": len(content),
        "design_members": members,
        "body_count": 0,
        "line_count": len(lines),
        "anchor": anchor,
        "dimensions": rows,
    }


def inspect_controls():
    snapshot = GitSnapshot(ROOT)
    receipts = {}
    for folder, (count, expected_digest) in CAPTURES.items():
        prefix = f"re/automation/PairedCaptures/{folder}/"
        raw = snapshot.blob(REVISION, prefix + "receipt.json")
        require(
            sha256(raw) == expected_digest, "original Fusion capture receipt differs"
        )
        files = snapshot.parse_document(raw, "capture receipt")["native_files"]
        require(
            len(files) == len({row["file"] for row in files}) == count,
            "unexpected control roster",
        )
        cases = []
        for pin in files:
            content = snapshot.blob(REVISION, prefix + pin["file"])
            require(
                len(content) == pin["size_bytes"] and sha256(content) == pin["sha256"],
                "original Fusion capture bytes differ",
            )
            _, _, anchor, bodies = native_records(content)
            rows = []
            for raw_dim in bodies.values():
                dimension = ReadDimRecord(raw_dim, KLinearDimension)
                rows.append(
                    {
                        "code": dimension.Code,
                        "dependencies": dimension.DependencyIds,
                        "ranks": dimension.DependencySlots,
                        "arguments": dimension.TargetIds,
                        "settings_rank": dimension.PrefixSlot,
                    }
                )
            check_ranks(rows, anchor)
            cases.append(
                {
                    "file": pin["file"],
                    "archive_sha256": pin["sha256"],
                    "anchor": anchor,
                    "dimensions": rows,
                }
            )
        receipts[folder] = {"sha256": expected_digest, "files": cases}
    return {"revision": REVISION, "receipts": receipts}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="new directory for archive and evidence",
    )
    output = parser.parse_args().output
    content = emit_rectangle()
    generated = inspect_generated(content)
    report = {
        "claim": "generated_archive_record_evidence",
        "native_application_acceptance": False,
        "codec_revision": check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "probe_sha256": sha256(Path(__file__).read_bytes()),
        "generated": generated,
        "controls": inspect_controls(),
    }
    output.mkdir()
    (output / "OriginCoincidentRectangle.f3d").write_bytes(content)
    encoded = (
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    (output / "OriginCoincidenceEvidence.json").write_bytes(encoded)
    print(sha256(encoded))


if __name__ == "__main__":
    main()
