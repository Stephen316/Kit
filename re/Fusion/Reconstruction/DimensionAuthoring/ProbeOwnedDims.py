"""Generate a research-only Fusion rectangle with two sketch-owned driving values."""

from argparse import ArgumentParser
from dataclasses import replace
from importlib import import_module
import io
import json
import math
from pathlib import Path
import struct
from subprocess import check_output
import zipfile

import ProbeOrigin

from FusionCutExtentEvidence import REVISION, ROOT, design_members
from PairedCaptureIntake import GitSnapshot, require, sha256
from fusion_metadata import parse_metadata
from convert.adapters.Fusion.Projection.NativeIndex import MakeIndex
from convert.Formats.Fusion.BulkSpans import ReadBulkSpans
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KRootName
from convert.Formats.Fusion.ContainerCodec.Wire.ReadDocument import ReadDocument as ReadHeader
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.LinkDimGraphMut import (
    LinkDimGraphMut,
)
from convert.Formats.Fusion.DocumentCodec.Sketch.SketchRole import SketchRole
from convert.Formats.Fusion.DocumentCodec.Values.ReadObjects import ReadSeries
from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.NumericParam import KParamGuid, ReadNativeNum
from convert.Formats.Fusion.ParamBinding import ResolveOwner
from convert.Formats.Fusion.Sketches.Dimensional.DimRecord import DimRecordBody, ReadDimRecord
from convert.Formats.Fusion.Sketches.Dimensional.DimSpec import KLinearDimension
from convert.Formats.Fusion.Sketches.SketchPlacement import KSketchFeature

P01_FOLDER = "re/automation/PairedCaptures/P01/fusion-5dc3245eb59c/"
P01_RECEIPT = "88ca575b5176e61cd25d585c9cb6804d6ea2c1b3d3ef843ac2d2bcb43593a4db"
LOOKUP_GUID = "E276745D-D84E-40D5-88BC-8C94DD4ACCDF"
SOFTWARE = 0x2A48004000000011
NAMES = ("width_mm", "height_mm")


def generate(*, sizes=(40.0, 20.0)):
    require(
        len(sizes) == 2 and all(math.isfinite(value) and value > 0 for value in sizes),
        "a pair of positive finite rectangle lengths is required",
    )
    width, height = sizes
    build = import_module("convert.Formats.Fusion.DocumentCodec.BuildDesign")
    dims = import_module("convert.Formats.Fusion.DocumentCodec.Rectangle.Dimensions.ConstrainMut")
    add_collections, add_constraints, emit = (
        build.AddCollectMut,
        build.ConstrainMut,
        ProbeOrigin.EmitDocument,
    )

    def collect_without_global(author):
        original = author.SpecValue
        author.SpecValue = replace(original, ProfileKind="form")
        try:
            add_collections(author)
        finally:
            author.SpecValue = original

    def constrain_owned(author):
        dims.AddConstrMut(author)
        axes = dims.MakeDimAxes(author.SpecValue)
        ref = author.Reference
        bindings, dimensions, names = [], [], []
        helper = author.FindEntity("parameter_names")
        for ordinal, axis in enumerate(axes, start=1):
            role = axis.RoleName
            dims.AddDimMut(author, axis)
            dims.BindDimMut(author, axis, ordinal, ordinal)
            param = role + "_model"
            author.Change(
                param,
                userName=axis.ParamName,
                name=f"Linear Dimension-{ordinal + 1}",
                expression=f"{axis.LengthMm:g} mm",
            )
            helper.Subjects.append(param)
            names.append({"key": axis.ParamName, "value": ref(param)})
            bindings.append(ref(role + "_binding"))
            dimensions.append(ref(role + "_dimension"))
        author.Change("parameters", highWaterMark=len(axes))
        author.Change("fragment", nextParamId=len(axes))
        author.Change(SketchRole(author), dimensions=dimensions)
        children = ReadSeries(author.FindEntity("dc_sketch").FieldValues["childNodes"])
        author.Change("dc_sketch", dcParameters=bindings, childNodes=[*children, *bindings])
        author.Change("parameter_names", parameterMap=sorted(names, key=lambda row: row["key"]))
        LinkDimGraphMut(author)

    def emit_p01(spec):
        return emit(
            replace(
                spec,
                Title="P01 sketch-owned dimensions",
                SketchName="RectangleSketch",
                WidthMm=width,
                DepthMm=height,
                WidthParamName=NAMES[0],
                DepthParamName=NAMES[1],
            )
        )

    build.AddCollectMut, build.ConstrainMut, ProbeOrigin.EmitDocument = (
        collect_without_global,
        constrain_owned,
        emit_p01,
    )
    try:
        return ProbeOrigin.emit_rectangle()
    finally:
        build.AddCollectMut, build.ConstrainMut, ProbeOrigin.EmitDocument = (
            add_collections,
            add_constraints,
            emit,
        )


