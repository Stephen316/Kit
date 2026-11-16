from hashlib import sha256 as HashBytes
from pathlib import Path

from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Parasolid import DecodePartition
from convert.geometry.Parasolid import (
    BrepTopology,
    DecodeBrepModel,
    MakeEncOwners,
    MakeLoopOrder,
)


# the saved independent shells expose changes that body wide traversal would hide
def CheckShellWalk() -> None:
    RootPath = Path(__file__).resolve().parents[3]
    PartPath = (
        RootPath
        / "re/solidworks/examples"
        / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
        / "RODAMIENTO DE BANDA.SLDPRT"
    )
    PartBytes = PartPath.read_bytes()
    assert len(PartBytes) == 532245
    assert HashBytes(PartBytes).hexdigest() == (
        "d3b6e56ddadbfc81523d9f73c3da81b57956f11df5c248b03a6acbf12e2c891a"
    )
    Archive = SldprtArchive.from_bytes(PartBytes, PartPath.name)
    Stream = "Contents/Config-0-Partition"
    (Partition,) = (
        Value
        for Value in DecodePartition(Archive.require(Stream), Stream)
        if Value.kind == "partition"
    )
    assert Partition.sha256 == (
        "bd5eaa3628f976a789edd0443cadb6f60377e512d71203caf1c7e34180972307"
    )
    Model = DecodeBrepModel(Partition.data)
    assert Model is not None
    assert len(Model.bodies) == 1
    assert sorted(len(Shell.face_use_ids) for Shell in Model.shells) == [4, 8, 213]
    assert all(Shell.closed for Shell in Model.shells)
    Topology = BrepTopology(Model)
    Owners = MakeEncOwners(Model, Topology)
    EncodedLoops, EncodedDirections = MakeLoopOrder(Model, Topology, Owners)

    StableLegacyFlips = {
        "sldprt:brep:face:66",
        "sldprt:brep:face:69",
        "sldprt:brep:face:118",
        "sldprt:brep:face:151",
        "sldprt:brep:face:153",
        "sldprt:brep:face:161",
    }
    assert StableLegacyFlips <= {FaceValue.id for FaceValue in Model.faces}
    for LoopValue in Model.loops:
        Flipped = Topology.loop_face[LoopValue.id] in StableLegacyFlips
        ExpectedOrder = LoopValue.coedge_ids[::-1] if Flipped else LoopValue.coedge_ids
        assert EncodedLoops[LoopValue.id] == ExpectedOrder
        assert all(
            EncodedDirections[FinId] == Topology.coedges[FinId].reversed ^ Flipped
            for FinId in LoopValue.coedge_ids
        )
