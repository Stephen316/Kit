from struct import pack as PackFields
from sys import float_info as FloatInfo
from uuid import UUID

KPointTriple = tuple[float, float, float]
KStateBody = tuple[str, KPointTriple, KPointTriple]
KStateLead = bytes(18)
KStateMark = bytes.fromhex("2184de7b09")
KStateTail = bytes.fromhex("9101")
KFirstOrdinal = 2
KEmptyBox = (FloatInfo.max, FloatInfo.max, -FloatInfo.max, -FloatInfo.max)


def GuidBytes(GuidText: str) -> bytes:
    try:
        return UUID(GuidText).bytes_le
    except ValueError as Failure:
        raise ValueError(
            f"Authored DWG view GUID {GuidText!r} is malformed"
        ) from Failure


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
