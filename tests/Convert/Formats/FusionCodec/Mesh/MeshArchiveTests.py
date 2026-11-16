from dataclasses import asdict as DataMapping
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson

from pytest import mark as MarkTests

from convert.Formats.Fusion.MeshCodec.EmitParaMesh import EmitParaMesh
from convert.Formats.Fusion.MeshCodec.ReadParaMesh import ReadParaMesh
from tests.Convert.Formats.FusionCodec.Mesh.MeshCase import MeshCase
from tests.Convert.Formats.FusionCodec.Mesh.ReadMeshCases import ReadMeshCases
from tests.Convert.Formats.FusionCodec.Mesh.ReadMeshFile import ReadMeshFile


# the mesh archive contract needs boundary coverage so stored document relationships remain consistent
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