def read_name_table(raw):
    cursor = MetaCursor(raw)
    require(
        cursor.TakeBytes(1) == b"\1" and cursor.ReadCount(3) == 3,
        "unexpected name-table subject frame",
    )
    subjects = [(ReadNativeRef(cursor), cursor.ReadWord()) for _ in range(3)]
    require(
        cursor.TakeBytes(1) == b"\0" and cursor.ReadCount(2) == 2,
        "unexpected name-table metadata or count",
    )
    named = [(cursor.ReadText(True), ReadNativeRef(cursor)) for _ in range(2)]
    require(cursor.Offset == len(raw), "name-table frame did not close")
    return subjects, named


def read_raw(content, native_control=False):
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        root = ReadHeader(archive.read(KRootName))
    require(root.SoftwareVersion == SOFTWARE, "unexpected Fusion root ProductVersion")
    streams, members = design_members(content)
    bulk, meta = streams["BulkStream.dat"], streams["MetaStream.dat"]
    metadata = parse_metadata(meta)
    require(
        metadata["uninterpreted_header_fields"] == [SOFTWARE & 0xFFFFFFFF, SOFTWARE >> 32]
        and metadata["properties"] == {"Application": 9, "Server": 7, "VolField": 7},
        "unexpected Design metadata framing",
    )
    primary = {row.ObjectId: row for row in ReadBulkSpans(bulk, meta) if row.IsPrimary}
    params = {}
    for row in primary.values():
        if row.ClassGuid != KParamGuid:
            continue
        p = ReadNativeNum(DimRecordBody(bulk, row))
        witness = ResolveOwner(bulk, primary, p, row)
        require(witness is not None, "unbound global parameter present")
        owner, binding = witness
        require(
            p.BindingId == binding.ObjectId
            and owner.ClassGuid == KSketchFeature
            and p.Metadata == bytes(11)
            and p.DisplayUnit == "mm"
            and p.RoleName == f"Linear Dimension-{p.NativeIndex + 1}"
            and p.Formula.endswith(" mm")
            and math.isclose(p.Number, float(p.Formula[:-3]) / 10, abs_tol=1e-12),
            "native direct driver is outside the measured numeric dialect",
        )
        native_param_id = struct.unpack_from("<I", DimRecordBody(bulk, binding), 40)[0]
        require(
            native_param_id == p.NativeIndex and p.ParamName not in params,
            "binding index or parameter name differs",
        )
        params[p.ParamName] = {
            "parameter_id": row.ObjectId,
            "binding_id": binding.ObjectId,
            "sketch_id": owner.ObjectId,
            "formula": p.Formula,
            "value_cm": p.Number,
            "unit": p.DisplayUnit,
            "role": p.RoleName,
            "collection_id": p.CollectionId,
            "creation_index": p.NativeIndex,
            "metadata_size": len(p.Metadata),
            "runtime_parameter_id": native_param_id,
            "parameter_span": (row.StartOffset, row.EndOffset),
            "binding_span": (binding.StartOffset, binding.EndOffset),
        }
    require(params.keys() == set(NAMES), "expected exactly the two named model drivers")
    width, height = (params[name] for name in NAMES)
    require(
        width["sketch_id"] == height["sketch_id"]
        and width["collection_id"] == height["collection_id"]
        and (width["creation_index"], height["creation_index"]) == (1, 2),
        "direct drivers disagree on ownership",
    )
    (lookup,) = [row for row in primary.values() if row.ClassGuid == LOOKUP_GUID]
    subjects, entries = read_name_table(DimRecordBody(bulk, lookup))
    require(
        dict(entries) == {name: param["parameter_id"] for name, param in params.items()}
        and subjects
        == [
            (width["collection_id"], 0),
            (width["parameter_id"], 0),
            (height["parameter_id"], 0),
        ],
        "name table or observer ordering differs from direct drivers",
    )
    if native_control:
        by_binding = {row["binding_id"]: row for row in params.values()}
        for span in primary.values():
            if span.ClassGuid.upper() != KLinearDimension.upper():
                continue
            dimension = ReadDimRecord(DimRecordBody(bulk, span), KLinearDimension)
            row = by_binding.pop(dimension.BindingId)
            row["dimension_id"] = span.ObjectId
            row["dimension_argument_ids"] = dimension.TargetIds
        require(
            not by_binding, "native rectangle dimensions do not select both owned direct drivers"
        )
    return {
        "product_version": hex(root.SoftwareVersion),
        "design_meta_words": metadata["uninterpreted_header_fields"],
        "members": members,
        "parameters": params,
        "name_table": entries,
        "name_table_subjects": subjects,
    }


