from struct import pack as PackFields
from sys import float_info as FloatInfo
from uuid import UUID

# the point triple shape must stay shared so drawing view authoring uses one contract for compatible values
KPointTriple = tuple[float, float, float]

# the state body shape must stay shared so drawing view authoring uses one contract for compatible values
KStateBody = tuple[str, KPointTriple, KPointTriple]

# state lead must remain consistent across callers so projected geometry retains its paper and model relationships
KStateLead = bytes(18)

# state mark must remain consistent across callers so projected geometry retains its paper and model relationships
KStateMark = bytes.fromhex("2184de7b09")

# state tail must remain consistent across callers so projected geometry retains its paper and model relationships
KStateTail = bytes.fromhex("9101")

# first ordinal must remain consistent across callers so projected geometry retains its paper and model relationships
KFirstOrdinal = 2

# the empty box order must stay explicit so projected geometry retains its paper and model relationships
KEmptyBox = (FloatInfo.max, FloatInfo.max, -FloatInfo.max, -FloatInfo.max)


# guid bytes needs an explicit validity boundary so projected geometry retains its paper and model relationships
def GuidBytes(GuidText: str) -> bytes:
    try:
        return UUID(GuidText).bytes_le
    except ValueError as Failure:
        raise ValueError(
            f"Authored DWG view GUID {GuidText!r} is malformed"
        ) from Failure


# the state body contract needs a shared interpretation so projected geometry retains its paper and model relationships
def StateBody(Index: int, BodyEntry: KStateBody) -> bytes:
    GuidText, Lower, Upper = BodyEntry
    return b"".join(
        (
            PackFields("<d", 0.0),
            bytes(1 if Index == 0 else 2),
            PackFields("<q", KFirstOrdinal + Index),
            GuidBytes(GuidText),
            PackFields("<3d", *Lower),
            PackFields("<3d", *Upper),
            KStateMark,
        )
    )


# view state needs an explicit validity boundary so projected geometry retains its paper and model relationships
def ViewState(
    Target: KPointTriple,
    EyeAxis: KPointTriple,
    UpAxis: KPointTriple,
    Bodies: tuple[KStateBody, ...],
) -> bytes:
    if not 0 < len(Bodies) < 256:
        raise ValueError("Authored DWG view state needs between 1 and 255 bodies")
    return b"".join(
        (
            KStateLead,
            PackFields("<3d", *Target),
            PackFields("<3d", *EyeAxis),
            PackFields("<3d", *UpAxis),
            bytes((len(Bodies),)),
            *(StateBody(Index, BodyEntry) for Index, BodyEntry in enumerate(Bodies)),
            PackFields("<d", 0.0),
            PackFields("<4d", *KEmptyBox),
            KStateTail,
        )
    )
