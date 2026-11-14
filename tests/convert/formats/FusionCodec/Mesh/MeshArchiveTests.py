from dataclasses import asdict as DataMapping
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson

from pytest import mark as MarkTests

from convert.formats.Fusion.MeshCodec.EmitParaMesh import EmitParaMesh
from convert.formats.Fusion.MeshCodec.ReadParaMesh import ReadParaMesh
from tests.convert.formats.FusionCodec.Mesh.MeshCase import MeshCase
from tests.convert.formats.FusionCodec.Mesh.ReadMeshCases import ReadMeshCases
from tests.convert.formats.FusionCodec.Mesh.ReadMeshFile import ReadMeshFile


@MarkTests.parametrize("CaseValue", ReadMeshCases())
def TestMeshArchive(CaseValue: MeshCase) -> None:
    Model = ReadParaMesh(ReadMeshFile(CaseValue))
    Encoded = DumpJson(
        DataMapping(Model), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    assert HashBytes(Encoded).hexdigest() == CaseValue["SemanticHash"]
    assert len(Model.Positions) == CaseValue["Vertices"]
    assert len(Model.Corners) == 3 * CaseValue["Triangles"]
    assert ReadParaMesh(EmitParaMesh(Model)) == Model
