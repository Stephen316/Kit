from hashlib import sha256

from RectangleSupport import WriteProfileChain, WriteProfileSupport
from VerifyConfigRoot import require
from VerifyResolvedPlanes import map_state
from convert.adapters.solidworks.Resolved.ContourChain import ReadChainState
from convert.adapters.solidworks.Resolved.ProfilePlane import ReadProfileRef
from convert.adapters.solidworks.Resolved.RectanglePart import ResolveDatum


# The ordinary profile keeps its native perimeter order and references a system datum.
def verify_profile_support(
    cursor, profile, system, origin, has_atom, generation, writer
):
    start = cursor.Offset
    before = map_state(cursor)
    perimeter = tuple(
        line["native_id"]
        for line in profile.Geometry["lines"]
        if line["native_id"] >= 0
    )
    chain = ReadChainState(cursor, has_atom, perimeter)
    chain_end = cursor.Offset
    chain_map = map_state(cursor)
    require(
        chain is None or chain["edge_ids"] == tuple(sorted(perimeter)),
        "body chain walks the local sketch edge identities",
    )
    require(
        chain_map.NextIndex - before.NextIndex == 2 * int(has_atom),
        "optional body chain class and object slots",
    )
    reference = ReadProfileRef(cursor, generation)
    datum, _ = ResolveDatum(reference, system.Planes)
    end = cursor.Offset
    after = map_state(cursor)
    require(
        reference.PartIndex == origin.Support.PartIndex
        and reference.TimeValue == origin.Support.TimeValue
        and (reference.ObjectIndex, reference.UnitIndex)
        == (chain_map.NextIndex, chain_map.NextIndex + 1)
        and after.NextIndex == chain_map.NextIndex + 2,
        "principal support reuses the owning part and allocates two objects",
    )
    raw = cursor.BlobValue[start:end]
    if writer is not None:
        require(
            writer.Snapshot() == before, "profile chain receives the live sketch map"
        )
        position = len(writer.build())
        WriteProfileChain(writer, tuple(sorted(perimeter)) if has_atom else None)
        require(writer.Snapshot() == chain_map, "body chain ownership map")
        WriteProfileSupport(
            writer,
            generation,
            origin.Support.PartIndex,
            datum.FeatureId,
            reference.TimeValue,
        )
        require(
            writer.build()[position:] == raw,
            "exact rectangle chain and support records",
        )
        require(writer.Snapshot() == after, "rectangle support ownership map")
    proof = (
        start,
        chain_end,
        end,
        before.NextIndex,
        chain_map.NextIndex,
        after.NextIndex,
        datum.FeatureId,
        sha256(raw).hexdigest(),
    )
    return proof, reference
