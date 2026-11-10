# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


# isolated execution proves the wheel needs no cad application or external runtime hook
KIsolatedRuntime = r"""
import io
from pathlib import Path
import sys
from zipfile import ZipFile

blocked_imports = frozenset(
    {
        "FreeCAD",
        "FreeCADGui",
        "NXOpen",
        "OCC",
        "OCP",
        "Part",
        "Sketcher",
        "adsk",
        "aiohttp",
        "cadquery",
        "cffi",
        "clr",
        "comtypes",
        "ctypes",
        "ftplib",
        "httpx",
        "lxml",
        "multiprocessing",
        "numpy",
        "pycatia",
        "pythoncom",
        "requests",
        "runpy",
        "scipy",
        "socket",
        "ssl",
        "subprocess",
        "urllib",
        "urllib3",
        "websockets",
        "win32com",
    }
)


class ImportBlocker:
    def find_spec(self, fullname, path=None, target=None):
        root = fullname.partition(".")[0]
        if root in blocked_imports:
            raise RuntimeError(f"blocked runtime import: {fullname}")
        return None


def audit(event, arguments):
    blocked = (
        event == "os.system"
        or event.startswith("os.spawn")
        or event.startswith("socket.")
        or event.startswith("subprocess.")
        or event.startswith("ctypes.")
    )
    if blocked:
        raise RuntimeError(f"blocked runtime operation: {event}")


sys.meta_path.insert(0, ImportBlocker())
sys.addaudithook(audit)
sys.path.insert(0, sys.argv[1])

from convert import available_adapters, convert, open_document, write_document
from convert.adapters.Fusion.Adapter import FusionReader
from convert.adapters.base.ReadOptions import ReadOptions
from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.AssetCodec.AssetPlan import AssetPlan
from convert.formats.Fusion.AssetCodec.EmitAsset import EmitAsset
from convert.formats.Fusion.AssetCodec.SegmentPlan import SegmentPlan
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Browser.EmitBrowserRoot import EmitBrowserRoot
from convert.formats.Fusion.SegmentCodec.Browser.ReadBrowserRoot import ReadBrowserRoot
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Manifest.ReadAssetWire import ReadAssetWire
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootWire import ReadRootWire
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from convert.formats.Fusion.SourceProof.InspectSource import ReadSourceProof
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import ReadActiveMeta

root = Path(sys.argv[2])
output = Path(sys.argv[3])
adapters = {adapter.format_id for adapter in available_adapters()}
assert adapters == {
    "catia.v5",
    "freecad.fcstd",
    "interchange.json",
    "solidworks.sldprt",
}
fusion_path = output / "runtime-fusion.f3d"
fusion_reader = FusionReader()
fusion_opts = ReadOptions(strict=False)
fusion = fusion_reader.read(fusion_path, fusion_opts)
assert fusion.source.format_id == "fusion.f3d"
assert fusion.metadata["fusion.history_id"] == 104
assert any(item.code == "fusion.history.partial" for item in fusion.diagnostics)
assert fusion.brep_payloads[0].data == fusion_path.read_bytes()
assert ReadSourceProof(fusion_path).ActiveRoutes is None
try:
    from compression import zstd
except ImportError:
    zstd = None
if zstd is not None:
    capture = root / "re" / "Fusion" / "Study" / "revolveto-b1d196f65c46" / "two_planes.f3d"
    native_fusion = fusion_reader.read(capture, fusion_opts)
    assert len(native_fusion.bodies) == 1 and native_fusion.brep is not None
    proof = ReadSourceProof(capture)
    assert proof.Scope.SourceDigest == native_fusion.source.sha256
    assert proof.ActiveRoutes is not None and proof.ActiveRoutes.Routes
    assert not proof.IsComplete
    with ZipFile(capture) as archive:
        root_meta = ReadRootWire(archive.read("Manifest.dat"))
        asset_meta = ReadAssetWire(archive.read("FusionAssetName[Active]/Manifest.dat"))
        segment_plans = {}
        for segment in SegmentKind:
            prefix = f"FusionAssetName[Active]/{segment.value}1/"
            bulk_data = archive.read(prefix + "BulkStream.dat")
            meta_data = archive.read(prefix + "MetaStream.dat")
            records = []
            for span in ReadBulkSpans(bulk_data, meta_data, Segment=segment):
                payload = bulk_data[span.PayloadOffset:span.EndOffset]
                if segment is SegmentKind.KBrowser and span.ObjectId == 0 and span.IsPrimary:
                    payload = EmitBrowserRoot(ReadBrowserRoot(payload))
                records.append(BulkRecord(span.TypeCode, span.ObjectId, span.IsPrimary, payload))
            metadata = ReadMetaWire(meta_data, Segment=segment)
            assert EmitSegment(metadata, records) == (bulk_data, meta_data)
            segment_plans[segment] = SegmentPlan(metadata, tuple(records))
    generated = EmitAsset(AssetPlan(
        root_meta, asset_meta, segment_plans[SegmentKind.KDesign],
        segment_plans[SegmentKind.KAct], segment_plans[SegmentKind.KBrowser], True,
    ))
    with OpenFusionZip(generated) as archive:
        generated_manifest = ReadActiveMeta(archive)
        assert generated_manifest.AssetId == asset_meta.AssetId
        assert generated_manifest.SnapshotId == asset_meta.SnapshotId
    angular_capture = root / "re" / "Fusion" / "Study" / "revolvemodes-8eb734486235" / "negative.f3d"
    angular_fusion = fusion_reader.read(angular_capture, fusion_opts)
    assert type(angular_fusion.feature_timeline[-1].definition).__name__ == "AngularRevolve"
    assert len(angular_fusion.bodies) == 1 and angular_fusion.brep is not None
    analytic_capture = root / "re" / "Fusion" / "Study" / "analytic-86a12b291d0a" / "analytic.f3d"
    analytic_fusion = fusion_reader.read(analytic_capture, fusion_opts)
    assert len(analytic_fusion.bodies) == 3
    assert sorted(type(surface).__name__ for surface in analytic_fusion.brep.surfaces) == [
        "ConeSurface", "PlaneSurface", "SphereSurface", "TorusSurface",
    ]
cases = (
    (root / "examples" / ".SLDPRT" / "example.SLDPRT", ".FCStd"),
    (output / "conversion_0.FCStd", ".CATPart"),
    (root / "examples" / ".CATPart" / "Banjo.CATPart", ".SLDPRT"),
    (
        root
        / "examples"
        / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
        / "Cylinder Head Assy 1.SLDASM",
        ".CATProduct",
    ),
    (
        root
        / "examples"
        / ".CATProduct"
        / "Brake_Pedal_Assembly - Backup 2.CATProduct",
        ".SLDASM",
    ),
)
for index, (source, suffix) in enumerate(cases):
    destination = output / f"conversion_{index}{suffix}"
    result = convert(source, destination)
    assert result.output.path == destination.resolve()
    assert result.output.bytes_written == destination.stat().st_size
    assert result.requirements == ()
    assert result.dropped == frozenset()
    assert open_document(destination).validate() == ()

source_document = open_document(cases[0][0])
buffer = io.BytesIO()
written = write_document(
    source_document,
    buffer,
    destination_format="interchange.json",
)
assert written.path is None
assert written.bytes_written == len(buffer.getvalue())
assert open_document(
    buffer.getvalue(), source_format="interchange.json"
) == source_document
"""