def inspect_generated(content):
    raw = read_raw(content)
    anchor = ProbeOrigin.inspect_generated(content)
    graph = MakeIndex(ReadDocument(content))
    require(
        len(graph.Names["Parameter"]) == 2 and len(graph.Names["DcDoubleParameter"]) == 2,
        "typed graph includes duplicate parameters or bindings",
    )
    (feature,) = graph.Names["DcSketch"]
    (fragment,) = graph.Names["DcDesignFragment"]
    (table,) = graph.Names["ParameterTable"]
    require(
        graph.Fields[fragment]["nextParamId"] == 2 and graph.Fields[table]["highWaterMark"] == 2,
        "typed parameter accounting differs",
    )
    sketch = anchor["anchor"]["owner"]
    require(
        graph.Fields[feature]["rSketch"].ObjectId == sketch
        and graph.Fields[sketch]["rDcNode"].ObjectId == feature,
        "anchored sketch and parameter-owning feature do not reciprocate",
    )
    feature_fields = graph.Fields[feature]
    owned = tuple(item.ObjectId for item in feature_fields["dcParameters"].Items)
    require(
        owned == tuple(raw["parameters"][name]["binding_id"] for name in NAMES)
        and set(owned) <= {item.ObjectId for item in feature_fields["childNodes"].Items},
        "sketch binding inventory differs",
    )
    for name, dimension in zip(NAMES, anchor["dimensions"], strict=True):
        param = raw["parameters"][name]
        p = graph.Fields[param["parameter_id"]]
        b = graph.Fields[param["binding_id"]]
        d = graph.Fields[dimension["id"]]
        require(
            param["sketch_id"] == feature
            and param["collection_id"] == table
            and p["isUserDefined"] is False
            and p["isDriven"] is False
            and p["dcParameter"].ObjectId == param["binding_id"] == d["dcParameter"].ObjectId
            and b["parameter"].ObjectId == param["parameter_id"]
            and b["rrOwnerFeature"].ObjectId == b["rParentFeature"].ObjectId == feature
            and graph.Fields[b["rDynamicUpdateData"].ObjectId]["rOwnerNode"].ObjectId
            == param["binding_id"],
            "parameter, binding, dimension and sketch joins disagree",
        )
        param["dimension_id"] = dimension["id"]
    return {"direct_driver_inventory": raw, "anchor_evidence": anchor}


def native_controls():
    snapshot = GitSnapshot(ROOT)
    receipt = snapshot.blob(REVISION, P01_FOLDER + "receipt.json")
    require(sha256(receipt) == P01_RECEIPT, "P01 receipt changed")
    sources = {}
    for pin in snapshot.parse_document(receipt, "P01 receipt")["native_files"]:
        data = snapshot.blob(REVISION, P01_FOLDER + pin["file"])
        require(
            sha256(data) == pin["sha256"] and len(data) == pin["size_bytes"], "P01 input changed"
        )
        sources[pin["file"]] = {
            "archive_sha256": pin["sha256"],
            **read_raw(data, native_control=True),
        }
    require(len(sources) == 6, "P01 roster differs")
    return {"revision": REVISION, "receipt_sha256": P01_RECEIPT, "assets": sources}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="new directory for archive and evidence"
    )
    output = parser.parse_args().output
    content = generate()
    report = {
        "claim": "generated_archive_record_evidence",
        "native_application_acceptance": False,
        "codec_revision": check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "probe_sha256": sha256(Path(__file__).read_bytes()),
        "origin_probe_sha256": sha256(Path(ProbeOrigin.__file__).read_bytes()),
        "generated": inspect_generated(content),
        "discovery": native_controls(),
    }
    output.mkdir()
    (output / "OwnedRectangle.f3d").write_bytes(content)
    encoded = (json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    (output / "OwnedRectangleEvidence.json").write_bytes(encoded)
    print(sha256(encoded))


if __name__ == "__main__":
    main()
