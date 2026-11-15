from pathlib import Path

from convert.adapters.base.ContractTypes import IsBinaryTarget, KTargetType
from convert.adapters.base.WriteOptions import WriteOptions


# the payload operation needs a consistent construction rule so public document claims remain grounded in native records
def WritePayloadMut(
    Target: KTargetType, Payload: bytes, Settings: WriteOptions
) -> Path | None:
    if isinstance(Target, (str, Path)):
        PathValue = Path(Target)
        with PathValue.open("wb" if Settings.overwrite else "xb") as Stream:
            Count = Stream.write(Payload)
        if Count != len(Payload):
            raise OSError("Incomplete Fusion file write")
        return PathValue
    if not IsBinaryTarget(Target):
        raise TypeError("Fusion requires a binary output stream")
    StreamCount = Target.write(Payload)
    if StreamCount is not None and StreamCount != len(Payload):
        raise OSError("Incomplete Fusion stream write")
    return None
