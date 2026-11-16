from collections.abc import Callable

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# embedded and named features share a base even when their following records differ
def ReadFeatBase(
    ReadFields: Callable[[str], tuple[object, ...]],
    ReadVector: Callable[[int], tuple[float, ...]],
    ReadNull: Callable[[], object],
    ReadLabel: Callable[[], str],
) -> None:
    ModeValue, _, _ = ReadFields("<2iI")
    RequireArch(ModeValue, 0, "ordinary feature mode")
    RequireArch(ReadFields("<B"), (0,), "absent alternate feature label")
    _ = ReadFields("<4i")
    _ = ReadVector(1)
    _ = ReadFields("<i")
    _ = ReadNull()
    RequireArch(ReadLabel(), "", "empty feature label")
    RequireArch(ReadFields("<B"), (0,), "observed editable state")
    _ = ReadFields("<HHBIHhf")
    _ = ReadFields("<2i")
    _ = ReadNull()
    _ = ReadFields("<IBB")
    _ = ReadFields("<5iH2i")
